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
    assert "CONFORME" in contenu


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
