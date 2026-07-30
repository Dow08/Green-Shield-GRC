"""Criticité des tiers scindée par volet (§14.1bis).

Le spec tranche deux choses : la moyenne arithmétique est remplacée par le
ratio ANSSI sur le volet Consulting, et le volet GRC n'a **pas** de score du
tout. Ces tests verrouillent la justification chiffrée du spec — c'est elle qui
fonde la décision, pas la formule prise isolément.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import schema_migration, tprm  # noqa: E402


# --- La formule -------------------------------------------------------------

def test_le_ratio_rapporte_l_exposition_a_la_fiabilite():
    # (5 × 5) / (4 × 4) = 1,5625
    assert tprm.ratio_anssi(5, 5, 4, 4)["score"] == 1.56


def test_une_maturite_et_une_confiance_nulles_ne_divisent_pas_par_zero():
    """Les curseurs vont de 1 à 5 dans l'interface, mais une mission importée
    ou migrée peut porter 0 : le dénominateur est plancher à 1."""
    assert tprm.ratio_anssi(4, 4, 0, 0)["score"] == 16.0


def test_les_bandes_couvrent_tout_le_domaine():
    assert tprm.ratio_anssi(5, 5, 1, 1)["rating"] == "Critique"   # 25.0
    assert tprm.ratio_anssi(4, 5, 3, 3)["rating"] == "Élevé"      # 2.22
    assert tprm.ratio_anssi(5, 5, 4, 4)["rating"] == "Moyen"      # 1.56
    assert tprm.ratio_anssi(1, 1, 5, 5)["rating"] == "Faible"     # 0.04


def test_un_ratio_exactement_sur_un_seuil_prend_la_bande_haute():
    assert tprm.ratio_anssi(2, 2, 2, 1)["rating"] == "Élevé"      # exactement 2.0
    assert tprm.ratio_anssi(1, 1, 1, 1)["rating"] == "Moyen"      # exactement 1.0


def test_le_tiers_porte_la_methode_qui_l_a_note():
    """Sans cette trace, impossible de distinguer une note ANSSI d'une note
    héritée, donc impossible de proposer un recalcul ciblé."""
    assert tprm.ratio_anssi(3, 3, 3, 3)["methode"] == tprm.METHODE_ANSSI


# --- La justification chiffrée du spec --------------------------------------

def test_le_ratio_separe_deux_tiers_que_la_moyenne_confondait():
    """Le cœur de la décision §14.1bis, sur les tiers pré-remplis réels.

    Moyennes : hébergeur 3,50 et ESN 3,75 — indistinguables, et dans le
    mauvais ordre au regard du risque. Le ratio les écarte d'un facteur 1,4 et
    remonte l'ESN devant : plus de pénétration pour moins de maturité et moins
    de confiance.
    """
    hebergeur = tprm.ratio_anssi(5, 5, 4, 4)
    esn = tprm.ratio_anssi(4, 5, 3, 3)

    assert (hebergeur["score"], esn["score"]) == (1.56, 2.22)
    assert esn["score"] > hebergeur["score"]
    assert round(esn["score"] / hebergeur["score"], 1) == 1.4


def test_le_ratio_fait_decrocher_un_tiers_peu_expose():
    """Le cabinet comptable passe de 2,25 (moyenne, soit « au milieu ») à 0,25
    — il cesse d'encombrer le haut du classement."""
    comptable = tprm.ratio_anssi(2, 1, 2, 4)
    assert comptable["score"] == 0.25
    assert comptable["rating"] == "Faible"


def test_le_classement_complet_est_priorisable():
    scores = [tprm.ratio_anssi(*t)["score"] for t in [(4, 5, 3, 3), (5, 5, 4, 4), (2, 1, 2, 4)]]
    assert scores == sorted(scores, reverse=True)
    # Amplitude ~9× là où la moyenne tenait dans un intervalle de 1,5 point.
    assert max(scores) / min(scores) > 5


# --- Volet GRC : des exigences, pas un score --------------------------------

def test_le_volet_grc_ne_produit_aucun_score():
    """DORA et NIS2 ne se réclament pas d'EBIOS RM : leur appliquer un scoring
    de risque serait inventer une exigence qu'ils ne portent pas."""
    tiers_grc = {"name": "AWS", "exigences": tprm.exigences_par_defaut()}
    assert "score" not in tprm.conformite(tiers_grc)
    assert "rating" not in tprm.conformite(tiers_grc)


