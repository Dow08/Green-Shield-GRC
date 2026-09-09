"""GREEN SHIELD — API (FastAPI).

Expose le registre des modules, la gestion des projets, et l'exécution des audits au frontend React.
Le moteur reste 100 % Python ; l'API n'est qu'une façade JSON.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

# Journalisation configurée AVANT tout autre import de `modules` : plusieurs de
# ces modules journalisent dès l'import (secret JWT illisible, clé de
# chiffrement non persistable…). Configurée plus bas, ces alertes de démarrage
# repasseraient par le `lastResort` de Python, sans horodatage ni origine —
# c'est précisément l'angle mort relevé par l'audit du 09/09/2026.
from modules import logging_config

logging_config.configurer()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from modules.auth import get_current_user, limiter
from modules import ressources
from modules import aipd
from fastapi.middleware.cors import CORSMiddleware

from modules import auditcraft_grc
from modules import journal_requetes
from modules.projects.router import router as projects_router
from modules import collecte_technique
from modules import copilot_grc
from modules.connectors import router as connectors_router
from modules.auth_routes import router as auth_router

# Cible auditée : /audit/target en conteneur (monté :ro), sinon ../target_lab/config en local.
TARGET_DIR = os.environ.get("AUDIT_TARGET_DIR", str(Path(__file__).resolve().parent.parent / "target_lab" / "config"))

_log = logging.getLogger("greenshield.main")

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request

app = FastAPI(title="GREEN SHIELD API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# `default_limits` seul ne freine rien : il faut le middleware pour que la
# limite s'applique aux routes qui n'ont pas de décorateur explicite.
app.add_middleware(SlowAPIMiddleware)

# Origines autorisées : 8080 = SPA servie par nginx en production, 5175 = serveur
# de développement Vite.
#
# 09/09/2026 : la liste mentionnait 5173, port par défaut de Vite — mais
# `web/vite.config.ts` fixe `port: 5175` en `strictPort`. L'écart passait
# inaperçu parce que le développement passe par le proxy `/api` de Vite, donc en
# même origine : CORS n'entre jamais en jeu. Tout appel direct au backend depuis
# le navigateur aurait pourtant été refusé, sans que rien n'explique pourquoi.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# En-têtes de sécurité HTTP, indépendants de nginx (V-06, audit combiné du
# 06/08/2026). `web/nginx.conf` ne protège que le déploiement Docker : ce
# même FastAPI est aussi servi en direct par l'exécutable de bureau
# (PyInstaller, desktop.py) et en développement (`uvicorn`), sans reverse
# proxy devant — ces deux modes n'avaient jusqu'ici AUCUN de ces en-têtes.
# Mêmes valeurs que nginx.conf, pour un comportement identique quel que soit
# le mode d'exécution.
_CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self';")


@app.middleware("http")
async def ajouter_en_tetes_securite(request: Request, call_next):
    reponse = await call_next(request)
    reponse.headers["X-Frame-Options"] = "DENY"
    reponse.headers["X-Content-Type-Options"] = "nosniff"
    reponse.headers["Referrer-Policy"] = "no-referrer"
    reponse.headers["Content-Security-Policy"] = _CSP
    return reponse


# Journal d'accès HTTP avec durée par requête (audit du 09/09/2026 : c'est la
# donnée qui manquait pendant la saturation du pool — sans durée, impossible de
# distinguer l'endpoint fuyant de ses victimes).
#
# Inscrit en DERNIER volontairement : `add_middleware` empile en tête de liste,
# le dernier inscrit est donc le middleware le plus EXTERNE. Le chronomètre
# englobe ainsi les en-têtes de sécurité, CORS et le limiteur de débit — un
# rejet 429 de slowapi ou une préflight refusée produisent eux aussi leur ligne,
# ce qui ne serait pas le cas s'il était inscrit plus tôt.
#
# Ce module muselle au passage la ligne d'accès d'uvicorn, qu'il remplace plutôt
# que de la doubler : voir son en-tête pour le détail du raisonnement.
journal_requetes.installer(app)


# Enregistrement des routes projets/frameworks/collecte technique/copilote GRC (sécurisées)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(collecte_technique.router)
app.include_router(copilot_grc.router)
app.include_router(connectors_router)

# Registre des modules (un descripteur par module installé).
MODULES = [auditcraft_grc.MODULE]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "green-shield-api", "version": "1.0.0"}


@app.get("/api/modules")
def list_modules(_user=Depends(get_current_user)) -> list[dict]:
    """Registre : la nav du shell est construite à partir de cette liste."""
    return MODULES


@app.get("/api/aipd/obligations")
def aipd_obligations(_user=Depends(get_current_user)) -> list[dict]:
    """Référentiel des cinq obligations de conduite de l'AIPD (§14.2.1) : pas
    l'état d'une mission, seulement le libellé, l'article et l'aide de
    chacune — d'où l'appel à `aipd.py` plutôt qu'à une mission stockée."""
    return aipd.referentiel_obligations()


@app.get("/api/auditcraft/run")
def auditcraft_run(_user=Depends(get_current_user)) -> dict:
    """Exécute l'audit AuditCraft-GRC sur la cible et renvoie le résultat complet."""
    try:
        return auditcraft_grc.run(TARGET_DIR)
    except Exception:
        # Le détail (chemin, trace) reste dans les logs serveur : le renvoyer
        # au client exposerait la structure du système de fichiers du poste.
        _log.exception("Échec de l'audit AuditCraft-GRC (cible=%s)", TARGET_DIR)
        raise HTTPException(status_code=500, detail="Audit impossible : cible ou référentiel introuvable ou illisible.")


# --- Frontend embarqué (exécutable de bureau) --------------------------------
# Monté en dernier, après toutes les routes d'API : le point de montage racine
# capterait sinon `/api/...`. Absent en développement (Vite sert le frontend)
# et en Docker (nginx s'en charge) — d'où la condition, plutôt qu'un chemin
# supposé toujours présent.
_FRONTEND = ressources.frontend_dir()
if (_FRONTEND / "index.html").is_file():

    @app.get("/{chemin:path}", include_in_schema=False)
    def servir_spa(chemin: str) -> FileResponse:
        """Sert le frontend, avec repli sur `index.html`.

        L'application est une SPA : une URL profonde rafraîchie ne correspond à
        aucun fichier et doit renvoyer la page d'entrée, c'est le routeur
        client qui décide de l'écran.
        """
        demande = (_FRONTEND / chemin).resolve()
        # `resolve()` neutralise les `..` : on refuse toute sortie du dossier.
        if demande.is_file() and demande.is_relative_to(_FRONTEND.resolve()):
            return FileResponse(demande)
        return FileResponse(_FRONTEND / "index.html")
