"""journal_requetes.py — journal d'accès HTTP applicatif (méthode, chemin,
statut, **durée**).

Pourquoi ce module (09/09/2026)
-------------------------------
L'audit du 09/09/2026 a rétabli un handler sur le logger racine
(`logging_config.py`) et une alerte de tension du pool
(`database/session.py`). Il restait le trou le plus coûteux de l'incident des
08-09/09/2026 : **aucune durée par requête**. Le journal d'uvicorn indique
qu'une requête a répondu 500, jamais qu'elle a mis 30 s à le faire — or c'est
exactement ce signal qui aurait désigné l'endpoint fuyant en quelques minutes
au lieu de plusieurs heures. Les 36 échecs sur 224 étaient des victimes du
`pool_timeout`, pas des coupables ; seule la durée les distingue.

Choix 1 — on **remplace** la ligne d'accès d'uvicorn, on ne l'ajoute pas
---------------------------------------------------------------------
Deux lignes quasi identiques par requête rendraient le journal illisible, et
c'est un journal qu'on lit en urgence. Notre ligne est un sur-ensemble utile de
celle d'uvicorn (même méthode, même chemin, même statut, **plus** la durée), la
seule à disposer d'un niveau variable (WARNING/ERROR) — donc à être filtrable
sur incident. La ligne d'uvicorn est donc muselée.

Le muselage passe par un **filtre posé sur le logger `uvicorn.access`**, et non
par un `setLevel`, pour une raison précise : uvicorn applique sa propre
`dictConfig` au démarrage, laquelle repositionne `uvicorn.access` à INFO et
écraserait tout niveau fixé à l'import (`desktop.py` importe `main` **avant**
d'appeler `uvicorn.run`, et le CLI construit sa `Config` avant de charger
l'application — dans les deux cas notre réglage perdrait). En revanche
`logging.config` ne retire jamais les filtres déjà attachés à un logger
existant : le filtre, lui, survit. Vérifié en conditions réelles sur le port
8012 le 09/09/2026.

Échappatoire : `GREENSHIELD_LOG_ACCES_UVICORN=1` rend sa ligne à uvicorn (utile
pour comparer les deux journaux, ou si l'on soupçonne ce middleware lui-même).
**Elle rétablit un risque de fuite** : voir l'avertissement porté sur
`museler_journal_acces_uvicorn()`, seul endroit où la variable est lue.

Choix 2 — middleware ASGI pur, pas `@app.middleware("http")`
------------------------------------------------------------
Le middleware des en-têtes de sécurité de `main.py` utilise la forme
décorateur, qui repose sur `BaseHTTPMiddleware` : celle-ci ouvre un groupe de
tâches anyio et une paire de flux mémoire **par requête**. Acceptable une fois ;
en doubler le coût pour une simple mesure de temps ne l'est pas, alors que la
consigne est un surcoût négligeable. La forme ASGI ci-dessous n'ajoute qu'une
fermeture et un `perf_counter()`. Elle a de plus deux avantages de fond :

  * elle lit le statut dans le message `http.response.start`, donc y compris
    quand la réponse est produite par un gestionnaire d'exception ou par un
    middleware situé plus bas (429 de slowapi, 400 de CORS) ;
  * elle arrête le chronomètre quand le corps a fini d'être émis, pas quand
    l'objet `Response` a été construit — pour une réponse en flux (export
    Word, archive de mission), c'est la seule mesure qui corresponde au temps
    vécu par l'utilisateur.

Choix 3 — ce qui n'est PAS journalisé
-------------------------------------
Seuls méthode, chemin, statut et durée sortent. Sont volontairement exclus :

  * la **chaîne de requête** (`scope["query_string"]`) — c'est le seul endroit
    de l'URL où peuvent transiter un jeton ou un paramètre sensible, et son
    absence ne coûte rien au diagnostic ;
  * les **en-têtes** (donc `Authorization`, `Cookie`) et le **corps** de la
    requête, qui contient des données de mission client ;
  * l'**adresse IP du client**, présente chez uvicorn : GREEN SHIELD n'écoute
    que sur 127.0.0.1 (cf. `desktop.py`), l'information est constante donc sans
    valeur, et c'est une donnée à caractère personnel qu'un outil GRC n'a
    aucune raison d'accumuler dans un journal console.

Le chemin est conservé tel quel : il porte des identifiants de mission
(`/api/projects/cassiopee`), ce qui est assumé — sans lui la ligne ne sert à
rien.

Correctifs du 09/09/2026 (revue du module)
------------------------------------------
Trois défauts relevés à la relecture ont été traités ici :

  * le **seuil de lenteur unique** produisait un WARNING garanti sur des routes
    lentes par construction — voir la table `_SEUILS_PAR_PREFIXE` plus bas ;
  * une **annulation du client** sortait en `ERROR ... -> 500` alors qu'aucun
    500 n'avait été émis, ce qui polluait le seul signal qu'on veut pouvoir
    filtrer en incident — voir `_ABANDONS_CLIENT` et `_STATUT_ABANDON_CLIENT` ;
  * l'échappatoire `GREENSHIELD_LOG_ACCES_UVICORN` réintroduit la fuite de la
    chaîne de requête — documentée à l'endroit où la variable est lue.

Le tout est verrouillé par `api/tests/test_journal_requetes.py`, qui garde
notamment l'invariant « inscrit en dernier, donc le plus externe ».
"""
from __future__ import annotations