def test_les_exigences_par_defaut_sont_non_cochees():
    exigences = tprm.exigences_par_defaut()
    assert len(exigences) == 4
    assert all(e["satisfait"] is False for e in exigences)
    assert all(e["preuve"] == "" for e in exigences)


def test_les_exigences_couvrent_les_articles_dora_cites():
    ids = {e["id"] for e in tprm.exigences_par_defaut()}
    assert {"DORA-28.3", "DORA-30", "SORTIE", "NIST-ID.RA-10"} == ids


def test_deux_appels_ne_partagent_pas_la_meme_liste():
    """Sinon cocher une exigence sur un tiers la cocherait sur tous."""
    a, b = tprm.exigences_par_defaut(), tprm.exigences_par_defaut()
    a[0]["satisfait"] = True
    assert b[0]["satisfait"] is False


def test_le_taux_de_conformite_suit_les_cases_cochees():
    exigences = tprm.exigences_par_defaut()
    exigences[0]["satisfait"] = True
    exigences[1]["satisfait"] = True
    resultat = tprm.conformite({"exigences": exigences})
    assert (resultat["satisfaites"], resultat["total"], resultat["taux"]) == (2, 4, 50)
    assert resultat["conforme"] is False


def test_un_tiers_sans_exigence_n_est_pas_declare_conforme():
    """Zéro sur zéro vaut 100 % en arithmétique — pas en conformité."""
    resultat = tprm.conformite({"name": "Tiers vierge"})
    assert resultat["taux"] == 0
    assert resultat["conforme"] is False


def test_toutes_les_exigences_cochees_declarent_le_tiers_conforme():
    exigences = [{**e, "satisfait": True} for e in tprm.exigences_par_defaut()]
    assert tprm.conformite({"exigences": exigences})["conforme"] is True


# --- Le recalcul n'est jamais silencieux ------------------------------------

def _mission(volet: str, tiers: list[dict]) -> dict:
    return {"type": volet, "steps": {"tprm": {"tiers": tiers}}}


def test_un_tiers_note_a_l_ancienne_est_signale():
    state = _mission("consulting", [{"name": "ESN", "methode": tprm.METHODE_HISTORIQUE}])
    assert tprm.tiers_a_recalculer(state) == ["ESN"]


def test_un_tiers_sans_methode_est_traite_comme_ancien():
    """Une mission antérieure au 29/07/2026 n'a pas le champ du tout."""
    state = _mission("consulting", [{"name": "Ancien", "score": 3.5}])
    assert tprm.tiers_a_recalculer(state) == ["Ancien"]


def test_un_tiers_deja_au_ratio_n_est_pas_signale():
    state = _mission("consulting", [{"name": "AWS", "methode": tprm.METHODE_ANSSI}])
    assert tprm.tiers_a_recalculer(state) == []


def test_une_mission_grc_ne_propose_jamais_de_recalcul():
    """Il n'y a rien à recalculer : ce volet n'a pas de score."""
    state = _mission("grc", [{"name": "AWS", "methode": tprm.METHODE_HISTORIQUE}])
    assert tprm.tiers_a_recalculer(state) == []


def test_le_recalcul_applique_le_ratio_et_marque_la_methode():
    state = _mission("consulting", [
        {"name": "ESN", "dependence": 4, "penetration": 5, "maturity": 3, "trust": 3,
         "score": 3.75, "rating": "Élevé", "methode": tprm.METHODE_HISTORIQUE},
    ])
    state, recalcules = tprm.recalculer_mission(state)
    tier = state["steps"]["tprm"]["tiers"][0]

    assert recalcules == 1
    assert tier["score"] == 2.22
    assert tier["methode"] == tprm.METHODE_ANSSI


def test_le_recalcul_conserve_le_nom_et_les_curseurs():
    """Il ne réévalue rien : il réapplique une formule aux mêmes saisies."""
    state = _mission("consulting", [
        {"name": "Cabinet Comptable", "dependence": 2, "penetration": 1,
         "maturity": 2, "trust": 4, "score": 2.25, "methode": tprm.METHODE_HISTORIQUE},
    ])
    state, _ = tprm.recalculer_mission(state)
    tier = state["steps"]["tprm"]["tiers"][0]

    assert tier["name"] == "Cabinet Comptable"
    assert (tier["dependence"], tier["penetration"], tier["maturity"], tier["trust"]) == (2, 1, 2, 4)


