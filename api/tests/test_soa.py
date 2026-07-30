"""Tests de la Déclaration d'Applicabilité (SoA) — api/modules/soa.py.

Manque identifié en revue GRC senior le 30/07/2026 : sans SoA, une mission
ISO 27001 ne peut pas passer un audit de certification (clause 6.1.3 d).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import soa  # noqa: E402


def test_le_catalogue_porte_les_93_controles_de_l_annexe_a():
    assert len(soa.catalogue()) == 93


def test_le_catalogue_n_a_aucun_texte_normatif_recopie():
    """F3 : identifiants et intitulés courts reformulés seulement, jamais le
    texte de la norme ISO/AFNOR."""
    for c in soa.catalogue():
        assert len(c["titre"]) < 100
        assert c["theme"] in soa.THEMES
        assert c["code"].startswith("A.")


def test_entrees_par_defaut_ne_presume_aucune_decision():
    """Zéro invention : `applicable` démarre à `None`, jamais `True` — un
    consultant qui n'a pas encore tranché ne doit jamais voir 93 décisions
    qu'il n'a pas prises s'afficher comme actées."""
    entrees = soa.entrees_par_defaut()
    assert len(entrees) == 93
    assert all(e["applicable"] is None for e in entrees)
    assert all(e["statut"] is None for e in entrees)
    assert all(e["justification"] == "" for e in entrees)


def test_etat_compte_les_controles_statues():
    entrees = soa.entrees_par_defaut()
    entrees[0]["applicable"] = True
    entrees[1]["applicable"] = False
    resultat = soa.etat(entrees)
    assert resultat["total"] == 93
    assert resultat["statues"] == 2
    assert resultat["non_statues"] == 91
    assert resultat["applicables"] == 1
    assert resultat["exclus"] == 1
    assert resultat["complete"] is False


def test_etat_complete_quand_tout_est_statue():
    entrees = [{"code": "A.5.1", "theme": "Organisationnel", "applicable": True}]
    resultat = soa.etat(entrees)
    assert resultat["complete"] is True
    assert resultat["taux"] == 100


def test_par_theme_couvre_les_quatre_themes_sans_perte():
    entrees = soa.entrees_par_defaut()
    resume = soa.par_theme(entrees)
    assert {r["theme"] for r in resume} == set(soa.THEMES)
    assert sum(r["total"] for r in resume) == 93
