"""Tests des 4 exports HTML complémentaires au rapport de mission (M2-M5).

Contexte : les maquettes M1-M5 avaient été validées le 29/07/2026, mais seul M1
avait été branché à des données réelles le 30/07/2026 (`report_html.py`,
`build_report`). Ces tests couvrent les trois autres — synthèse direction
(M2), tableau de restitution (M3), registre de conformité (M4) et
cartographie du risque (M5) — sur le même principe que M1 : zéro invention,
séparation stricte des volets (§14.1bis), aucun tuyau Markdown brut.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import report_html  # noqa: E402


def _mission(volet: str = "consulting") -> dict:
    return {
        "id": "acme", "name": "Mission", "client": "Acme Corp", "type": volet,
        "progress": 60,
        "steps": {
            "cadrage": {"assets_metier": [{"id": "VM-01", "name": "Fichier clients"}],
                       "assets_support": [{"id": "BS-01", "name": "AD"}]},
            "ebios": {
                "redoute_events": [{"id": "ER-01", "event": "Fuite", "gravity": 4, "impact": "Grave"}],
                "operational_scenarios": [{"id": "SO-01", "event": "Hameçonnage", "gravity": 4,
                                           "likelihood": 3, "mitigation": "MFA"}],
            },
            "tprm": {"tiers": [
                {"name": "Prestataire", "dependence": 5, "penetration": 5, "maturity": 2, "trust": 3,
                 "score": 4.17, "rating": "Critique", "methode": "ratio_anssi",
                 "exigences": [{"id": "DORA-30", "libelle": "Clauses", "satisfait": False}]},
            ]},
            "evaluation": {"manual_controls": [
                {"id": "A.7", "title": "RH", "status": "NON_CONFORME", "notes": "14 comptes actifs"},
            ]},
            "traitement": {"remediations": [
                {"id": "REM-01", "axe": "Protection", "priority": "Critique", "measure": "Segmenter"},
                {"id": "REM-02", "axe": "Défense", "priority": "Moyen", "measure": "Centraliser"},
            ]},
            "restitution": {"exec_summary": "Deux écarts majeurs à traiter en priorité."},
        },
        "socle": {"entretiens": [{"id": "ENT-01", "role": "RSSI", "date": "2026-06-05",
                                  "synthese": "Confirme l'absence de segmentation."}],
                  "qualification": {"budget": "18 jours"},
                  "temps": {"entrees": [{"phase": "cadrage", "minutes": 120}]}},
    }


# --- M2 — Synthèse direction -------------------------------------------------

def test_m2_est_un_document_autonome():
    _, html = report_html.build_synthese(_mission(), "acme")
    assert html.startswith("<!doctype html>")
    assert "http://" not in html and "https://" not in html


def test_m2_reprend_la_synthese_saisie_par_le_consultant():
    """Jamais de texte inventé : la synthèse vient du champ `exec_summary`."""
    _, html = report_html.build_synthese(_mission(), "acme")
    assert "Deux écarts majeurs à traiter en priorité." in html


def test_m2_annonce_l_absence_de_synthese_plutot_que_d_en_inventer_une():
    mission = _mission()
    mission["steps"]["restitution"]["exec_summary"] = ""
    _, html = report_html.build_synthese(mission, "acme")
    assert 'class="vide"' in html


def test_m2_affiche_la_jauge_d_avancement_reelle():
    mission = _mission()
    mission["progress"] = 73
    _, html = report_html.build_synthese(mission, "acme")
    assert "73 %" in html


def test_m2_liste_les_ecarts_prioritaires_par_priorite():
    _, html = report_html.build_synthese(_mission(), "acme")
    i_crit, i_moy = html.index("REM-01"), html.index("REM-02")
    assert i_crit < i_moy, "la mesure Critique doit précéder la Moyenne"


def test_m2_ne_contient_aucun_tuyau_markdown():
    _, html = report_html.build_synthese(_mission(), "acme")
    assert "| :---" not in html


def test_m2_porte_le_logo_et_l_empreinte():
    _, html = report_html.build_synthese(_mission(), "acme")
    assert "data:image/png;base64," in html
    assert "<code>" in html


# --- M3 — Tableau de restitution ---------------------------------------------

def test_m3_est_un_document_autonome_sans_tuyau():
    _, html = report_html.build_tableau_restitution(_mission(), "acme")
    assert html.startswith("<!doctype html>")
    assert "| :---" not in html


def test_m3_colonne_diagnostique_reprend_evenements_et_scenarios():
    _, html = report_html.build_tableau_restitution(_mission(), "acme")
    assert "ER-01" in html and "SO-01" in html


def test_m3_colonne_a_faire_reprend_le_plan_de_traitement():
    _, html = report_html.build_tableau_restitution(_mission(), "acme")
    assert "REM-01" in html and "Segmenter" in html


def test_m3_signale_le_tiers_critique_sur_le_volet_consulting():
    _, html = report_html.build_tableau_restitution(_mission("consulting"), "acme")
    assert "Prestataire" in html and "Critique" in html


def test_m3_signale_l_ecart_organisationnel_sur_le_volet_grc():
    """Sur GRC, la colonne diagnostiquée doit citer l'écart ISO, pas le tiers noté."""
    _, html = report_html.build_tableau_restitution(_mission("grc"), "acme")
    assert "A.7" in html


