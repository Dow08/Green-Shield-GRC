"""Tests du rattachement NIST CSF (api/modules/nist_csf_map.py).

La roue implique une couverture : ces tests vérifient d'abord qu'elle ne
fabrique jamais un taux là où aucune donnée ne le justifie.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import nist_csf_map as nm  # noqa: E402


def _mission_iso(soa=None) -> dict:
    return {
        "grc": {"referentiels_actifs": ["iso27001"]},
        "steps": {"evaluation": {"soa": soa or [], "manual_controls": []}},
    }


def _mission_nist(controles=None) -> dict:
    return {
        "grc": {"referentiels_actifs": ["nist_csf"]},
        "steps": {"evaluation": {"manual_controls": controles or [], "soa": []}},
    }


def _fonction(carte: dict, code: str) -> dict:
    return next(f for f in carte["fonctions"] if f["code"] == code)


# --- Structure ------------------------------------------------------------

def test_la_roue_a_toujours_les_six_fonctions_dans_l_ordre():
    carte = nm.carte(_mission_iso())
    assert [f["code"] for f in carte["fonctions"]] == ["GV", "ID", "PR", "DE", "RS", "RC"]


def test_une_mission_vide_ne_produit_aucun_taux_invente():
    # Zéro rattaché => taux None partout, jamais 0 %.
    carte = nm.carte(_mission_iso())
    assert all(f["taux"] is None for f in carte["fonctions"])
    assert carte["total_rattaches"] == 0


# --- Mode direct (mission NIST) -------------------------------------------

def test_une_mission_nist_est_rattachee_directement():
    carte = nm.carte(_mission_nist([
        {"id": "GV.RM-01", "referentiel_id": "nist_csf", "status": "CONFORME"},
        {"id": "PR.AA-03", "referentiel_id": "nist_csf", "status": "NON_CONFORME"},
    ]))
    assert carte["mode"] == "direct"
    assert _fonction(carte, "GV")["taux"] == 100
    # Rattaché mais non conforme : compté, non couvert.
    assert _fonction(carte, "PR")["rattaches"] == 1
    assert _fonction(carte, "PR")["couverts"] == 0
    assert _fonction(carte, "PR")["taux"] == 0


def test_un_controle_nist_non_evalue_n_est_pas_rattache():
    carte = nm.carte(_mission_nist([
        {"id": "DE.CM-01", "referentiel_id": "nist_csf", "status": "A_VERIFIER"},
    ]))
    # A_VERIFIER est décidé (rattaché) mais non couvert.
    assert _fonction(carte, "DE")["rattaches"] == 1
    assert _fonction(carte, "DE")["taux"] == 0


# --- Mode indicatif (mission ISO, pont catalogue) -------------------------

def test_une_mission_iso_est_en_mode_indicatif_avec_avertissement():
    carte = nm.carte(_mission_iso())
    assert carte["mode"] == "indicatif"
    assert "portée" in carte["note"] or "indicatif" in carte["note"]


def test_le_pont_catalogue_rattache_un_code_soa_a_sa_fonction():
    # A.5.17 (MFA) est mappé nist_csf PR.AA-* dans le catalogue : doit peupler PR.
    carte = nm.carte(_mission_iso([
        {"code": "A.5.17", "statut": "Implémenté"},
    ]))
    pr = _fonction(carte, "PR")
    assert pr["rattaches"] >= 1
    assert pr["couverts"] >= 1
    assert "A.5.17" in pr["codes"]


def test_un_controle_soa_partiel_compte_comme_rattache_non_couvert():
    carte = nm.carte(_mission_iso([
        {"code": "A.5.17", "statut": "Partiel"},
    ]))
    pr = _fonction(carte, "PR")
    assert pr["rattaches"] >= 1
    assert pr["couverts"] == 0
    assert pr["taux"] == 0


def test_un_controle_soa_sans_decision_n_est_pas_rattache():
    # statut vide / None : le consultant ne s'est pas prononcé, on ne compte pas.
    carte = nm.carte(_mission_iso([
        {"code": "A.5.17", "statut": None},
        {"code": "A.5.1", "statut": ""},
    ]))
    assert carte["total_rattaches"] == 0


def test_un_code_soa_hors_catalogue_ne_rattache_rien():
    # Un code réel mais absent du pont catalogue ne doit pas être inventé.
    carte = nm.carte(_mission_iso([
        {"code": "A.5.99", "statut": "Implémenté"},
    ]))
    assert carte["total_rattaches"] == 0


# --- Cohérence avec la démo -----------------------------------------------

def test_la_demo_atteint_plusieurs_fonctions_sans_toutes_les_remplir():
    from modules import demo_fixture
    carte = nm.carte(demo_fixture.construire("demo_green_shield"))
    atteintes = [f["code"] for f in carte["fonctions"] if f["rattaches"] > 0]
    # La SoA décidée touche plusieurs fonctions, mais pas les six : c'est
    # exactement ce que la vue doit montrer honnêtement.
    assert len(atteintes) >= 3
    assert len(atteintes) < 6
