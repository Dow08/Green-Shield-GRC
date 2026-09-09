"""Tests du journal structuré des requêtes HTTP (`modules/journal_requetes.py`).

09/09/2026 — pourquoi ces tests existent. Ce middleware est traversé par 100 %
des requêtes, mais aucune fonctionnalité ne tombe s'il se dérègle : seules les
lignes de journal deviennent fausses. Un dérèglement est donc invisible jusqu'au
prochain incident, c'est-à-dire au pire moment. Trois invariants méritaient
d'être verrouillés :

  * **l'ordre d'inscription** — `installer()` doit rester le dernier appel de
    `main.py`. Le prochain `add_middleware` ajouté après lui le casserait en
    silence : la durée mesurée n'engloberait plus CORS ni le limiteur de débit,
    et un 429 de slowapi n'apparaîtrait dans aucune ligne ;
  * **l'absence de fuite** — la chaîne de requête et les en-têtes sont
    volontairement écartés. Un jeton recopié dans un journal est une faille, et
    une régression ici ne se verrait jamais à l'œil nu ;
  * **le choix du niveau** — c'est lui qui rend le journal filtrable en
    incident. Un abandon client classé ERROR 500 polluerait le signal 5xx,
    précisément celui qu'on interroge quand quelque chose casse.
"""
import asyncio
import logging

import pytest

import main
from modules import journal_requetes
from modules.journal_requetes import (
    JournalRequetesHTTP,
    museler_journal_acces_uvicorn,
    seuil_pour_chemin,
)

_NOM_LOGGER = "greenshield.http"


# --- utilitaires -------------------------------------------------------------

def _app_factice(statut: int = 200, exception: BaseException | None = None):
    """Application ASGI minimale : répond `statut`, ou lève `exception`."""
    async def app(scope, receive, send):
        if exception is not None:
            raise exception
        await send({"type": "http.response.start", "status": statut, "headers": []})
        await send({"type": "http.response.body", "body": b""})
    return app