def test_m3_affiche_le_taux_de_rattachement_reel():
    _, html = report_html.build_tableau_restitution(_mission(), "acme")
    assert "%." in html  # phrase « N pratique(s) couverte(s) sur M — X %. »


def test_m3_annonce_une_colonne_vide_plutot_que_de_l_inventer():
    mission = _mission()
    mission["steps"]["traitement"]["remediations"] = []
    _, html = report_html.build_tableau_restitution(mission, "acme")
    assert 'class="vide"' in html


# --- M4 — Registre de conformité ---------------------------------------------

def test_m4_est_un_document_autonome_sans_tuyau():
    _, html = report_html.build_registre_conformite(_mission(), "acme")
    assert html.startswith("<!doctype html>")
    assert "| :---" not in html


def test_m4_reprend_les_exigences_organisationnelles_avec_libelle_lisible():
    _, html = report_html.build_registre_conformite(_mission(), "acme")
    assert "Non conforme" in html
    assert "NON_CONFORME" not in html


def test_m4_reprend_le_registre_des_tiers_selon_le_volet():
    _, html_grc = report_html.build_registre_conformite(_mission("grc"), "acme")
    assert "Écarts restants" in html_grc  # colonne du tableau volet GRC (exigences)
    _, html_conseil = report_html.build_registre_conformite(_mission("consulting"), "acme")
    assert ">Ratio</th>" in html_conseil  # volet Conseil : classement par ratio


def test_m4_ne_montre_aucun_score_de_risque_sur_le_registre_grc():
    """§14.1bis : le registre de conformité GRC reste un registre, pas un scoring."""
    mission = _mission("grc")
    mission["steps"]["tprm"]["tiers"][0].pop("score", None)
    mission["steps"]["tprm"]["tiers"][0].pop("rating", None)
    _, html = report_html.build_registre_conformite(mission, "acme")
    assert ">Ratio</th>" not in html


def test_m4_reprend_le_plan_de_remediation_trie():
    _, html = report_html.build_registre_conformite(_mission(), "acme")
    assert html.index("REM-01") < html.index("REM-02")


# --- M5 — Cartographie du risque ---------------------------------------------

def test_m5_est_un_document_autonome_sans_tuyau():
    _, html = report_html.build_cartographie_risque(_mission(), "acme")
    assert html.startswith("<!doctype html>")
    assert "| :---" not in html


def test_m5_place_le_scenario_dans_la_bonne_case_de_la_matrice():
    """Reprend exactement les seuils déjà utilisés en Phase 4 de l'application
    (web/src/components/phases/PhaseEbios.tsx) : gravité 4 × vraisemblance 3
    = 12 → zone la plus soutenue."""
    _, html = report_html.build_cartographie_risque(_mission(), "acme")
    assert '<span class="jeton">SO-01</span>' in html
    assert 'background:rgba(255,111,145,.22)' in html


def test_m5_classe_les_tiers_par_ratio_anssi_sur_le_volet_consulting():
    _, html = report_html.build_cartographie_risque(_mission("consulting"), "acme")
    assert "formule ANSSI" in html
    assert "4.17" in html


def test_m5_classe_les_tiers_par_conformite_sur_le_volet_grc_sans_score():
    _, html = report_html.build_cartographie_risque(_mission("grc"), "acme")
    assert "aucun score de risque" in html
    assert "4.17" not in html  # le ratio ne doit pas fuiter sur ce volet


def test_m5_annonce_l_absence_de_scenario_plutot_que_d_inventer_une_matrice():
    mission = _mission()
    mission["steps"]["ebios"]["operational_scenarios"] = []
    _, html = report_html.build_cartographie_risque(mission, "acme")
    assert 'class="vide"' in html


def test_m5_reprend_les_evenements_redoutes():
    _, html = report_html.build_cartographie_risque(_mission(), "acme")
    assert "ER-01" in html and "Fuite" in html


# --- Échappement des données de mission -------------------------------------

@pytest.mark.parametrize("build", [
    report_html.build_synthese, report_html.build_tableau_restitution,
    report_html.build_registre_conformite, report_html.build_cartographie_risque,
])
def test_les_quatre_exports_echappent_les_donnees_de_mission(build):
    mission = _mission()
    mission["client"] = "<script>alert(1)</script> & Fils"
    _, html = build(mission, "acme") if build in (
        report_html.build_synthese, report_html.build_registre_conformite,
    ) else build(mission, "acme")
    assert "<script>alert(1)</script>" not in html
    assert "&amp; Fils" in html


@pytest.mark.parametrize("build", [
    report_html.build_synthese, report_html.build_tableau_restitution,
    report_html.build_registre_conformite, report_html.build_cartographie_risque,
])
def test_les_quatre_exports_rendent_les_deux_volets_sans_exception(build):
    for volet in ("consulting", "grc"):
        _, html = build(_mission(volet), "acme")
        assert len(html) > 500
