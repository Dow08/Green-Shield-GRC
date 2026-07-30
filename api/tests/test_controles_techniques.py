"""Rattachement des pratiques aux contrôles CIS / NIST CSF (§14.2.4).

Les booléens `vulnerabilities_active` et `logging_active` existaient sans
mapping : un consultant cochait une case sans pouvoir dire à quelle exigence
elle répond. Ces tests verrouillent le rattachement et, surtout, le fait que ce
module **lit** un état saisi ailleurs sans jamais le rejuger.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import controles_techniques as ct  # noqa: E402
from modules import report_builder  # noqa: E402


def _par_id(resultat: dict) -> dict[str, dict]:
    return {p["id"]: p for p in resultat["pratiques"]}


# --- Le référentiel ---------------------------------------------------------

def test_les_quatre_mappings_du_spec_sont_couverts():
    refs = {m["ref"] for p in ct.PRATIQUES for m in p["mappings"]}
    assert {"CIS 7", "ID.RA-01", "CIS 8", "ID.RA-10"} <= refs


def test_l_inventaire_couvre_le_cycle_de_vie():
    refs = {m["ref"] for m in ct.mappings_de("inventaire")}
    assert "ID.AM" in refs


def test_chaque_mapping_nomme_son_referentiel():
    """« CIS 7 » seul est ambigu hors contexte : un livrable client doit dire
    de quel référentiel et de quelle version il parle."""
    for pratique in ct.PRATIQUES:
        for mapping in pratique["mappings"]:
            assert mapping["referentiel"] in ("CIS v8", "NIST CSF 2.0")


def test_chaque_pratique_indique_la_phase_ou_elle_se_constate():
    """Sans cela, le consultant ne sait pas où aller corriger l'écart."""
    assert all(1 <= p["phase"] <= 6 and p["phase_libelle"] for p in ct.PRATIQUES)


def test_le_referentiel_ne_recopie_pas_le_texte_normatif():
    """F3 : intitulés courts reformulés."""
    for pratique in ct.PRATIQUES:
        assert all(len(m["intitule"]) < 80 for m in pratique["mappings"])


def test_mappings_d_une_pratique_inconnue():
    assert ct.mappings_de("nexiste_pas") == []


def test_le_referentiel_renvoie_des_copies():
    """Sinon un appelant qui modifie sa réponse corrompt la table du module."""
    ct.referentiel()[0]["mappings"][0]["ref"] = "PIRATÉ"
    assert ct.mappings_de("inventaire")[0]["ref"] != "PIRATÉ"


# --- Lecture de l'état ------------------------------------------------------

def test_une_mission_vide_ne_couvre_rien():
    resultat = ct.etat({})
    assert resultat["couvertes"] == 0
    assert resultat["total"] == 4
    assert resultat["taux"] == 0


def test_l_inventaire_est_couvert_des_qu_un_bien_support_existe():
    resultat = ct.etat({"steps": {"cadrage": {"assets_support": [{"id": "BS-01"}]}}})
    pratique = _par_id(resultat)["inventaire"]
    assert pratique["couverte"] is True
    assert "1 bien(s) support" in pratique["justification"]


def test_la_gestion_des_vulnerabilites_suit_le_booleen_de_la_phase_2():
    resultat = ct.etat({"steps": {"diagnostic": {"vulnerabilities_active": True}}})
    assert _par_id(resultat)["vulnerabilites"]["couverte"] is True


def test_la_journalisation_suit_le_booleen_de_la_phase_5():
    resultat = ct.etat({"steps": {"resilience": {"logging_active": True}}})
    assert _par_id(resultat)["journalisation"]["couverte"] is True


def test_la_justification_cite_la_phase_d_origine():
    """La donnée reste vérifiable : le module dit d'où il la tient."""
    resultat = ct.etat({"steps": {"resilience": {"logging_active": True}}})
    assert "phase 5" in _par_id(resultat)["journalisation"]["justification"]


def test_le_taux_compte_les_pratiques_couvertes():
    resultat = ct.etat({"steps": {
        "cadrage": {"assets_support": [{"id": "BS-01"}]},
        "diagnostic": {"vulnerabilities_active": True},
    }})
    assert (resultat["couvertes"], resultat["taux"]) == (2, 50)


# --- L'évaluation fournisseurs vient du TPRM -------------------------------

def _mission_grc(satisfait: bool) -> dict:
    return {"steps": {"tprm": {"tiers": [
        {"name": "AWS", "exigences": [{"id": "NIST-ID.RA-10", "satisfait": satisfait}]},
    ]}}}


def test_l_evaluation_fournisseurs_est_lue_depuis_les_exigences_tprm():
    assert _par_id(ct.etat(_mission_grc(True)))["evaluation_fournisseurs"]["couverte"] is True


def test_un_fournisseur_non_evalue_laisse_la_pratique_a_decouvert():
    resultat = _par_id(ct.etat(_mission_grc(False)))["evaluation_fournisseurs"]
    assert resultat["couverte"] is False
    assert "0 tiers évalué(s)" in resultat["justification"]


def test_une_mission_consulting_n_invente_pas_un_ecart():
    """Le volet Consulting n'a pas cette exigence : dire « non satisfaite »
    serait inventer un constat plutôt que signaler une absence de trace."""
    mission = {"steps": {"tprm": {"tiers": [{"name": "ESN", "score": 2.22}]}}}
    justification = _par_id(ct.etat(mission))["evaluation_fournisseurs"]["justification"]
    assert "Non tracé" in justification
    assert "volet GRC" in justification


def test_tous_les_tiers_doivent_etre_evalues():
    mission = {"steps": {"tprm": {"tiers": [
        {"name": "AWS", "exigences": [{"id": "NIST-ID.RA-10", "satisfait": True}]},
        {"name": "ESN", "exigences": [{"id": "NIST-ID.RA-10", "satisfait": False}]},
    ]}}}
    resultat = _par_id(ct.etat(mission))["evaluation_fournisseurs"]
    assert resultat["couverte"] is False
    assert "1 tiers évalué(s) avant acquisition sur 2" in resultat["justification"]


# --- Restitution dans le livrable ------------------------------------------

def test_le_livrable_cite_les_controles_rattaches():
    markdown = report_builder._controles_techniques_md(
        {"steps": {"diagnostic": {"vulnerabilities_active": True}}})
    assert "CIS v8 CIS 7" in markdown
    assert "NIST CSF 2.0 ID.RA-01" in markdown


def test_le_livrable_montre_les_pratiques_non_couvertes():
    markdown = report_builder._controles_techniques_md({})
    assert "Non couverte" in markdown


def test_le_livrable_renvoie_vers_la_phase_a_corriger():
    markdown = report_builder._controles_techniques_md({})
    assert "Phase 5 (Résilience & E3R)" in markdown


def test_le_livrable_donne_le_taux():
    markdown = report_builder._controles_techniques_md(
        {"steps": {"diagnostic": {"vulnerabilities_active": True}}})
    assert "1 pratique(s) couverte(s) sur 4 (25 %)" in markdown


@pytest.mark.parametrize("doc_type", ["audit_report"])
def test_le_rapport_d_audit_integre_la_section(doc_type):
    state = {"name": "M", "client": "ACME", "type": "grc",
             "steps": {"diagnostic": {"vulnerabilities_active": True}}}
    _, markdown = report_builder.build_document(state, "m1", doc_type)
    assert "Rattachement aux référentiels de contrôles" in markdown
    assert "CIS 7" in markdown
