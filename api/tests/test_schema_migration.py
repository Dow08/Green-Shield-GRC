"""Tests de la chaîne de migration du schéma des missions (cf. audit F4)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import schema_migration  # noqa: E402


def _mission_v1() -> dict:
    """Mission telle qu'elle existait avant le jalon 1 : pas de schema_version."""
    return {
        "id": "acme", "name": "Audit ACME", "client": "ACME", "type": "grc",
        "steps": {
            "cadrage": {"scope": "SI de production", "framework_id": "iso27001"},
        },
    }


def test_mission_sans_version_est_migree_vers_la_version_courante():
    mission = schema_migration.migrate(_mission_v1())
    assert mission["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION


def test_migration_ajoute_sans_effacer():
    """Aucune donnée existante ne doit disparaître pendant la migration."""
    original = _mission_v1()
    cles_avant = set(original.keys())
    migree = schema_migration.migrate(dict(original))
    assert cles_avant <= set(migree.keys())
    assert migree["steps"]["cadrage"]["scope"] == "SI de production"


def test_socle_et_volets_crees_a_partir_du_type_existant():
    grc = schema_migration.migrate(_mission_v1())
    assert grc["grc"]["active"] is True
    assert grc["grc"]["referentiels_actifs"] == ["iso27001"]
    assert grc["consulting"]["active"] is False

    consulting = schema_migration.migrate({**_mission_v1(), "type": "consulting", "steps": {"cadrage": {}}})
    assert consulting["grc"]["active"] is False
    assert consulting["consulting"]["active"] is True


def test_mission_deja_a_jour_traverse_sans_modification():
    migree_une_fois = schema_migration.migrate(_mission_v1())
    migree_deux_fois = schema_migration.migrate(dict(migree_une_fois))
    assert migree_deux_fois == migree_une_fois


def test_mission_deja_v2_n_est_pas_retraitee():
    dejaV2 = {"schema_version": 2, "socle": {"marqueur": "intact"}, "grc": {}, "consulting": {}}
    assert schema_migration.migrate(dict(dejaV2)) == dejaV2


def test_needs_migration():
    assert schema_migration.needs_migration(_mission_v1()) is True
    assert schema_migration.needs_migration(schema_migration.migrate(_mission_v1())) is False