import asyncio
import logging
import os
import time

import anyio
from starlette.requests import ClientDisconnect

# Logger dédié : le nom occupe une colonne fixe du format défini dans
# `logging_config.py`, donc `grep "greenshield.http"` isole tout le trafic HTTP
# sans attraper le reste du journal applicatif.
_log = logging.getLogger("greenshield.http")

# Au-delà de ce seuil, la ligne passe en WARNING. 1 s est déjà anormal pour un
# outil local sur SQLite : le tableau de bord répond en quelques dizaines de
# millisecondes. Ajustable sans redéploiement via `GREENSHIELD_SEUIL_LENTEUR_MS`
# si le bruit devenait gênant.
_SEUIL_LENTEUR_MS_DEFAUT = 1000.0

# ---------------------------------------------------------------------------
# Seuils par chemin (09/09/2026)
# ---------------------------------------------------------------------------
# Pourquoi une table plutôt qu'un seuil unique : un WARNING qui se déclenche sur
# un usage parfaitement normal se filtre mentalement au bout de deux jours, puis
# s'ignore — et le jour où il signale un vrai problème, personne ne le lit. Le
# seuil de 1 s garantissait ce sort à trois familles de routes, chiffres à
# l'appui :
#
#   * `/api/copilot/ask` interroge un modèle de langage. Quand le fournisseur
#     est local (Ollama, cas par défaut du consultant en clientèle), le modèle
#     tourne sur le processeur du poste : `ai_gateway.py` lui accorde
#     `TIMEOUT_LOCAL = 300` secondes, et une réponse en dessous de 5 s est déjà
#     une bonne surprise. **Tout** appel dépassait donc le seuil. 30 s : au-delà,
#     l'utilisateur commence réellement à se demander si l'outil a planté, et
#     c'est le moment où la ligne mérite l'œil.
#   * les **exports** (`report.docx`, `nda.docx`, `pssi.docx`, … et
#     `/projects/{id}/export/{type}`) composent un document Word complet à la
#     volée : lecture de la mission entière, rendu des tableaux, écriture du
#     paquet OOXML. Quelques secondes sont le régime nominal.
#   * l'**archive** de mission (`POST /projects/{id}/archive` et
#     `/projects/import-archive`) parcourt l'arborescence des preuves et la
#     compresse ; elle grandit avec la mission, par nature.
#
# Les deux dernières familles ne partagent pas de préfixe utilisable — le
# préfixe commun serait `/api/projects`, qui couvrirait aussi les routes de
# lecture rapides et rendrait le seuil inutile. Elles sont donc reconnues par
# marqueur de chemin (`_MARQUEURS_EXPORT`), ce qui reste quelques comparaisons
# de sous-chaînes sur une chaîne courte : le surcoût par requête demeure
# négligeable, conformément à la contrainte de conception de ce module.
_SEUILS_PAR_PREFIXE: tuple[tuple[str, float], ...] = (
    ("/api/copilot", 30_000.0),
)

