"""Tests du multi-référentiel par mission GRC (31/07/2026).

Un client réel peut être soumis à ISO 27001 *et* DORA *et* NIS2 à la fois —
jusqu'ici une mission ne pouvait en choisir qu'un seul, sans retour possible.
Ces tests vérifient que `manual_controls` porte bien la trace de son
référentiel d'origine une fois plusieurs listes fusionnées, et qu'une
mission mono-référentiel (le cas très majoritaire) continue de se comporter
exactement comme avant.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects, schema_migration  # noqa: E402


def test_une_mission_mono_referentiel_se_comporte_comme_avant():
    state = projects.create_empty_state("acme", "Audit Acme", "Acme Corp", "grc", framework_id="iso27001")
    assert state["steps"]["cadrage"]["framework_id"] == "iso27001"
    assert state["steps"]["cadrage"]["framework_ids"] == ["iso27001"]
    controles = state["steps"]["evaluation"]["manual_controls"]
    assert controles  # ISO 27001 a des exigences représentatives
    assert all(c["referentiel_id"] == "iso27001" for c in controles)
    assert state["steps"]["evaluation"]["soa"]  # SoA toujours générée pour ISO 27001 seul


def test_une_mission_multi_referentiel_fusionne_les_controles_des_deux():
    state = projects.create_empty_state("acme", "Audit Acme", "Acme Corp", "grc",
                                        framework_ids=["iso27001", "dora"])
    assert state["steps"]["cadrage"]["framework_id"] == "iso27001"  # pivot = premier choisi
    assert state["steps"]["cadrage"]["framework_ids"] == ["iso27001", "dora"]
    controles = state["steps"]["evaluation"]["manual_controls"]
    referentiels_presents = {c["referentiel_id"] for c in controles}
    assert referentiels_presents == {"iso27001", "dora"}
    # Chaque contrôle garde son intitulé de référentiel lisible, pas seulement l'id.
    assert any(c["referentiel_name"] and c["referentiel_name"] != c["referentiel_id"] for c in controles)


def test_la_soa_apparait_des_que_iso27001_est_l_un_des_referentiels_actifs():
    """Même si ISO 27001 n'est pas le référentiel pivot (premier choisi), la
    SoA doit être générée — c'est une exigence de ce référentiel, indépendante
    de sa position dans la liste."""
    state = projects.create_empty_state("acme", "Audit Acme", "Acme Corp", "grc",
                                        framework_ids=["dora", "iso27001"])
    assert state["steps"]["evaluation"]["soa"]


def test_une_mission_sans_iso27001_ne_recoit_pas_de_soa_meme_multi_referentiel():
    state = projects.create_empty_state("acme", "Audit Acme", "Acme Corp", "grc",
                                        framework_ids=["dora", "nis2"])
    assert "soa" not in state["steps"]["evaluation"]


# --- Migration v11 -> v12 : backfill des missions déjà existantes ----------

def test_mission_v11_gagne_le_tag_referentiel_sur_ses_controles_existants():
    v11 = {
        "schema_version": 11, "socle": {}, "grc": {}, "consulting": {},
        "steps": {
            "cadrage": {"framework_id": "iso27001", "framework_name": "ISO/IEC 27001:2022"},
            "evaluation": {"manual_controls": [
                {"id": "ISO-A.5", "title": "Politiques", "status": "CONFORME", "notes": "ok"},
            ]},
        },
    }
    migree = schema_migration.migrate(dict(v11))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    controle = migree["steps"]["evaluation"]["manual_controls"][0]
    assert controle["referentiel_id"] == "iso27001"
    assert controle["referentiel_name"] == "ISO/IEC 27001:2022"
    # Rien de déjà saisi n'est modifié.
    assert controle["status"] == "CONFORME" and controle["notes"] == "ok"


def test_mission_v11_sans_controle_traverse_sans_erreur():
    v11 = {
        "schema_version": 11, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"cadrage": {}, "evaluation": {"manual_controls": []}},
    }
    migree = schema_migration.migrate(dict(v11))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION


def test_referentiels_actifs_derive_de_framework_ids_pluriel_si_present():
    v1 = {
        "id": "acme", "type": "grc",
        "steps": {"cadrage": {"framework_id": "iso27001", "framework_ids": ["iso27001", "dora"]}},
    }
    migree = schema_migration.migrate(dict(v1))
    assert migree["grc"]["referentiels_actifs"] == ["iso27001", "dora"]
