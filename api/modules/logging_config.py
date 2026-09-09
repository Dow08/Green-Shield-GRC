"""logging_config.py — journalisation applicative (console).

À ne pas confondre avec `audit_log.py`, qui est le journal *métier* des actions
sensibles (qui a supprimé quelle mission), écrit dans un fichier dédié et
volontairement isolé (`propagate = False`). Le présent module s'occupe du
journal *technique* : ce que le code raconte sur son propre fonctionnement.

Constat de l'audit du 09/09/2026 : 19 appels à `logging.getLogger(...)` dans
`api/`, mais aucun handler nulle part sur le logger racine. Vérifié
empiriquement : les messages ne sortaient que par le mécanisme `lastResort` de
Python — donc à partir de WARNING seulement, sans horodatage ni nom de module.
Tout `logger.info(...)` et `logger.debug(...)` du projet était perdu.

Ce que cet angle mort a coûté : lors de la saturation du pool SQLAlchemy des
08-09/09/2026 (36 requêtes en échec sur 224), le seul journal disponible était
celui d'uvicorn, qui désigne la requête *victime* et jamais la session fuyante.
Un signal précurseur a été ajouté dans le même lot de correctifs —
`database/session.py::_tracer_tension_pool` émet un `logger.warning` dès 15
connexions empruntées — mais il n'aurait eu nulle part où sortir sans la
configuration ci-dessous : les deux ne valent qu'ensemble.

Cohabitation avec uvicorn (le point délicat)
--------------------------------------------
uvicorn applique sa propre `dictConfig` au démarrage. Trois raisons pour
lesquelles la configuration ci-dessous ne peut pas entrer en conflit avec elle,
vérifiées sur `uvicorn.config.LOGGING_CONFIG` :

  * on ne configure QUE le logger racine ; la configuration d'uvicorn ne
    contient pas de clé `root`, et `logging.config` laisse alors la racine
    intacte ;
  * `uvicorn` et `uvicorn.access` y sont déclarés `propagate: False`, et
    `uvicorn.error` s'arrête sur son parent `uvicorn` : aucun message d'uvicorn
    ne remonte jusqu'à notre handler. Les logs d'accès HTTP gardent donc leur
    format d'origine et n'apparaissent pas en double ;
  * `disable_existing_loggers` y vaut `False` : les loggers déjà créés par nos
    modules ne sont pas désactivés au passage.

Reste un effet de bord à connaître, car il dicte un choix ci-dessous :
`dictConfig` appelle `_clearExistingHandlers()`, qui **ferme** tous les
handlers existants. Pour un `StreamHandler` sur `sys.stderr` c'est sans
conséquence (`close()` ne ferme pas le flux sous-jacent), mais c'est la raison
pour laquelle on n'ouvre surtout pas ici de handler fichier : il serait fermé
au démarrage d'uvicorn dans `desktop.py`, qui importe `main` **avant**
d'appeler `uvicorn.run`.

Enfin, `desktop.py` lance uvicorn avec `log_level="warning"` : ce réglage ne
touche que les loggers `uvicorn.*`, nos INFO applicatifs continuent de sortir.
"""
from __future__ import annotations

import logging
import os
import sys

# Format : horodatage, niveau, nom du logger, message. Le nom du logger est la
# seule information qui aurait permis de rattacher un message à son origine
# pendant l'incident du pool ; il est en position fixe pour rester grep-able.
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

# Marqueur posé sur notre handler. `configurer()` est appelée à l'import de
# `main`, lui-même importé par la quasi-totalité des fichiers de tests : sans ce
# repère, chaque import empilerait un handler de plus et les messages
# sortiraient en double, puis en triple.
_MARQUEUR = "_greenshield_console"

# Bibliothèques tierces bavardes à INFO et sans valeur de diagnostic ici. On les
# plafonne nommément plutôt que de remonter le niveau global, qui masquerait du
# même coup nos propres INFO.
_TIERS_BAVARDS = ("httpx", "httpcore", "urllib3", "multipart", "python_multipart")

_NIVEAU_PAR_DEFAUT = logging.INFO


def _resoudre_niveau(niveau: int | str | None) -> int:
    """Traduit un niveau donné en clair ("DEBUG") ou par variable
    d'environnement. Toute valeur inconnue retombe sur INFO plutôt que de faire
    échouer le démarrage du serveur pour une faute de frappe."""
    if niveau is None:
        niveau = os.environ.get("GREENSHIELD_LOG_LEVEL") or _NIVEAU_PAR_DEFAUT
    if isinstance(niveau, int):
        return niveau
    resolu = logging.getLevelName(str(niveau).strip().upper())
    return resolu if isinstance(resolu, int) else _NIVEAU_PAR_DEFAUT


def configurer(niveau: int | str | None = None) -> logging.Logger:
    """Installe (une seule fois) le handler console sur le logger racine.

    Idempotente : réappelée, elle se contente de réajuster le niveau. Renvoie le
    logger racine pour permettre une vérification directe en test ou en console.
    """
    racine = logging.getLogger()
    racine.setLevel(_resoudre_niveau(niveau))

    for handler in racine.handlers:
        if getattr(handler, _MARQUEUR, False):
            return racine

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, _FORMAT_DATE))
    setattr(handler, _MARQUEUR, True)
    racine.addHandler(handler)

    for nom in _TIERS_BAVARDS:
        logging.getLogger(nom).setLevel(logging.WARNING)

    return racine
