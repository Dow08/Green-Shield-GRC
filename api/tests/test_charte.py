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

from modules import charte, report_builder  # noqa: E402


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


# --- En-tête ---------------------------------------------------------------

def test_l_entete_porte_la_marque_et_le_cabinet():
    html = charte.entete("RAPPORT", "Acme Corp", "29/07/2026", "acme")
    assert "GREEN SHIELD" in html
    assert "DP Cyber Consulting" in html


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
def test_chaque_livrable_porte_l_entete_et_le_pied(doc_type):
    _, contenu = report_builder.build_document(_mission(), "acme", doc_type)
    assert 'class="gs-entete"' in contenu
    assert 'class="gs-pied"' in contenu


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_chaque_livrable_porte_le_logo(doc_type):
    _, contenu = report_builder.build_document(_mission(), "acme", doc_type)
    assert "data:image/png;base64," in contenu


@pytest.mark.parametrize("doc_type", report_builder.TYPES_DOCUMENTS)
def test_chaque_livrable_porte_une_empreinte_sha256_reelle(doc_type):
    _, contenu = report_builder.build_document(_mission(), "acme", doc_type)
    assert re.search(r"<code>[0-9a-f]{64}</code>", contenu)


def test_l_empreinte_change_avec_les_donnees_de_la_mission():
    """L'empreinte doit attester du contenu, pas être décorative."""
    m1 = _mission()
    m2 = _mission()
    m2["client"] = "Autre Client"
    _, c1 = report_builder.build_document(m1, "acme", "audit_report")
    _, c2 = report_builder.build_document(m2, "acme", "audit_report")
    e1 = re.search(r"<code>([0-9a-f]{64})</code>", c1).group(1)
    e2 = re.search(r"<code>([0-9a-f]{64})</code>", c2).group(1)
    assert e1 != e2
