"""Tests des utilitaires communs aux livrables (docx_export.py) et du calcul
de criticité des tiers.

La génération du rapport Word elle-même est testée dans test_report_docx.py
depuis le 31/07/2026 — ce module ne rend plus de document, il ne porte plus
que ce qui est réellement partagé entre les trois formats de sortie.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import docx_export  # noqa: E402
from modules.projects import _tprm_rate  # noqa: E402


# --- Valeur affichable, jamais inventée -------------------------------------

def test_une_valeur_absente_devient_explicitement_non_renseignee():
    assert docx_export._txt(None) == docx_export.NON_RENSEIGNE
    assert docx_export._txt("") == docx_export.NON_RENSEIGNE
    assert docx_export._txt("   ") == docx_export.NON_RENSEIGNE


def test_une_valeur_presente_traverse_telle_quelle():
    assert docx_export._txt("Fichier clients") == "Fichier clients"
    assert docx_export._txt(0) == "0"  # une valeur falsy reste une valeur


def test_les_statuts_de_controle_ont_un_libelle_lisible():
    assert docx_export.STATUS_LABELS["NON_CONFORME"] == "Non conforme"
    assert docx_export.STATUS_LABELS["A_VERIFIER"] == "À vérifier"


# --- Empreinte d'intégrité ---------------------------------------------------

def test_empreinte_stable_et_sensible_au_contenu():
    mission = {"id": "acme", "name": "Audit ISO 27001", "client": "ACME"}
    empreinte = docx_export.data_fingerprint(mission)
    assert empreinte == docx_export.data_fingerprint(mission)
    assert len(empreinte) == 64
    mission["client"] = "AUTRE"
    assert docx_export.data_fingerprint(mission) != empreinte


# --- Mention de réserve ------------------------------------------------------

def test_mention_de_reserve_datee_et_nominative():
    """La réserve délimite la responsabilité : elle doit citer le client et la date."""
    texte = docx_export.mention_reserve("29/07/2026", "ACME")
    assert "ACME" in texte
    assert "29/07/2026" in texte
    assert "ne saurait" in texte and "garantie" in texte


# --- Criticité des tiers ----------------------------------------------------

@pytest.mark.parametrize("criteres,score,rating", [
    ((5, 5, 4, 4), 1.56, "Moyen"),
    ((4, 5, 3, 3), 2.22, "Élevé"),
    ((2, 1, 2, 4), 0.25, "Faible"),
    ((4, 4, 4, 4), 1.0, "Moyen"),
])
def test_criticite_tiers_derivee_des_criteres(criteres, score, rating):
    """La criticité reste dérivée des quatre curseurs, jamais saisie à la main.

    Les valeurs attendues sont celles du ratio ANSSI (§14.1bis) depuis le
    29/07/2026 ; la moyenne arithmétique qu'elles remplacent est couverte, avec
    sa justification, dans test_tprm.py.
    """
    resultat = _tprm_rate(*criteres)
    assert resultat["score"] == score
    assert resultat["rating"] == rating


def test_le_serveur_est_seul_a_noter_un_tiers():
    """Le frontend possédait sa propre copie de la formule et recalculait le
    score à l'édition d'un tiers. Les deux ont divergé au passage au ratio
    ANSSI ; la notation est désormais exclusivement serveur."""
    phase = Path(__file__).resolve().parents[2] / "web" / "src" / "components" / "phases" / "PhaseTprm.tsx"
    source = phase.read_text(encoding="utf-8")
    # Affectation, pas comparaison : `t.rating === "Critique"` reste légitime,
    # c'est de l'affichage. `rating = ...` serait un second calcul.
    affectation = re.search(r"\b(score|rating)\s*=\s*[^=]", source)
    assert affectation is None, f"le frontend s'est remis à noter les tiers : {affectation.group(0)!r}"
