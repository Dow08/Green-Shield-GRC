"""Tests de la génération des livrables Markdown.

Devenus possibles par l'extraction hors de `projects.py` (29/07/2026) : le
module ne connaît plus ni HTTP ni disque, on peut donc vérifier directement
le contenu produit.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import report_builder  # noqa: E402


def mission() -> dict:
    return {
        "id": "acme", "name": "Mission Acme", "client": "Acme Corp",
        "steps": {
            "cadrage": {
                "scope": "SI de production", "framework_name": "ISO 27001",
                "nda_text": "TEXTE DU NDA NEGOCIE",
                "assets_metier": [{"id": "VM-01", "name": "Fichier Clients", "description": "d", "is_personal_data": True}],
                "assets_support": [{"id": "BS-01", "name": "Active Directory", "type": "Logiciel", "description": "d", "owner": "DSI"}],
            },
            "diagnostic": {
                "rgpd_register": [{"id": "RGPD-01", "name": "Paie", "purpose": "Salaires",
                                   "data_categories": "NIR", "retention": "5 ans"}],
                "aipd": {"treatment_description": "TRAITEMENT DECRIT", "necessity_eval": "NECESSITE",
                         "risks_eval": "RISQUES", "mitigation_measures": "MESURES"},
            },
            "ebios": {
                "redoute_events": [{"id": "ER-01", "event": "Rancongiciel", "gravity": 4, "impact": "Arret"}],
                "operational_scenarios": [{"id": "SC-01", "event": "Hameconnage", "gravity": 4,
                                           "likelihood": 3, "mitigation": "MFA"}],
            },
            "resilience": {
                "bcp_strategy": {"rto": "4 heures", "rpo": "1 heure", "backup_policy": "Immuable"},
                "e3r": {"endiguement": "ISOLER", "eviction": "KRBTGT",
                        "eradication": "NETTOYER", "reconstruction": "IAC"},
            },
            "evaluation": {"manual_controls": [
                {"id": "A.5.1", "title": "Politiques", "status": "CONFORME", "notes": "ok"}]},
        },
    }


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_chaque_type_de_document_produit_un_titre_et_du_contenu(doc_type):
    titre, contenu = report_builder.build_document(mission(), "acme", doc_type)
    assert titre.endswith(".md")
    assert len(contenu) > 200


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_le_nom_de_fichier_derive_de_l_identifiant_pas_du_client(doc_type):
    """Non-régression V-06 : le champ libre `client` ne doit jamais composer un
    nom de fichier."""
    etat = mission()
    etat["client"] = "../../evasion"
    titre, _ = report_builder.build_document(etat, "acme", doc_type)
    assert "acme" in titre
    assert ".." not in titre and "/" not in titre


def test_un_type_inconnu_leve_une_erreur_explicite():
    with pytest.raises(report_builder.TypeDocumentInconnu):
        report_builder.build_document(mission(), "acme", "type_invente")


# --- Contenu réellement repris de la mission -------------------------------

def test_le_nda_reprend_le_texte_negocie():
    _, contenu = report_builder.build_document(mission(), "acme", "nda")
    assert "TEXTE DU NDA NEGOCIE" in contenu


def test_le_nda_signale_un_texte_absent_plutot_que_de_l_inventer():
    etat = mission()
    etat["steps"]["cadrage"]["nda_text"] = ""
    _, contenu = report_builder.build_document(etat, "acme", "nda")
    assert "non rédigé" in contenu


def test_l_analyse_ebios_reprend_les_scenarios():
    _, contenu = report_builder.build_document(mission(), "acme", "ebios")
    assert "Hameconnage" in contenu


def test_le_document_pssi_pri_reprend_les_cibles_temporelles():
    _, contenu = report_builder.build_document(mission(), "acme", "pssi_pri")
    assert "4 heures" in contenu
    assert "ISOLER" in contenu


def test_l_aipd_reprend_les_quatre_volets_cnil():
    _, contenu = report_builder.build_document(mission(), "acme", "aipd")
    for attendu in ("TRAITEMENT DECRIT", "NECESSITE", "RISQUES", "MESURES"):
        assert attendu in contenu


def test_le_rapport_d_audit_reprend_les_controles_manuels():
    _, contenu = report_builder.build_document(mission(), "acme", "audit_report")
    assert "Politiques" in contenu
    # Libellé lisible, pas l'énumération interne : « NON_CONFORME » partait
    # tel quel chez le client avant la recette du 29/07/2026.
    assert "Conforme" in contenu
    assert "CONFORME" not in contenu


def test_le_tableau_des_controles_manuels_porte_le_referentiel_d_origine():
    """Multi-référentiel : une fois plusieurs listes de contrôles fusionnées,
    la colonne « Référentiel » est la seule façon de savoir de quel
    référentiel chaque contrôle vient."""
    etat = mission()
    etat["steps"]["evaluation"]["manual_controls"] = [
        {"id": "ISO-A.5", "title": "Politiques", "status": "CONFORME", "notes": "ok",
         "referentiel_id": "iso27001", "referentiel_name": "ISO/IEC 27001:2022"},
        {"id": "DORA-01", "title": "Gestion des risques TIC", "status": "A_VERIFIER", "notes": "",
         "referentiel_id": "dora", "referentiel_name": "DORA"},
    ]
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "Référentiel" in contenu
    assert "ISO/IEC 27001:2022" in contenu
    assert "DORA" in contenu


def test_une_preuve_multi_referentiel_apparait_sur_les_deux_controles_qu_elle_couvre():
    """L'intérêt de la bibliothèque de preuves (Lot E) : une preuve saisie une
    fois apparaît sur chaque contrôle qu'elle couvre, quel que soit le
    référentiel."""
    etat = mission()
    etat["steps"]["evaluation"]["manual_controls"] = [
        {"id": "ISO-A.5", "title": "Politiques", "status": "CONFORME", "notes": "",
         "referentiel_id": "iso27001", "referentiel_name": "ISO/IEC 27001:2022"},
        {"id": "DORA-ICT", "title": "Cadre de gestion des risques TIC", "status": "CONFORME", "notes": "",
         "referentiel_id": "dora", "referentiel_name": "DORA"},
    ]
    etat["steps"]["evaluation"]["preuves"] = [
        {"id": "PRV-01", "libelle": "PSSI signée par la Direction", "controles_lies": [
            {"referentiel_id": "iso27001", "control_id": "ISO-A.5"},
            {"referentiel_id": "dora", "control_id": "DORA-ICT"},
        ]},
    ]
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "Preuve(s) associée(s)" in contenu
    assert contenu.count("PSSI signée par la Direction") == 2


def test_un_controle_sans_preuve_liee_n_affiche_rien_dans_la_colonne():
    _, contenu = report_builder.build_document(mission(), "acme", "audit_report")
    assert "Preuve(s) associée(s)" in contenu


def test_le_rapport_d_audit_indique_l_absence_de_scan_technique():
    _, contenu = report_builder.build_document(mission(), "acme", "audit_report")
    assert "Aucun scan technique" in contenu


# --- Signature ------------------------------------------------------------

@pytest.mark.parametrize("doc_type", ["nda", "audit_report"])
def test_les_documents_signes_portent_une_vraie_empreinte_sha256(doc_type):
    """Non-régression V-05 : `hash()` Python n'est ni du SHA256 ni reproductible."""
    from modules import docx_export
    etat = mission()
    _, contenu = report_builder.build_document(etat, "acme", doc_type)
    empreinte = docx_export.data_fingerprint(etat)
    assert len(empreinte) == 64
    assert empreinte in contenu


