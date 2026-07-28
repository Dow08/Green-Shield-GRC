"""GREEN SHIELD — API (FastAPI).

Expose le registre des modules, la gestion des projets, et l'exécution des audits au frontend React.
Le moteur reste 100 % Python ; l'API n'est qu'une façade JSON.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from modules import auditcraft_grc
from modules import projects
from modules import collecte_technique
from modules import copilot_grc

# Cible auditée : /audit/target en conteneur (monté :ro), sinon ../lab_target en local.
TARGET_DIR = os.environ.get("AUDIT_TARGET_DIR", str(Path(__file__).resolve().parent.parent / "lab_target"))     

app = FastAPI(title="GREEN SHIELD API", version="1.0.0")

# Le frontend (SPA) est servi sur http://localhost:8080 en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes projets/frameworks/collecte technique/copilote GRC
app.include_router(projects.router)
app.include_router(collecte_technique.router)
app.include_router(copilot_grc.router)

# Registre des modules (un descripteur par module installé).
MODULES = [auditcraft_grc.MODULE]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "green-shield-api", "version": "1.0.0"}


@app.get("/api/modules")
def list_modules() -> list[dict]:
    """Registre : la nav du shell est construite à partir de cette liste."""
    return MODULES


@app.get("/api/auditcraft/run")
def auditcraft_run() -> dict:
    """Exécute l'audit AuditCraft-GRC sur la cible et renvoie le résultat complet."""
    try:
        return auditcraft_grc.run(TARGET_DIR)
    except Exception as exc:  # cible/référentiel introuvable → 500 explicite
        raise HTTPException(status_code=500, detail=str(exc))
