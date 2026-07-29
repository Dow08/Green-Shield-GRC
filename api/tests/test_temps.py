"""Tests du suivi du temps consommé par mission (F19).

Le temps consommé alimente la facturation et le pilotage client : une entrée
perdue ou mal validée a un coût réel. D'où la couverture des cas limites.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects, schema_migration  # noqa: E402


@pytest.fixture()
def mission(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    p_dir = tmp_path / "acme"
    p_dir.mkdir()
    (p_dir / "project.json").write_text(
        json.dumps({"id": "acme", "name": "Acme", "client": "Acme Corp", "steps": {}}),
        encoding="utf-8",
    )
    return "acme"


def _entrees(state: dict) -> list[dict]:
    return state["socle"]["temps"]["entrees"]


# --- Migration ------------------------------------------------------------

def test_migration_v3_ajoute_le_journal_de_temps():
    state = schema_migration.migrate({"id": "x"})
    assert state["socle"]["temps"] == {"entrees": []}
    assert state["schema_version"] == 3


def test_migration_v3_n_ecrase_pas_un_journal_existant():
    existant = {"entrees": [{"id": "T-001", "phase": "cadrage", "minutes": 60}]}
    state = schema_migration.migrate({"schema_version": 2, "socle": {"temps": existant}})
    assert state["socle"]["temps"] == existant


def test_une_mission_v1_traverse_toute_la_chaine_jusqu_au_temps():
    """Une mission d'avant le jalon 1 doit ressortir avec socle ET temps."""
    state = schema_migration.migrate({"id": "vieux", "type": "grc", "steps": {}})
    assert "qualification" in state["socle"]
    assert state["socle"]["temps"]["entrees"] == []


# --- Ajout d'entrées ------------------------------------------------------

def test_ajoute_une_entree_de_temps(mission):
    state = projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": 90})
    entrees = _entrees(state)
    assert len(entrees) == 1
    assert entrees[0]["id"] == "T-001"
    assert entrees[0]["phase"] == "cadrage"
    assert entrees[0]["minutes"] == 90


def test_date_par_defaut_est_aujourd_hui(mission):
    state = projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": 30})
    assert _entrees(state)[0]["date"] == date.today().isoformat()


def test_date_explicite_est_respectee(mission):
    state = projects.add_temps_entry(mission, {"phase": "ebios", "minutes": 30, "date": "2026-07-01"})
    assert _entrees(state)[0]["date"] == "2026-07-01"


def test_les_identifiants_sont_sequentiels_et_uniques(mission):
    for _ in range(3):
        state = projects.add_temps_entry(mission, {"phase": "autre", "minutes": 15})
    ids = [e["id"] for e in _entrees(state)]
    assert ids == ["T-001", "T-002", "T-003"]
    assert len(set(ids)) == 3


def test_phase_absente_retombe_sur_autre(mission):
    state = projects.add_temps_entry(mission, {"minutes": 45})
    assert _entrees(state)[0]["phase"] == "autre"


def test_la_note_est_tronquee_pour_ne_pas_gonfler_le_fichier(mission):
    state = projects.add_temps_entry(mission, {"phase": "autre", "minutes": 10, "note": "x" * 500})
    assert len(_entrees(state)[0]["note"]) == 200


def test_l_ajout_est_persiste_sur_disque(mission, tmp_path):
    projects.add_temps_entry(mission, {"phase": "tprm", "minutes": 120})
    sauvegarde = json.loads((tmp_path / mission / "project.json").read_text(encoding="utf-8"))
    assert sauvegarde["socle"]["temps"]["entrees"][0]["minutes"] == 120


def test_la_progression_reste_coherente_apres_saisie_de_temps(mission):
    """Non-régression : la saisie de temps renvoyait la progression stockée
    (périmée) au lieu de la recalculer, ce qui faisait chuter la jauge à 0 %
    dans l'interface. Le temps consommé n'influence pas la progression
    méthodologique — il ne doit donc pas la modifier non plus."""
    avant = projects.get_project(mission)["progress"]
    apres = projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": 60})["progress"]
    assert apres == avant

    apres_suppression = projects.delete_temps_entry(mission, "T-001")["progress"]
    assert apres_suppression == avant


# --- Validation des cas limites -------------------------------------------

@pytest.mark.parametrize("minutes", [0, -30])
def test_duree_nulle_ou_negative_est_rejetee(mission, minutes):
    with pytest.raises(HTTPException) as exc:
        projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": minutes})
    assert exc.value.status_code == 400


def test_duree_non_numerique_est_rejetee(mission):
    with pytest.raises(HTTPException) as exc:
        projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": "deux heures"})
    assert exc.value.status_code == 400


def test_duree_superieure_a_24h_est_rejetee(mission):
    """Garde-fou anti-faute de frappe : 6000 au lieu de 600."""
    with pytest.raises(HTTPException) as exc:
        projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": 6000})
    assert exc.value.status_code == 400


def test_phase_inconnue_est_rejetee(mission):
    with pytest.raises(HTTPException) as exc:
        projects.add_temps_entry(mission, {"phase": "phase_inventee", "minutes": 60})
    assert exc.value.status_code == 400


def test_ajout_sur_mission_introuvable_renvoie_404(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        projects.add_temps_entry("inexistante", {"phase": "cadrage", "minutes": 60})
    assert exc.value.status_code == 404


def test_ajout_avec_p_id_traverse_est_rejete(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        projects.add_temps_entry("..", {"phase": "cadrage", "minutes": 60})
    assert exc.value.status_code == 400


# --- Suppression ----------------------------------------------------------

def test_supprime_une_entree(mission):
    projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": 60})
    projects.add_temps_entry(mission, {"phase": "ebios", "minutes": 30})
    state = projects.delete_temps_entry(mission, "T-001")
    restantes = _entrees(state)
    assert len(restantes) == 1
    assert restantes[0]["id"] == "T-002"


def test_suppression_d_une_entree_inexistante_renvoie_404(mission):
    with pytest.raises(HTTPException) as exc:
        projects.delete_temps_entry(mission, "T-999")
    assert exc.value.status_code == 404


def test_un_id_reste_unique_apres_suppression(mission):
    """Après suppression de la dernière entrée, le prochain id ne doit pas
    réutiliser un identifiant déjà porté par une entrée existante."""
    projects.add_temps_entry(mission, {"phase": "cadrage", "minutes": 60})
    projects.add_temps_entry(mission, {"phase": "ebios", "minutes": 30})
    projects.delete_temps_entry(mission, "T-002")
    state = projects.add_temps_entry(mission, {"phase": "autre", "minutes": 10})
    ids = [e["id"] for e in _entrees(state)]
    assert len(set(ids)) == len(ids)