def test_une_mission_vide_ne_fait_pas_planter_la_generation():
    for doc_type in report_builder.TYPES_DOCUMENTS:
        titre, contenu = report_builder.build_document({"id": "x"}, "x", doc_type)
        assert titre and contenu


# --- Charges consommées dans le rapport d'audit (reste de F19) -------------

def test_le_rapport_expose_les_charges_consommees():
    """L'indicateur « charges consommées vs budget » exigé par Hermes n'était
    visible que dans l'interface : le client ne le voyait jamais."""
    etat = mission()
    etat["socle"] = {
        "qualification": {"budget": "10 jours"},
        "temps": {"entrees": [
            {"phase": "cadrage", "minutes": 180},
            {"phase": "ebios", "minutes": 240},
        ]},
    }
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "Charges consommées" in contenu
    assert "3 h" in contenu           # cadrage
    assert "4 h" in contenu           # ebios
    assert "**7 h**" in contenu       # total
    assert "10 jours" in contenu      # budget vendu


def test_le_rapport_signale_l_absence_de_temps_saisi_sans_l_inventer():
    _, contenu = report_builder.build_document(mission(), "acme", "audit_report")
    assert "Aucun temps consommé" in contenu


def test_les_charges_ne_listent_que_les_phases_reellement_saisies():
    etat = mission()
    etat["socle"] = {"temps": {"entrees": [{"phase": "tprm", "minutes": 60}]}}
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    i = contenu.index("Charges consommées")
    section = contenu[i:i + 400]
    assert "Risques Tiers" in section
    assert "Résilience & E3R" not in section


