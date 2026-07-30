"""Tests de l'identité visuelle des livrables (api/modules/charte.py).

Un livrable part chez un client : il doit porter la marque, la mention de
confidentialité et l'empreinte d'intégrité — et rester lisible hors ligne.
"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import charte, report_builder, report_html  # noqa: E402


# --- Logo embarqué ---------------------------------------------------------

def test_le_logo_est_un_png_valide():
    b64 = charte.LOGO_DATA_URI.split("base64,", 1)[1]
    donnees = base64.b64decode(b64)
    assert donnees[:8] == b"\x89PNG\r\n\x1a\n"


def test_le_logo_reste_leger():
    """Il est dupliqué dans chaque livrable : au-delà de ~30 ko l'export
    deviendrait inutilement lourd."""
    assert len(charte.LOGO_DATA_URI) < 30_000


def test_le_logo_est_embarque_et_non_reference():
    """Un livrable doit rester lisible hors ligne et après transmission :
    aucune dépendance à un fichier joint ni à un serveur d'images."""
    assert charte.LOGO_DATA_URI.startswith("data:image/png;base64,")
    assert "http" not in charte.LOGO_DATA_URI


# --- Logo personnalisé du cabinet (30/07/2026) -------------------------------
#
# Ajouté à la suite du retour utilisateur sur l'identité écrite en dur : nom
# et cabinet sont personnalisables, mais le logo restait celui de GREEN
# SHIELD quoi qu'il arrive. Le défaut (logo GREEN SHIELD) reste inchangé ;
# un logo de cabinet valide, déposé dans Réglages, vient le remplacer.

# PNG 1x1 minimal, valide — assez pour vérifier le chemin "logo personnalisé
# accepté" sans dépendre d'un fichier binaire dans le dépôt.
_LOGO_PERSONNALISE_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY"
    "42YAAAAASUVORK5CYII="
)


def test_logo_bytes_retombe_sur_le_defaut_si_aucun_logo_fourni():
    assert charte.logo_bytes("") == base64.b64decode(charte.LOGO_BASE64)


def test_logo_bytes_accepte_un_png_personnalise_valide():
    donnees = charte.logo_bytes(_LOGO_PERSONNALISE_PNG)
    assert donnees == base64.b64decode(_LOGO_PERSONNALISE_PNG)
    assert donnees != base64.b64decode(charte.LOGO_BASE64)


def test_logo_bytes_retombe_sur_le_defaut_si_donnees_invalides():
    """Ne doit jamais faire planter la génération d'un rapport : un logo
    corrompu ou dans un format non pris en charge retombe silencieusement
    sur le logo GREEN SHIELD, plutôt que de lever une exception."""
    assert charte.logo_bytes("ceci n'est pas du base64 valide !!!") == base64.b64decode(charte.LOGO_BASE64)
    assert charte.logo_bytes(base64.b64encode(b"pas une image").decode()) == base64.b64decode(charte.LOGO_BASE64)


def test_logo_data_uri_reflete_le_meme_comportement():
    assert charte.logo_data_uri("") == charte.LOGO_DATA_URI
    assert charte.logo_data_uri(_LOGO_PERSONNALISE_PNG) == f"data:image/png;base64,{_LOGO_PERSONNALISE_PNG}"
    assert charte.logo_data_uri("invalide") == charte.LOGO_DATA_URI


# --- En-tête ---------------------------------------------------------------

def test_l_entete_porte_la_marque_et_le_cabinet():
    html = charte.entete("RAPPORT", "Acme Corp", "29/07/2026", "acme", cabinet="Cabinet Test")
    assert "GREEN SHIELD" in html
    assert "Cabinet Test" in html


def test_l_entete_signale_l_absence_de_cabinet_configure():
    """L'application sert n'importe quel consultant : sans cabinet saisi dans
    Réglages, elle ne doit jamais retomber sur un nom écrit en dur (retour
    utilisateur du 30/07/2026)."""
    html = charte.entete("RAPPORT", "Acme Corp", "29/07/2026", "acme")
    assert "DP Cyber Consulting" not in html
    assert "Cabinet non renseigné" in html