_MARQUEURS_EXPORT: tuple[str, ...] = (".docx", "/archive", "import-archive", "/export/")
_SEUIL_EXPORT_MS = 10_000.0

# Statut porté par une requête abandonnée avant toute réponse. 499 est la
# convention nginx (« Client Closed Request ») : il n'a jamais circulé sur le
# réseau, il sert uniquement à ce que la ligne ne se compte pas parmi les 5xx.
_STATUT_ABANDON_CLIENT = 499

# Exceptions qui signent un abandon du client (ou l'arrêt du serveur), et non
# une panne applicative. Sans cette distinction, un simple Ctrl+C dans l'onglet
# du navigateur produisait `ERROR ... -> 500` : le pire des faux positifs, car
# 5xx est justement le filtre qu'on dégaine en incident. uvicorn annule la tâche
# de la requête quand la connexion tombe, d'où `CancelledError` ; les variantes
# anyio apparaissent quand la coupure est vue au niveau du flux, et
# `ClientDisconnect` quand c'est Starlette qui la détecte en lisant le corps.
_ABANDONS_CLIENT: tuple[type[BaseException], ...] = (
    asyncio.CancelledError,
    ClientDisconnect,
    anyio.EndOfStream,
    anyio.BrokenResourceError,
    anyio.ClosedResourceError,
)


def _seuil_lenteur_ms() -> float:
    """Seuil par défaut, éventuellement surchargé par l'environnement."""
    brut = os.environ.get("GREENSHIELD_SEUIL_LENTEUR_MS")
    if not brut:
        return _SEUIL_LENTEUR_MS_DEFAUT
    try:
        return float(brut)
    except ValueError:
        # Une faute de frappe dans une variable d'environnement ne doit pas
        # empêcher le serveur de démarrer : on retombe sur le défaut.
        return _SEUIL_LENTEUR_MS_DEFAUT


def seuil_pour_chemin(chemin: str, seuil_defaut_ms: float) -> float:
    """Seuil de lenteur applicable à `chemin`, en millisecondes.

    `max(...)` avec le défaut : quelqu'un qui remonte
    `GREENSHIELD_SEUIL_LENTEUR_MS` cherche à se taire, pas à se faire alerter
    davantage. Un défaut relevé à 60 s ne doit donc pas rendre le copilote
    (30 s) subitement plus bavard que le reste.
    """
    for prefixe, seuil in _SEUILS_PAR_PREFIXE:
        if chemin.startswith(prefixe):
            return max(seuil, seuil_defaut_ms)
    for marqueur in _MARQUEURS_EXPORT:
        if marqueur in chemin:
            return max(_SEUIL_EXPORT_MS, seuil_defaut_ms)
    return seuil_defaut_ms


class _FiltreMuselant(logging.Filter):
    """Filtre qui rejette tout. Marqué pour rester idempotent."""

    greenshield_muselage = True

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D102
        return False


def museler_journal_acces_uvicorn() -> bool:
    """Coupe la ligne d'accès d'uvicorn. Renvoie True si le muselage est actif.

    Idempotente : `main` est importé par la quasi-totalité des tests, empiler
    les filtres serait sans effet visible mais inutilement sale.

    ATTENTION — `GREENSHIELD_LOG_ACCES_UVICORN=1` rétablit une fuite (09/09/2026)
    ---------------------------------------------------------------------------
    Cette variable rend à uvicorn sa ligne d'accès. Or uvicorn journalise le
    chemin **avec la chaîne de requête** : `GET /api/x?token=eyJhbGciOi... 200`.
    Tout ce que le `Choix 3` de l'en-tête de ce module écarte volontairement
    (jeton en query string, paramètre sensible, adresse IP du client) revient
    alors dans la console — et, si la sortie est redirigée, dans un fichier que
    personne n'a classé comme sensible.

    Ce n'est pas corrigeable ici : le format de la ligne appartient à uvicorn.
    La variable reste donc réservée au diagnostic ponctuel (comparer les deux
    journaux, ou soupçonner ce middleware lui-même), sur un poste de
    développement, et surtout pas dans une configuration permanente livrée au
    client. Quiconque l'active doit savoir qu'il rouvre ce risque.
    """
    if os.environ.get("GREENSHIELD_LOG_ACCES_UVICORN"):
        return False
    acces = logging.getLogger("uvicorn.access")
    for filtre in acces.filters:
        if getattr(filtre, "greenshield_muselage", False):
            return True
    acces.addFilter(_FiltreMuselant())
    return True


