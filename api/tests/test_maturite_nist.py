"""Tests du radar de maturité NIST CSF (api/modules/maturite_nist.py).

Contrairement à la roue de rattachement (nist_csf_map.py), ce module ne
calcule rien : il restitue un jugement déclaré par le consultant. Ces tests
vérifient d'abord qu'il ne fabrique jamais un tier là où rien n'a été
déclaré.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import maturite_nist as mn  # noqa: E402


def _mission(maturite: dict | None = None, referentiels: list[str] | None = None) -> dict:
    return {
        "grc": {
            "referentiels_actifs": referentiels or ["iso27001"],
            "maturite_nist": maturite or {},
        },
    }


def _fonction(profil: dict, code: str) -> dict:
    return next(f for f in profil["fonctions"] if f["code"] == code)


# --- Structure --------------------------------------------------------------

def test_le_radar_a_toujours_les_six_fonctions_dans_l_ordre():
    profil = mn.radar(_mission())
    assert [f["code"] for f in profil["fonctions"]] == ["GV", "ID", "PR", "DE", "RS", "RC"]


def test_une_mission_sans_maturite_declaree_ne_fabrique_aucun_tier():
    profil = mn.radar(_mission())
    assert all(f["tier"] is None for f in profil["fonctions"])
    assert all(f["tier_nom"] is None for f in profil["fonctions"])
    assert profil["nb_evaluees"] == 0


def test_la_note_de_distinction_avec_la_roue_est_toujours_presente():
    profil = mn.radar(_mission())
    assert "rattachement de contrôles" in profil["note"] or "roue" in profil["note"]


# --- Tier déclaré -------------------------------------------------------------

def test_un_tier_declare_est_restitue_avec_son_nom_et_sa_description():
    profil = mn.radar(_mission({"PR": {"tier": 3, "justification": "PSSI en place."}}))
    pr = _fonction(profil, "PR")
    assert pr["tier"] == 3
    assert pr["tier_nom"] == "Repeatable"
    assert "formalisé" in pr["tier_description"]
    assert pr["justification"] == "PSSI en place."
    assert profil["nb_evaluees"] == 1


def test_chaque_tier_correspond_au_bon_nom_officiel():
    noms_attendus = {1: "Partial", 2: "Risk Informed", 3: "Repeatable", 4: "Adaptive"}
    for tier, nom in noms_attendus.items():
        profil = mn.radar(_mission({"GV": {"tier": tier, "justification": ""}}))
        assert _fonction(profil, "GV")["tier_nom"] == nom


def test_une_valeur_de_tier_hors_bareme_est_traitee_comme_non_evaluee():
    for valeur_corrompue in (0, 5, -1, "x", 3.5, None):
        profil = mn.radar(_mission({"DE": {"tier": valeur_corrompue, "justification": "bruit"}}))
        de = _fonction(profil, "DE")
        assert de["tier"] is None
        assert de["tier_nom"] is None


def test_la_justification_est_toujours_une_chaine_jamais_null():
    profil = mn.radar(_mission({"RC": {"tier": 2, "justification": None}}))
    assert _fonction(profil, "RC")["justification"] == ""


def test_le_radar_est_disponible_sans_que_nist_csf_soit_un_referentiel_actif():
    # Le CSF est un cadre agnostique de pilotage : la mission ISO 27001/DORA
    # de démo n'active pas nist_csf, mais doit quand même pouvoir porter un
    # radar de maturité.
    profil = mn.radar(_mission({"GV": {"tier": 3, "justification": ""}}, referentiels=["iso27001", "dora"]))
    assert _fonction(profil, "GV")["tier"] == 3


# --- Cohérence avec la démo ---------------------------------------------------

def test_la_demo_illustre_un_radar_de_maturite_partiel():
    from modules import demo_fixture
    profil = mn.radar(demo_fixture.construire("demo_green_shield"))
    evaluees = [f["code"] for f in profil["fonctions"] if f["tier"] is not None]
    # La démo doit montrer un état honnête : plusieurs fonctions évaluées,
    # mais pas les six — jamais une mission fictivement complète.
    assert 0 < len(evaluees) < 6
    assert profil["nb_evaluees"] == len(evaluees)