def test_l_entete_reprend_le_document_le_client_et_la_reference():
    html = charte.entete("AIPD / PIA (RGPD)", "Acme Corp", "29/07/2026", "acme")
    assert "AIPD / PIA (RGPD)" in html
    assert "Acme Corp" in html
    assert "29/07/2026" in html
    assert "acme" in html


def test_l_entete_affiche_la_mention_de_confidentialite():
    html = charte.entete("RAPPORT", "Acme", "29/07/2026", "acme")
    assert "gs-confidentiel" in html
    assert "confidentiel" in html.lower()


def test_l_entete_embarque_la_feuille_de_style_d_impression():
    html = charte.entete("RAPPORT", "Acme", "29/07/2026", "acme")
    assert "@media print" in html


# --- Pied de page ----------------------------------------------------------

def test_le_pied_porte_l_empreinte_d_integrite():
    html = charte.pied("a" * 64)
    assert "a" * 64 in html
    assert "SHA-256" in html


def test_le_pied_rappelle_la_restriction_de_diffusion():
    assert "ne pas diffuser" in charte.pied("x" * 64).lower()


# --- Application aux livrables réels ---------------------------------------

def _mission() -> dict:
    return {"id": "acme", "name": "M", "client": "Acme Corp", "steps": {}}


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_chaque_livrable_markdown_porte_la_marque_et_la_confidentialite(doc_type):
    """Depuis le 30/07/2026, un livrable Markdown ne contient **que** du Markdown.

    L'en-tête HTML + CSS et le logo en `data:` URI qu'il embarquait ne rendaient
    correctement nulle part : GitHub retire les styles et bloque les images
    `data:`, un navigateur affiche les tableaux Markdown en texte brut. La marque
    et la mention de confidentialité restent présentes, en Markdown.
    """
    _, contenu = report_builder.build_document(_mission(), "acme", doc_type, cabinet="Cabinet Test")
    assert "GREEN SHIELD" in contenu
    assert "Cabinet Test" in contenu
    assert "confidentiel" in contenu.lower()


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_aucun_livrable_markdown_ne_retombe_sur_un_nom_ecrit_en_dur(doc_type):
    """Régression du 30/07/2026 : NDA et PSSI affichaient « Dorian » /
    « DP Cyber Consulting » quels que soient l'auditeur et le cabinet réels
    saisis dans Réglages — l'application doit servir n'importe quel
    consultant, jamais un seul."""
    _, sans_identite = report_builder.build_document(_mission(), "acme", doc_type)
    assert "Dorian" not in sans_identite
    assert "DP Cyber Consulting" not in sans_identite

    _, avec_identite = report_builder.build_document(
        _mission(), "acme", doc_type, auditeur="Camille Martin", cabinet="Martin Cyber Audit")
    assert "Martin Cyber Audit" in avec_identite
    if doc_type != "aipd":
        # L'AIPD ne nomme que des rôles (DPO, Responsable du Traitement),
        # jamais l'auditeur — à l'identique de sa version Markdown d'origine.
        assert "Camille Martin" in avec_identite


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_aucun_livrable_markdown_n_embarque_de_html_ni_de_css(doc_type):
    """Régression : c'est ce mélange qui rendait les livrables illisibles."""
    _, contenu = report_builder.build_document(_mission(), "acme", doc_type)
    for interdit in ("<style>", "<div", "data:image/png;base64,", "@media print"):
        assert interdit not in contenu, f"{interdit} réapparu dans l'export Markdown"


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_chaque_livrable_markdown_porte_une_empreinte_sha256_reelle(doc_type):
    _, contenu = report_builder.build_document(_mission(), "acme", doc_type)
    assert re.search(r"`[0-9a-f]{64}`", contenu)


def test_l_empreinte_change_avec_les_donnees_de_la_mission():
    """L'empreinte doit attester du contenu, pas être décorative."""
    m2 = _mission()
    m2["client"] = "Autre Client"
    _, c1 = report_builder.build_document(_mission(), "acme", "audit_report")
    _, c2 = report_builder.build_document(m2, "acme", "audit_report")
    e1 = re.search(r"`([0-9a-f]{64})`", c1).group(1)
    e2 = re.search(r"`([0-9a-f]{64})`", c2).group(1)
    assert e1 != e2