def _appeler(middleware, chemin: str = "/api/x", methode: str = "GET",
             query: bytes = b"", entetes: list | None = None) -> None:
    """Fait passer une requête HTTP factice dans le middleware."""
    scope = {
        "type": "http", "method": methode, "path": chemin,
        "query_string": query, "headers": entetes or [],
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(_message):
        return None

    asyncio.run(middleware(scope, receive, send))


# --- invariant d'ordre -------------------------------------------------------

def test_le_journal_est_le_middleware_le_plus_externe():
    """`add_middleware` empile en tête : le dernier inscrit est le plus externe.

    C'est le garde-fou annoncé dans la docstring d'`installer()`. S'il tombe,
    c'est qu'un `add_middleware` a été ajouté après `journal_requetes.installer`
    dans `main.py` — remettre l'appel en dernier plutôt que d'ajuster ce test.
    """
    assert main.app.user_middleware[0].cls is JournalRequetesHTTP


# --- muselage de la ligne d'accès d'uvicorn ---------------------------------

def test_le_muselage_est_pose_et_idempotent():
    """`main` étant importé par presque tous les tests, empiler un filtre par
    import serait sans effet visible mais salirait le logger indéfiniment."""
    museler_journal_acces_uvicorn()
    museler_journal_acces_uvicorn()
    acces = logging.getLogger("uvicorn.access")
    marques = [f for f in acces.filters if getattr(f, "greenshield_muselage", False)]
    assert len(marques) == 1


def test_l_echappatoire_rend_sa_ligne_a_uvicorn(monkeypatch):
    """`GREENSHIELD_LOG_ACCES_UVICORN=1` doit court-circuiter le muselage.

    Le contrat est de renvoyer False **sans** toucher aux filtres : la variable
    sert au diagnostic ponctuel et rétablit une fuite (uvicorn journalise le
    chemin avec sa chaîne de requête), elle ne doit rien laisser derrière elle.
    """
    monkeypatch.setenv("GREENSHIELD_LOG_ACCES_UVICORN", "1")
    assert museler_journal_acces_uvicorn() is False


# --- absence de fuite --------------------------------------------------------

def test_ni_le_jeton_ni_l_en_tete_d_autorisation_ne_sont_journalises(caplog):
    """La ligne ne porte que méthode, chemin, statut et durée.

    Un jeton passé en chaîne de requête (mauvaise pratique, mais elle arrive) ou
    un en-tête `Authorization` recopié dans la console finirait dans un fichier
    que personne n'a classé comme sensible.
    """
    middleware = JournalRequetesHTTP(_app_factice())
    with caplog.at_level(logging.INFO, logger=_NOM_LOGGER):
        _appeler(
            middleware,
            chemin="/api/projects",
            query=b"token=SECRET_EN_QUERY_STRING",
            entetes=[(b"authorization", b"Bearer SECRET_EN_ENTETE")],
        )
    trace = "\n".join(enregistrement.getMessage() for enregistrement in caplog.records)
    assert "SECRET_EN_QUERY_STRING" not in trace
    assert "SECRET_EN_ENTETE" not in trace
    assert "/api/projects" in trace


# --- choix du niveau ---------------------------------------------------------

def _niveaux(caplog) -> list[int]:
    return [e.levelno for e in caplog.records if e.name == _NOM_LOGGER]


def test_une_requete_normale_sort_en_info(caplog):
    middleware = JournalRequetesHTTP(_app_factice(statut=200))
    middleware.seuil_ms = 10_000.0  # rien ne sera jugé lent
    with caplog.at_level(logging.INFO, logger=_NOM_LOGGER):
        _appeler(middleware)
    assert _niveaux(caplog) == [logging.INFO]


def test_une_requete_lente_sort_en_warning(caplog):
    """Seuil ramené à 0 plutôt que d'attendre réellement une seconde : le test
    porte sur la règle de décision, pas sur la capacité de Python à dormir."""
    middleware = JournalRequetesHTTP(_app_factice(statut=200))
    middleware.seuil_ms = 0.0
    with caplog.at_level(logging.INFO, logger=_NOM_LOGGER):
        _appeler(middleware)
    assert _niveaux(caplog) == [logging.WARNING]


def test_une_erreur_serveur_sort_en_error(caplog):
    middleware = JournalRequetesHTTP(_app_factice(statut=500))
    middleware.seuil_ms = 10_000.0
    with caplog.at_level(logging.INFO, logger=_NOM_LOGGER):
        _appeler(middleware)
    assert _niveaux(caplog) == [logging.ERROR]


def test_un_abandon_client_n_est_pas_une_erreur_serveur(caplog):
    """Régression du 09/09/2026 : une annulation sortait en `ERROR ... -> 500`
    alors qu'aucun 500 n'avait été émis, polluant le seul signal qu'on interroge
    en incident. Elle doit sortir en 499, sans niveau ERROR."""
    abandon = journal_requetes._ABANDONS_CLIENT[0]
    middleware = JournalRequetesHTTP(_app_factice(exception=abandon()))
    middleware.seuil_ms = 10_000.0
    with caplog.at_level(logging.INFO, logger=_NOM_LOGGER):
        with pytest.raises(BaseException):  # le middleware relaie l'annulation
            _appeler(middleware)
    lignes = [e for e in caplog.records if e.name == _NOM_LOGGER]
    assert len(lignes) == 1
    assert lignes[0].levelno == logging.INFO
    assert "499" in lignes[0].getMessage()
    assert "abandon client" in lignes[0].getMessage()


# --- seuils par préfixe ------------------------------------------------------

@pytest.mark.parametrize("chemin, attendu", [
    ("/api/projects", 1000.0),                       # défaut
    ("/api/copilot/ask", 30_000.0),                  # appel à un modèle de langage
    ("/api/projects/x/export/report.docx", 10_000.0),  # génération Word
    ("/api/projects/x/archive", 10_000.0),           # archive chiffrée
])
def test_le_seuil_depend_du_chemin(chemin, attendu):
    """Sans cette table, `TIMEOUT_LOCAL = 300` (`ai_gateway.py`) garantissait un
    WARNING sur **chaque** appel au copilote : une alerte systématique sur un
    usage normal s'apprend à s'ignorer, et ne sert plus le jour venu."""
    assert seuil_pour_chemin(chemin, 1000.0) == attendu


def test_relever_le_defaut_ne_rend_aucune_route_plus_bavarde():
    """Qui remonte `GREENSHIELD_SEUIL_LENTEUR_MS` cherche le silence : un défaut
    à 60 s ne doit pas rendre le copilote (30 s) subitement plus loquace."""
    assert seuil_pour_chemin("/api/copilot/ask", 60_000.0) == 60_000.0
