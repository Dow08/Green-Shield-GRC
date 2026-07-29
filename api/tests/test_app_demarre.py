"""Test de fumée : l'application s'assemble-t-elle réellement ?

Introduit après l'incident du 29/07/2026 — `python-multipart` manquait dans
`requirements.txt`. FastAPI lève une RuntimeError *au moment de l'import* du
module déclarant une route `UploadFile`, donc l'API ne démarrait pas du tout
avec une installation propre (y compris dans l'image Docker). Aucun test ne
l'avait vu : ils importaient tous des modules isolément, et le paquet était
présent par ailleurs sur le poste de développement.

Ce fichier vérifie ce qu'aucun test unitaire ne couvrait : que `main` s'importe
et que les routes attendues sont bien montées.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402


def _chemins() -> set[str]:
    return {getattr(r, "path", "") for r in main.app.routes}


def test_l_application_s_importe_et_expose_des_routes():
    assert len(main.app.routes) > 0


def test_la_route_de_sante_est_montee():
    assert "/health" in _chemins()


def test_les_routes_des_quatre_modules_sont_montees():
    chemins = _chemins()
    attendues = {
        "/api/auditcraft/run",                  # AuditCraft-GRC
        "/api/projects",                        # Registre de missions
        "/api/copilot/ask",                     # Copilote GRC
        "/api/collecte/fingerprint",            # Collecte technique
    }
    manquantes = attendues - chemins
    assert not manquantes, f"routes absentes : {manquantes}"


def test_la_route_d_upload_est_montee():
    """C'est précisément cette route (UploadFile/File) dont la déclaration
    échouait sans python-multipart."""
    assert "/api/projects/{p_id}/upload" in _chemins()


def test_les_routes_de_suivi_du_temps_sont_montees():
    chemins = _chemins()
    assert "/api/projects/{p_id}/temps" in chemins
    assert "/api/projects/{p_id}/temps/{entry_id}" in chemins
