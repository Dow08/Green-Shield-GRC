"""Tests d'intégration du journal d'audit : vérifient que les opérations
métier réelles alimentent effectivement le journal (et pas seulement que la
fonction record() sait écrire quand on l'appelle isolément).

Couvre aussi l'exigence de confidentialité : le contenu des missions ne doit
jamais se retrouver dans le journal.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import audit_log, collecte_technique, data_paths, projects  # noqa: E402


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Missions ET journal isolés dans un répertoire jetable."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    frameworks_dir = tmp_path / "frameworks"
    (frameworks_dir / "custom").mkdir(parents=True)
    monkeypatch.setattr(projects, "PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", projects_dir, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", projects_dir, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", projects_dir, raising=False)
    monkeypatch.setattr(projects, "FRAMEWORKS_DIR", frameworks_dir)
    monkeypatch.setattr(projects.crud, "FRAMEWORKS_DIR", frameworks_dir, raising=False)
    monkeypatch.setattr(projects.exports, "FRAMEWORKS_DIR", frameworks_dir, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "FRAMEWORKS_DIR", frameworks_dir, raising=False)
    monkeypatch.setattr(data_paths, "resolve_data_root", lambda: tmp_path)
    monkeypatch.setattr(audit_log, "_logger", None)
    logging.getLogger("greenshield.audit").handlers.clear()
    yield tmp_path
    logging.getLogger("greenshield.audit").handlers.clear()


def journal(env_path: Path) -> str:
    for handler in logging.getLogger("greenshield.audit").handlers:
        handler.flush()
    log_file = env_path / "logs" / "audit.log"
    return log_file.read_text(encoding="utf-8") if log_file.exists() else ""


def _mission(env_path: Path, p_id: str = "acme", **extra) -> str:
    p_dir = projects.PROJECTS_DIR / p_id
    p_dir.mkdir()
    (p_dir / "targets").mkdir()
    (p_dir / "reports").mkdir()
    state = {"id": p_id, "name": "Acme", "client": "Acme Corp", "steps": {}}
    state.update(extra)
    (p_dir / "project.json").write_text(json.dumps(state), encoding="utf-8")
    
    from modules.database.models import Project
    from modules.database.session import get_db
    db = next(get_db())
    if not db.query(Project).filter_by(id=p_id).first():
        p = Project(id=p_id, owner_id=0, name="Acme", client="Acme Corp", type="grc", status="en_cours", progress=0, steps=state.get("steps", {}))
        db.add(p)
        db.commit()
        
    return p_id


def test_creation_de_mission_est_journalisee(env):
    projects.create_project({"name": "Nouvelle Mission", "client": "X", "type": "grc"})
    assert "project.create" in journal(env)


def test_suppression_de_mission_est_journalisee(env):
    p_id = _mission(env)
    projects.delete_project(p_id)
    contenu = journal(env)
    assert "project.delete" in contenu
    assert f"target={p_id}" in contenu


def test_export_de_document_est_journalise(env):
    p_id = _mission(env)
    projects.export_project_document(p_id, "nda")
    contenu = journal(env)
    assert "project.export" in contenu
    assert "type=nda" in contenu


def test_import_de_referentiel_est_journalise(env):
    projects.import_framework({"id": "mon_ref", "name": "Mon référentiel"})
    assert "framework.import" in journal(env)


def test_appel_copilote_journalise_la_source_sans_le_prompt(env):
    p_id = _mission(env)
    projects.run_project_copilot(p_id, {"prompt": "SECRET_TRES_CONFIDENTIEL_A_NE_PAS_LOGGER"})
    contenu = journal(env)
    assert "copilot.mission" in contenu
    assert "source=offline" in contenu
    # Le contenu du prompt ne doit JAMAIS atteindre le journal.
    assert "SECRET_TRES_CONFIDENTIEL_A_NE_PAS_LOGGER" not in contenu


def test_import_collecte_technique_est_journalise(env):
    p_id = _mission(env)
    collecte_technique.import_asset_into_registry(p_id, {"name": "Serveur SSH", "type": "Réseau"})
    contenu = journal(env)
    assert "collecte.import" in contenu
    assert "asset=BS-01" in contenu


def test_tentative_de_traversee_de_chemin_est_journalisee_comme_refusee(env):
    """Signal de sécurité : une tentative d'exploitation doit laisser une trace."""
    with pytest.raises(HTTPException):
        projects.delete_project("..")
    contenu = journal(env)
    assert "path.rejected" in contenu
    assert "outcome=denied" in contenu


def test_nom_de_fichier_uploade_dangereux_est_journalise_comme_neutralise(env):
    from modules import path_safety

    assert path_safety.safe_filename("../../evil.conf") == "evil.conf"
    contenu = journal(env)
    assert "upload.sanitized" in contenu


def test_le_journal_ne_contient_pas_le_contenu_des_missions(env):
    """Garde-fou de confidentialité : constats, vulnérabilités et données
    personnelles ne doivent jamais transiter par le journal."""
    p_id = _mission(
        env,
        steps={
            "cadrage": {"scope": "PERIMETRE_CONFIDENTIEL_CLIENT"},
            "ebios": {"redoute_events": [{"event": "VULNERABILITE_SECRETE", "gravity": 4}]},
        },
    )
    projects.update_project(p_id, {
        "id": p_id, "name": "Acme", "client": "Acme Corp",
        "steps": {"cadrage": {"scope": "PERIMETRE_CONFIDENTIEL_CLIENT"}},
    })
    projects.export_project_document(p_id, "ebios")

    contenu = journal(env)
    assert "PERIMETRE_CONFIDENTIEL_CLIENT" not in contenu
    assert "VULNERABILITE_SECRETE" not in contenu
    # Mais la traçabilité de l'action, elle, est bien là.
    assert "project.update" in contenu
    assert "project.export" in contenu