# --- Le rapport HTML : c'est lui qui porte la mise en page ------------------

def test_le_rapport_html_est_un_document_autonome():
    """Aucune ressource externe : le projet doit rester utilisable hors ligne."""
    _, html = report_html.build_report(_mission(), "acme", "Dorian", "DP Cyber")
    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    assert "http://" not in html and "https://" not in html


def test_le_rapport_html_porte_le_logo_embarque():
    _, html = report_html.build_report(_mission(), "acme")
    assert "data:image/png;base64," in html


# --- Logo personnalisé étendu aux exports HTML (30/07/2026) -----------------

_LOGO_PERSONNALISE_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY"
    "42YAAAAASUVORK5CYII="
)


def test_le_rapport_html_utilise_le_logo_personnalise_s_il_est_fourni():
    _, sans_logo = report_html.build_report(_mission(), "acme")
    assert charte.LOGO_BASE64 in sans_logo
    assert _LOGO_PERSONNALISE_PNG not in sans_logo

    _, avec_logo = report_html.build_report(_mission(), "acme", logo=_LOGO_PERSONNALISE_PNG)
    assert _LOGO_PERSONNALISE_PNG in avec_logo
    assert f"data:image/png;base64,{_LOGO_PERSONNALISE_PNG}" in avec_logo


@pytest.mark.parametrize("builder", [
    report_html.build_synthese,
    report_html.build_registre_conformite,
])
def test_les_vues_courtes_html_utilisent_aussi_le_logo_personnalise(builder):
    """M2 (synthèse) et M4 (registre) ont leur propre en-tête compact
    (`_entete_court`), distinct de la page de garde de M1 — vérifié
    séparément pour ne pas supposer qu'ils partagent le même chemin de code."""
    _, html = builder(_mission(), "acme", logo=_LOGO_PERSONNALISE_PNG)
    assert _LOGO_PERSONNALISE_PNG in html


def test_le_rapport_html_rend_de_vrais_tableaux():
    """Le défaut d'origine : les tableaux Markdown sortaient en texte brut,
    tuyaux et lignes de séparation compris."""
    mission = _mission()
    mission["steps"] = {"cadrage": {"assets_metier": [
        {"id": "VM-01", "name": "Fichier clients", "description": "d", "is_personal_data": True}]}}
    _, html = report_html.build_report(mission, "acme")
    assert "<table>" in html and "<td>VM-01</td>" in html
    assert "| :---" not in html


def test_le_rapport_html_est_imprimable_en_a4():
    _, html = report_html.build_report(_mission(), "acme")
    assert "@page" in html and "A4" in html


def test_le_rapport_html_echappe_les_donnees_de_mission():
    """Un nom de client contenant du HTML ne doit pas casser le document."""
    mission = _mission()
    mission["client"] = '<script>alert(1)</script> & Fils'
    _, html = report_html.build_report(mission, "acme")
    assert "<script>alert(1)</script>" not in html
    assert "&amp; Fils" in html


def test_le_rapport_html_annonce_les_sections_sans_donnee():
    """Une section vide est dite vide, jamais comblée par une valeur plausible."""
    _, html = report_html.build_report(_mission(), "acme")
    assert 'class="vide"' in html


def test_le_titre_du_rapport_html_suit_le_volet():
    conseil = _mission()
    grc = dict(_mission(), type="grc")
    _, h_conseil = report_html.build_report(conseil, "acme")
    _, h_grc = report_html.build_report(grc, "acme")
    assert "analyse de risque" in h_conseil
    assert "conformité" in h_grc


def test_le_rapport_html_grc_ne_montre_aucun_score_de_risque():
    """§14.1bis : ni DORA ni NIS2 ne se réclament d'EBIOS RM."""
    grc = dict(_mission(), type="grc")
    grc["steps"] = {"tprm": {"tiers": [
        {"name": "Éditeur", "exigences": [{"id": "DORA-30", "libelle": "Clauses", "satisfait": False}]}]}}
    _, html = report_html.build_report(grc, "acme")
    assert "<th>Ratio</th>" not in html
    assert "aucun score de risque" in html
