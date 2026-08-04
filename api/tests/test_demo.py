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
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    return tmp_path


def test_la_demo_est_creee_avec_un_marqueur_explicite(registre):
    state = projects.create_demo_project()
    assert state["is_demo"] is True


def test_le_nom_et_le_client_annoncent_la_demonstration(registre):
    """F16 : un lecteur doit reconnaître la démonstration sans effort — au nom
    de la mission comme à celui du client."""
    state = projects.create_demo_project()
    assert "DÉMO" in state["name"]
    assert "Fictiv" in state["client"]  # « Fictive » / « Fictif » selon le libellé


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
    state = projects.get_project(projects.DEMO_ID)
    resultat = projects.export_project_document(projects.DEMO_ID, "audit_report")
    titre, contenu = resultat["title"], resultat["markdown"]
    assert projects.DEMO_ID in titre
    assert state["client"] in contenu


# --- Complétude de la vitrine (recette du 31/07/2026) -----------------------
# La démo échouait à son rôle : `aipd_required` à False supprimait le chapitre
# RGPD des rapports, la SoA sortait à 0/93 et les fonctionnalités récentes
# (violations, preuves, multi-référentiel) n'apparaissaient nulle part.

def test_la_demo_couvre_les_deux_referentiels(registre):
    state = projects.create_demo_project()
    assert state["steps"]["cadrage"]["framework_ids"] == ["iso27001", "dora"]
    referentiels = {c["referentiel_id"] for c in state["steps"]["evaluation"]["manual_controls"]}
    assert referentiels == {"iso27001", "dora"}


def test_la_demo_a_une_soa_partiellement_statuee(registre):
    """Ni 0 % (panneau vide) ni 100 % (irréaliste en cours de mission)."""
    state = projects.create_demo_project()
    soa = state["steps"]["evaluation"]["soa"]
    statues = [e for e in soa if e["applicable"] is not None]
    assert len(soa) == 93
    assert 0 < len(statues) < 93
    assert any(e["applicable"] is False for e in statues), "aucune exclusion justifiée"


def test_la_demo_expose_le_registre_des_violations_et_ses_deux_cas(registre):
    state = projects.create_demo_project()
    violations = state["steps"]["diagnostic"]["violations"]
    assert len(violations) >= 2
    assert any(v["notifiee_cnil"] for v in violations)
    # Une violation non notifiée mais justifiée : l'autre branche de l'Art. 33.
    assert any(not v["notifiee_cnil"] and v["justification"].strip() for v in violations)


def test_la_demo_porte_une_preuve_partagee_entre_deux_referentiels(registre):
    """C'est la raison d'être de la bibliothèque de preuves."""
    state = projects.create_demo_project()
    preuves = state["steps"]["evaluation"]["preuves"]
    assert preuves
    partagee = [p for p in preuves
                if len({l["referentiel_id"] for l in p["controles_lies"]}) > 1]
    assert partagee, "aucune preuve ne couvre plusieurs référentiels"


def test_la_demo_declenche_le_chapitre_rgpd_des_rapports(registre):
    """Sans AIPD requise, tout le module RGPD restait invisible en démo."""
    state = projects.create_demo_project()
    assert state["steps"]["diagnostic"]["aipd_required"] is True
    contenu = projects.export_project_document(projects.DEMO_ID, "audit_report")["markdown"]
    assert "Protection des données personnelles" in contenu
    assert "VIO-01" in contenu


def test_la_demo_ne_remonte_aucun_manque_bloquant(registre):
    """Une vitrine ne doit pas s'afficher « non exportable » en démonstration."""
    projects.create_demo_project()
    revue = projects.get_revue_export(projects.DEMO_ID)
    assert revue["pret_pour_export"] is True, revue["manques"]
