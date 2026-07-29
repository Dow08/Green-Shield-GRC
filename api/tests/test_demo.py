"""Tests du jeu de démonstration anonymisé (F16).

Enjeu de confidentialité : démontrer l'outil ne doit jamais exiger d'ouvrir une
mission cliente réelle. La mission de démonstration doit donc être fictive,
reconnaissable comme telle, et suffisamment garnie pour être démonstrative.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects, schema_migration  # noqa: E402


@pytest.fixture()
def registre(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    return tmp_path


def test_la_demo_est_creee_avec_un_marqueur_explicite(registre):
    state = projects.create_demo_project()
    assert state["is_demo"] is True


def test_le_nom_et_le_client_annoncent_la_demonstration(registre):
    state = projects.create_demo_project()
    assert "DÉMO" in state["name"]
    assert "Fictif" in state["client"]


def test_la_demo_est_au_schema_courant(registre):
    state = projects.create_demo_project()
    assert state["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION


def test_la_demo_est_persistee_et_listee(registre):
    projects.create_demo_project()
    assert (registre / projects.DEMO_ID / "project.json").is_file()
    assert projects.DEMO_ID in [p["id"] for p in projects.list_projects()]


def test_la_demo_embarque_du_temps_consomme(registre):
    """Pour démontrer le suivi charges/budget, il faut des données dedans."""
    state = projects.create_demo_project()
    entrees = state["socle"]["temps"]["entrees"]
    assert len(entrees) >= 2
    assert state["socle"]["qualification"]["budget"]


def test_la_demo_embarque_une_configuration_auditable(registre):
    """Le scan technique doit avoir de quoi trouver pendant une démonstration."""
    projects.create_demo_project()
    cible = registre / projects.DEMO_ID / "targets" / "sshd_config"
    assert cible.is_file()
    contenu = cible.read_text(encoding="utf-8")
    assert "PermitRootLogin yes" in contenu
    assert "FICTIVE" in contenu


def test_le_scan_technique_fonctionne_sur_la_demo(registre):
    projects.create_demo_project()
    state = projects.run_project_audit(projects.DEMO_ID)
    resultats = state["steps"]["evaluation"]["technical_results"]
    assert resultats["counts"]["evaluated"] > 0


def test_recreer_la_demo_repart_d_un_etat_propre(registre):
    projects.create_demo_project()
    chemin = registre / projects.DEMO_ID / "project.json"
    pollue = json.loads(chemin.read_text(encoding="utf-8"))
    pollue["name"] = "modifié pendant la démo"
    chemin.write_text(json.dumps(pollue), encoding="utf-8")

    state = projects.create_demo_project()
    assert "DÉMO" in state["name"]


def test_la_demo_n_ecrase_aucune_mission_reelle(registre):
    reelle = registre / "mission_reelle"
    reelle.mkdir()
    (reelle / "project.json").write_text(
        json.dumps({"id": "mission_reelle", "name": "Vraie", "steps": {}}), encoding="utf-8")

    projects.create_demo_project()

    assert json.loads((reelle / "project.json").read_text(encoding="utf-8"))["name"] == "Vraie"


def test_la_demo_est_exportable_comme_une_mission_ordinaire(registre):
    """Elle doit servir à démontrer l'export, donc le traverser réellement."""
    projects.create_demo_project()
    titre, contenu = None, None
    resultat = projects.export_project_document(projects.DEMO_ID, "audit_report")
    titre, contenu = resultat["title"], resultat["markdown"]
    assert projects.DEMO_ID in titre
    assert "Cabinet Fictif" in contenu
