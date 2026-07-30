"""Tests de la revue de complétude avant export.

Enjeu : un livrable client ne doit pas partir criblé de « N/A » sans que le
consultant l'ait vu. Ces tests vérifient que les manques sont détectés — et
surtout qu'aucun manque n'est inventé sur une mission complète.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import aipd, revue_export  # noqa: E402


def mission_complete() -> dict:
    return {
        "steps": {
            "cadrage": {
                "scope": "SI de production", "client_missions": "Distribution",
                "nda_signed": True, "nda_text": "ACCORD…",
                "assets_metier": [{"id": "VM-01"}], "assets_support": [{"id": "BS-01"}],
            },
            "diagnostic": {
                "rgpd_register": [{"id": "RGPD-01"}], "aipd_required": True,
                # Une AIPD complète, c'est les 4 volets d'analyse *et* les
                # obligations de procédure (§14.2.1).
                "aipd": {"treatment_description": "d", "necessity_eval": "n",
                         "risks_eval": "r", "mitigation_measures": "m",
                         "risque_residuel": "acceptable",
                         "obligations": [{"id": o["id"], "satisfait": True, "commentaire": ""}
                                         for o in aipd.OBLIGATIONS]},
            },
            "tprm": {"tiers": [{"name": "Hébergeur"}]},
            "ebios": {"redoute_events": [{"id": "ER-01"}], "operational_scenarios": [{"id": "SC-01"}]},
            "resilience": {
                "bcp_strategy": {"rto": "4 h", "rpo": "1 h", "backup_policy": "Immuable"},
                "e3r": {"endiguement": "e", "eviction": "v", "eradication": "r", "reconstruction": "c"},
                "strategie_remediation": {"decision_direction": "Priorité à l'éradication avant redémarrage."},
            },
            "traitement": {"remediations": [{"id": "REM-01"}], "quick_wins": ["a"]},
            # Une mission « complète » l'est désormais aussi du point de vue du
            # *rendu* : la revue vérifie qu'aucun chapitre du rapport ne sortirait
            # vide, ce qui suppose une synthèse rédigée (§14.2, recette 29/07/2026).
            "restitution": {"exec_summary": "Deux écarts majeurs, aucun structurel."},
        },
        "socle": {
            "qualification": {"declencheur": "Exigence du donneur d'ordre",
                              "sponsor_executif": "Directeur Général", "budget": "12 jours"},
            "contractualisation": {"perimetre_inclus": "SI de production",
                                   "perimetre_exclu": "Filiale étrangère"},
            "kickoff": {"date": "2026-06-03", "gouvernance": "Comité bimensuel"},
        },
    }


def champs(resultat: dict) -> set[str]:
    return {m["champ"] for m in resultat["manques"]}


# --- Mission complète : aucun manque inventé -------------------------------

def test_une_mission_complete_ne_remonte_aucun_manque():
    r = revue_export.revue(mission_complete())
    assert r["complet"] is True
    assert r["pret_pour_export"] is True
    assert r["manques"] == []


def test_une_mission_vide_remonte_des_manques_bloquants():
    r = revue_export.revue({})
    assert r["complet"] is False
    assert r["pret_pour_export"] is False
    assert r["bloquants"] > 0


def test_l_absence_de_steps_ne_plante_pas():
    revue_export.revue({"id": "x"})  # ne doit rien lever


# --- Détection ciblée ------------------------------------------------------

def test_detecte_un_perimetre_non_defini():
    m = mission_complete()
    m["steps"]["cadrage"]["scope"] = "   "  # espaces seuls
    assert "Périmètre technique de l'audit" in champs(revue_export.revue(m))


def test_detecte_un_inventaire_d_actifs_vide():
    m = mission_complete()
    m["steps"]["cadrage"]["assets_support"] = []
    assert "Inventaire des biens supports" in champs(revue_export.revue(m))


def test_detecte_le_nda_non_signe_sans_bloquer_l_export():
    m = mission_complete()
    m["steps"]["cadrage"]["nda_signed"] = False
    r = revue_export.revue(m)
    assert "NDA non signé" in champs(r)
    assert r["pret_pour_export"] is True  # signalé, mais non bloquant


def test_detecte_les_cibles_rto_rpo_manquantes():
    m = mission_complete()
    m["steps"]["resilience"]["bcp_strategy"] = {}
    c = champs(revue_export.revue(m))
    assert "Cible de reprise (RTO)" in c
    assert "Perte de données maximale admissible (RPO)" in c


def test_detecte_un_plan_de_traitement_vide():
    m = mission_complete()
    m["steps"]["traitement"]["remediations"] = []
    assert "Plan d'action de remédiation" in champs(revue_export.revue(m))


# --- AIPD : conditionnelle -------------------------------------------------

def test_l_aipd_n_est_exigee_que_si_elle_est_requise():
    m = mission_complete()
    m["steps"]["diagnostic"]["aipd_required"] = False
    m["steps"]["diagnostic"]["aipd"] = {}
    c = champs(revue_export.revue(m))
    assert not any(ch.startswith("AIPD") for ch in c)


def test_l_aipd_incomplete_est_signalee_quand_elle_est_requise():
    m = mission_complete()
    m["steps"]["diagnostic"]["aipd"]["risks_eval"] = ""
    assert "AIPD — évaluation des risques" in champs(revue_export.revue(m))


# --- Structure du résultat -------------------------------------------------

def test_chaque_manque_indique_sa_phase_pour_y_naviguer():
    r = revue_export.revue({})
    for m in r["manques"]:
        assert m["phase"] in revue_export.PHASES
        assert m["phase_libelle"] == revue_export.PHASES[m["phase"]]
        assert m["gravite"] in ("bloquant", "recommande")


def test_le_compte_de_bloquants_est_coherent():
    r = revue_export.revue({})
    assert r["bloquants"] == len([m for m in r["manques"] if m["gravite"] == "bloquant"])
    assert r["total"] == len(r["manques"])


@pytest.mark.parametrize("valeur", [None, "", "   ", [], {}])
def test_toutes_les_formes_de_vide_sont_detectees(valeur):
    m = mission_complete()
    m["steps"]["cadrage"]["scope"] = valeur
    assert "Périmètre technique de l'audit" in champs(revue_export.revue(m))


def test_une_valeur_renseignee_n_est_jamais_signalee():
    m = mission_complete()
    m["steps"]["cadrage"]["scope"] = "0"  # chaîne falsy mais renseignée
    assert "Périmètre technique de l'audit" not in champs(revue_export.revue(m))
