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


def test_mission_deja_a_la_version_courante_n_est_pas_retraitee():
    """Une mission déjà à jour traverse la chaîne sans qu'aucune migration ne
    la touche. La donnée de test suit la version courante du schéma : ce test
    vérifie l'idempotence, pas un numéro de version figé."""
    deja_a_jour = {
        "schema_version": schema_migration.CURRENT_SCHEMA_VERSION,
        "socle": {"marqueur": "intact"},
        "grc": {},
        "consulting": {},
    }
    assert schema_migration.migrate(dict(deja_a_jour)) == deja_a_jour


def test_mission_v2_est_migree_vers_la_version_courante_sans_perte():
    """Une mission au schéma v2 (avant le suivi du temps) doit gagner les
    nouveautés v3 sans qu'aucune donnée existante ne soit écrasée."""
    v2 = {"schema_version": 2, "socle": {"marqueur": "intact"}, "grc": {}, "consulting": {}}
    migree = schema_migration.migrate(dict(v2))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert migree["socle"]["marqueur"] == "intact"  # donnée préexistante conservée
    assert migree["socle"]["temps"] == {"entrees": []}  # nouveauté v3 ajoutée


def test_mission_v6_gagne_le_volet_strategique_de_remediation_sans_perte():
    """v6 → v7 (§14.2.3) : le volet stratégique de la remédiation ANSSI
    s'ajoute sans toucher à l'E3R déjà saisi."""
    v6 = {
        "schema_version": 6, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"resilience": {"e3r": {"endiguement": "Isolement réseau"}}},
    }
    migree = schema_migration.migrate(dict(v6))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert migree["steps"]["resilience"]["e3r"]["endiguement"] == "Isolement réseau"
    assert migree["steps"]["resilience"]["strategie_remediation"] == {
        "urgence_redemarrage": "", "couts_risques_redemarrage": "", "decision_direction": "",
    }


def test_mission_v7_gagne_la_chaine_risque_traitement_sans_perte():
    """v7 → v8 : un scénario opérationnel gagne propriétaire/résiduel/
    stratégie/statut, une remédiation gagne responsable/échéance/statut/coût/
    risque lié — sans qu'aucune valeur déjà saisie (event, mitigation,
    measure, priority) ne soit modifiée."""
    v7 = {
        "schema_version": 7, "socle": {}, "grc": {}, "consulting": {},
        "steps": {
            "ebios": {"operational_scenarios": [
                {"id": "SO-01", "event": "Ransomware", "gravity": 4, "likelihood": 3, "mitigation": "EDR"},
            ]},
            "traitement": {"remediations": [
                {"id": "REM-01", "axe": "Protection", "measure": "Déployer le MFA", "priority": "Critique"},
            ]},
        },
    }
    migree = schema_migration.migrate(dict(v7))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION

    scenario = migree["steps"]["ebios"]["operational_scenarios"][0]
    assert scenario["event"] == "Ransomware" and scenario["mitigation"] == "EDR"
    assert scenario["owner"] == "" and scenario["strategie_traitement"] == ""
    assert scenario["gravite_residuelle"] is None and scenario["vraisemblance_residuelle"] is None
    assert scenario["date_revue"] == "" and scenario["statut"] == ""

    remediation = migree["steps"]["traitement"]["remediations"][0]
    assert remediation["measure"] == "Déployer le MFA" and remediation["priority"] == "Critique"
    assert remediation["responsable"] == "" and remediation["echeance"] == ""
    assert remediation["statut"] == "" and remediation["cout_estime"] == "" and remediation["risque_lie"] == ""


def test_mission_v7_sans_scenario_ni_remediation_traverse_sans_erreur():
    """Une mission neuve (listes vides) ne doit pas planter la migration."""
    v7 = {
        "schema_version": 7, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"ebios": {"operational_scenarios": []}, "traitement": {"remediations": []}},
    }
    migree = schema_migration.migrate(dict(v7))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION


def test_needs_migration():
    assert schema_migration.needs_migration(_mission_v1()) is True
    assert schema_migration.needs_migration(schema_migration.migrate(_mission_v1())) is False


def test_mission_iso27001_gagne_la_soa():
    """v8 → v9 (chantier ①) : une mission au référentiel ISO 27001 reçoit les
    93 contrôles de l'Annexe A, non statués."""
    v8 = {
        "schema_version": 8, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"cadrage": {"framework_id": "iso27001"}},
    }
    migree = schema_migration.migrate(dict(v8))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    soa_donnees = migree["steps"]["evaluation"]["soa"]
    assert len(soa_donnees) == 93
    assert all(e["applicable"] is None for e in soa_donnees)


def test_mission_hors_iso27001_ne_recoit_pas_de_soa():
    """DORA/NIS2/EU AI Act n'ont pas de SoA — ce n'est pas une exigence de
    ces référentiels, la porter serait hors sujet."""
    v8 = {
        "schema_version": 8, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"cadrage": {"framework_id": "dora"}},
    }
    migree = schema_migration.migrate(dict(v8))
    assert "soa" not in migree["steps"].get("evaluation", {})


def test_mission_v9_gagne_le_registre_des_violations_vide():
    """v9 → v10 : le registre des violations (RGPD Art. 33-34, G5) démarre
    vide — aucune violation n'est présumée."""
    v9 = {
        "schema_version": 9, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"diagnostic": {"rgpd_register": [{"id": "RGPD-01"}]}},
    }
    migree = schema_migration.migrate(dict(v9))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert migree["steps"]["diagnostic"]["violations"] == []
    assert migree["steps"]["diagnostic"]["rgpd_register"] == [{"id": "RGPD-01"}]


def test_mission_v10_gagne_la_bibliotheque_de_preuves_vide():
    """v10 → v11 (G3bis) : la bibliothèque de preuves multi-référentiels
    démarre vide — aucune preuve n'est présumée exister."""
    v10 = {
        "schema_version": 10, "socle": {}, "grc": {}, "consulting": {},
        "steps": {"evaluation": {"manual_controls": [{"id": "A.5"}]}},
    }
    migree = schema_migration.migrate(dict(v10))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert migree["steps"]["evaluation"]["preuves"] == []
    assert migree["steps"]["evaluation"]["manual_controls"] == [
        {"id": "A.5", "referentiel_id": None, "referentiel_name": None}
    ]


def test_mission_v13_gagne_le_radar_de_maturite_nist_vide():
    """v13 → v14 : le radar de maturité NIST CSF démarre sans aucun tier
    déclaré — aucun niveau de maturité n'est présumé avant que le consultant
    ne le déclare explicitement."""
    v13 = {
        "schema_version": 13, "socle": {}, "consulting": {},
        "grc": {"referentiels_actifs": ["iso27001"], "parcours": {}},
        "steps": {},
    }
    migree = schema_migration.migrate(dict(v13))
    assert migree["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert migree["grc"]["maturite_nist"] == {
        "GV": {"tier": None, "justification": ""},
        "ID": {"tier": None, "justification": ""},
        "PR": {"tier": None, "justification": ""},
        "DE": {"tier": None, "justification": ""},
        "RS": {"tier": None, "justification": ""},
        "RC": {"tier": None, "justification": ""},
    }
    # Ne touche pas aux référentiels déjà actifs.
    assert migree["grc"]["referentiels_actifs"] == ["iso27001"]