def test_le_recalcul_ne_retouche_pas_un_tiers_deja_au_ratio():
    state = _mission("consulting", [
        {"name": "AWS", "dependence": 5, "penetration": 5, "maturity": 4, "trust": 4,
         "score": 1.56, "methode": tprm.METHODE_ANSSI},
    ])
    _, recalcules = tprm.recalculer_mission(state)
    assert recalcules == 0


def test_le_recalcul_d_une_mission_sans_tiers_ne_casse_pas():
    state, recalcules = tprm.recalculer_mission({"type": "consulting", "steps": {}})
    assert recalcules == 0


# --- Migration v5 -----------------------------------------------------------

def test_la_migration_marque_les_tiers_existants_comme_historiques():
    state = schema_migration.migrate({
        "type": "consulting", "schema_version": 4,
        "steps": {"tprm": {"tiers": [{"name": "ESN", "score": 3.75}]}},
    })
    assert state["steps"]["tprm"]["tiers"][0]["methode"] == tprm.METHODE_HISTORIQUE


def test_la_migration_ne_recalcule_aucune_note():
    """Point dur : une criticité a pu être présentée au client. La migration
    documente la méthode, elle ne change jamais la valeur sous ses pieds."""
    state = schema_migration.migrate({
        "type": "consulting", "schema_version": 4,
        "steps": {"tprm": {"tiers": [{"name": "ESN", "score": 3.75, "rating": "Élevé"}]}},
    })
    tier = state["steps"]["tprm"]["tiers"][0]
    assert tier["score"] == 3.75
    assert tier["rating"] == "Élevé"


def test_la_migration_dote_les_tiers_grc_de_leurs_exigences():
    state = schema_migration.migrate({
        "type": "grc", "schema_version": 4,
        "steps": {"tprm": {"tiers": [{"name": "AWS"}]}},
    })
    assert len(state["steps"]["tprm"]["tiers"][0]["exigences"]) == 4


def test_un_tiers_jamais_note_ne_recoit_pas_de_methode():
    """Lui coller « moyenne_historique » affirmerait un calcul qui n'a pas eu
    lieu — et ferait apparaître une pastille « ancienne méthode » à l'écran."""
    state = schema_migration.migrate({
        "type": "grc", "schema_version": 4,
        "steps": {"tprm": {"tiers": [{"name": "AWS", "dependence": 4}]}},
    })
    assert "methode" not in state["steps"]["tprm"]["tiers"][0]


def test_la_migration_n_ajoute_pas_d_exigences_sur_le_volet_consulting():
    state = schema_migration.migrate({
        "type": "consulting", "schema_version": 4,
        "steps": {"tprm": {"tiers": [{"name": "ESN"}]}},
    })
    assert "exigences" not in state["steps"]["tprm"]["tiers"][0]


def test_la_migration_preserve_des_exigences_deja_renseignees():
    deja = [{"id": "DORA-30", "libelle": "x", "satisfait": True, "preuve": "Contrat signé"}]
    state = schema_migration.migrate({
        "type": "grc", "schema_version": 4,
        "steps": {"tprm": {"tiers": [{"name": "AWS", "exigences": deja}]}},
    })
    assert state["steps"]["tprm"]["tiers"][0]["exigences"] == deja


def test_une_mission_sans_tprm_traverse_la_migration():
    state = schema_migration.migrate({"type": "consulting", "schema_version": 4, "steps": {}})
    assert state["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION


@pytest.mark.parametrize("depart", [1, 2, 3, 4])
def test_une_mission_de_n_importe_quelle_version_arrive_a_jour(depart):
    state = schema_migration.migrate({
        "type": "consulting", "schema_version": depart,
        "steps": {"tprm": {"tiers": [{"name": "ESN", "score": 3.75}]}},
    })
    assert state["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert state["steps"]["tprm"]["tiers"][0]["methode"] == tprm.METHODE_HISTORIQUE