class JournalRequetesHTTP:
    """Middleware ASGI : une ligne par requête HTTP terminée."""

    def __init__(self, app) -> None:
        self.app = app
        # Le seuil par défaut est résolu une fois à la construction, pas à
        # chaque requête : un `os.environ.get` par requête serait un coût
        # gratuit. La résolution par chemin, elle, doit rester par requête —
        # elle dépend de l'URL appelée.
        self.seuil_ms = _seuil_lenteur_ms()

    async def __call__(self, scope, receive, send) -> None:
        # `lifespan` et `websocket` n'ont pas de couple méthode/statut : on les
        # laisse passer sans même démarrer le chronomètre.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        debut = time.perf_counter()
        # Valeur de repli si l'application lève avant d'avoir émis une réponse :
        # c'est bien un 500 que le client recevra (via `ServerErrorMiddleware`).
        statut = 500
        reponse_commencee = False
        abandon_client = False

        async def envoyer(message) -> None:
            nonlocal statut, reponse_commencee
            if message["type"] == "http.response.start":
                statut = message["status"]
                reponse_commencee = True
            await send(message)

        try:
            await self.app(scope, receive, envoyer)
        except _ABANDONS_CLIENT:
            # On marque puis on relaie : intercepter une annulation sans la
            # relancer bloquerait l'arrêt propre du serveur.
            abandon_client = True
            raise
        finally:
            # `finally` et non `else` : une requête qui explose ou qu'un client
            # abandonne est précisément celle qu'on veut voir, avec sa durée.
            # La trace de l'exception, elle, est journalisée par la couche
            # au-dessus ; on ne la duplique pas ici.
            duree_ms = (time.perf_counter() - debut) * 1000.0
            chemin = scope.get("path", "")
            lent = duree_ms >= seuil_pour_chemin(chemin, self.seuil_ms)
            precision = ""
            if abandon_client:
                # Jamais ERROR : personne n'est en panne, l'utilisateur a fermé
                # l'onglet. WARNING seulement si c'était aussi lent, car une
                # requête qu'on abandonne au bout de 40 s dit quelque chose.
                if not reponse_commencee:
                    statut = _STATUT_ABANDON_CLIENT
                    precision = " (abandon client, aucune reponse emise)"
                else:
                    precision = " (abandon client en cours de reponse)"
                niveau = logging.WARNING if lent else logging.INFO
            elif statut >= 500:
                niveau = logging.ERROR
            elif lent:
                niveau = logging.WARNING
            else:
                niveau = logging.INFO
            # Formatage paresseux (`%s` et arguments) : sur les lignes INFO
            # filtrées par le niveau, la chaîne n'est jamais construite.
            _log.log(
                niveau, "%s %s -> %d en %.1f ms%s",
                scope["method"], chemin, statut, duree_ms, precision,
            )


def installer(app) -> None:
    """Branche le journal d'accès sur l'application.

    À appeler **en dernier** dans `main.py` : `add_middleware` empile en tête,
    le dernier inscrit est donc le plus externe. C'est ce qu'on veut — le
    chronomètre doit englober CORS, les en-têtes de sécurité et le limiteur de
    débit, sans quoi un 429 de slowapi ou un rejet CORS n'apparaîtrait dans
    aucune ligne.

    Cet invariant est fragile (le prochain `add_middleware` ajouté après
    l'appel le casserait en silence) : `test_journal_requetes.py` le vérifie via
    `app.user_middleware[0].cls`.
    """
    app.add_middleware(JournalRequetesHTTP)
    museler_journal_acces_uvicorn()
