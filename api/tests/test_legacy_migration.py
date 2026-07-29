"""Tests de la migration unique depuis l'ancien emplacement des missions.

Constat du 29/07/2026 : `_migrate_legacy_projects()` s'exécute à chaque import
du module. Sans garde-fou, pointer `GREENSHIELD_DATA_DIR` vers un répertoire de
test recopiait les missions clientes réelles à chaque démarrage.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects  # noqa: E402


@pytest.fixture()
def legacy_et_cible(tmp_path, monkeypatch):
    legacy = tmp_path / "ancien"
    legacy.mkdir()
    mission = legacy / "mission_a"
    mission.mkdir()
    (mission / "project.json").write_text(json.dumps({"id": "mission_a"}), encoding="utf-8")

    cible = tmp_path / "nouveau"
    cible.mkdir()

    monkeypatch.setattr(projects, "_LEGACY_PROJECTS_DIR", legacy)
    monkeypatch.setattr(projects, "PROJECTS_DIR", cible)
    return legacy, cible


def test_migre_les_missions_au_premier_passage(legacy_et_cible):
    _, cible = legacy_et_cible
    projects._migrate_legacy_projects()
    assert (cible / "mission_a" / "project.json").is_file()


def test_pose_un_marqueur_apres_migration(legacy_et_cible):
    _, cible = legacy_et_cible
    projects._migrate_legacy_projects()
    assert (cible / ".legacy-migre").is_file()


def test_ne_remigre_pas_une_mission_supprimee_volontairement(legacy_et_cible):
    """Le cœur du correctif : après une première migration, supprimer une
    mission dans le nouvel emplacement ne doit PAS la voir réapparaître au
    démarrage suivant."""
    _, cible = legacy_et_cible
    projects._migrate_legacy_projects()
    shutil_target = cible / "mission_a"
    assert shutil_target.is_dir()

    # L'utilisateur supprime la mission, puis relance l'application.
    import shutil
    shutil.rmtree(shutil_target)
    projects._migrate_legacy_projects()

    assert not shutil_target.exists(), "la mission supprimée a été ressuscitée"


def test_ne_recopie_pas_dans_un_repertoire_de_test(legacy_et_cible, tmp_path, monkeypatch):
    """Pointer GREENSHIELD_DATA_DIR ailleurs après une migration déjà faite ne
    doit pas dupliquer les missions — sauf s'il s'agit d'un tout nouvel
    emplacement, où la migration est alors légitime et unique."""
    _, cible = legacy_et_cible
    projects._migrate_legacy_projects()

    autre = tmp_path / "repertoire_de_test"
    autre.mkdir()
    monkeypatch.setattr(projects, "PROJECTS_DIR", autre)
    projects._migrate_legacy_projects()          # 1re fois : migration légitime
    projects._migrate_legacy_projects()          # 2e fois : ne doit rien refaire
    projects._migrate_legacy_projects()          # 3e fois non plus

    assert (autre / ".legacy-migre").is_file()
    assert len([p for p in autre.iterdir() if p.is_dir()]) == 1


def test_ne_fait_rien_si_l_ancien_emplacement_n_existe_pas(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "_LEGACY_PROJECTS_DIR", tmp_path / "inexistant")
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path / "cible")
    projects._migrate_legacy_projects()  # ne doit rien lever
    assert not (tmp_path / "cible").exists()


def test_n_ecrase_jamais_une_mission_existante(legacy_et_cible):
    _, cible = legacy_et_cible
    existante = cible / "mission_a"
    existante.mkdir()
    (existante / "project.json").write_text(json.dumps({"id": "version_locale"}), encoding="utf-8")

    projects._migrate_legacy_projects()

    contenu = json.loads((existante / "project.json").read_text(encoding="utf-8"))
    assert contenu["id"] == "version_locale"