def test_le_budget_est_omis_quand_il_n_est_pas_renseigne():
    etat = mission()
    etat["socle"] = {"temps": {"entrees": [{"phase": "autre", "minutes": 30}]}}
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "Budget vendu" not in contenu


@pytest.mark.parametrize("minutes,attendu", [(45, "45 min"), (120, "2 h"), (125, "2 h 05")])
def test_les_durees_du_rapport_suivent_le_meme_format_que_l_interface(minutes, attendu):
    assert report_builder._duree_lisible(minutes) == attendu


# --- Chapitre RGPD/AIPD du rapport Markdown (31/07/2026) --------------------
#
# Absent jusqu'ici : le rapport Markdown n'avait aucun chapitre RGPD, alors
# que les rendus Word et HTML en portent un (`_ch_aipd`/`_aipd_section`),
# décalant sa numérotation de chapitres par rapport aux deux autres formats.

def test_le_rapport_d_audit_porte_desormais_un_chapitre_rgpd():
    etat = mission()
    etat["steps"]["diagnostic"]["aipd_required"] = True
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "## 4. Protection des données personnelles" in contenu
    assert "TRAITEMENT DECRIT" in contenu
    assert "RGPD-01" in contenu


def test_le_rapport_d_audit_porte_le_registre_des_violations():
    etat = mission()
    etat["steps"]["diagnostic"]["violations"] = [
        {"id": "VIO-01", "date_constat": "2026-01-01", "nature": "Fuite de base",
         "notifiee_cnil": True, "date_notification_cnil": "2026-01-02", "personnes_informees": True},
    ]
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "4.1bis" in contenu
    assert "VIO-01" in contenu


def test_le_rapport_d_audit_sans_violation_l_indique_explicitement():
    _, contenu = report_builder.build_document(mission(), "acme", "audit_report")
    assert "Aucune violation de données n'a été constatée sur cette mission." in contenu


def test_la_numerotation_des_chapitres_du_rapport_est_alignee_sur_word_et_html():
    """Le chapitre AIPD (4) décale tout ce qui suit : Évaluation organisationnelle
    passe en 8 (après Résilience), Plan de traitement en 11 — comme dans
    `report_docx.CHAPITRES`/`report_html.CHAPITRES`."""
    _, contenu = report_builder.build_document(mission(), "acme", "audit_report")
    for titre in (
        "## 1. Synthèse à destination de la direction",
        "## 2. Cadrage de la mission",
        "## 3. Patrimoine évalué",
        "## 4. Protection des données personnelles",
        "## 5. Analyse de risque",
        "## 6. Écosystème et risques tiers",
        "## 7. Résilience et continuité",
        "## 8. Évaluation organisationnelle",
        "## 9. Évaluation technique des configurations",
        "## 10. Rattachement aux référentiels de contrôles",
        "## 11. Plan de traitement",
        "## 12. Charges consommées",
        "## 13. Réserves et limites",
        "## 14. Certifications et signatures d'audit",
    ):
        assert titre in contenu, f"chapitre manquant ou mal numéroté : {titre}"
