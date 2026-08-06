"""Tests du registre des demandes de preuves (api/modules/demandes_preuves.py).

Le registre traite un fait de gestion, pas un constat d'audit : ces tests
vérifient d'abord qu'il ne transforme jamais une absence en conformité.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import demandes_preuves as dp  # noqa: E402

LE_JOUR = date(2026, 8, 5)


def _mission(demandes=None, controles=None, preuves=None) -> dict:
    return {
        "socle": {"demandes_preuves": demandes or []},
        "steps": {"evaluation": {
            "manual_controls": controles or [],
            "preuves": preuves or [],
        }},
    }


def _demande(**kwargs) -> dict:
    base = {"id": "DEM-01", "libelle": "PSSI signée", "destinataire": "RSSI",
            "statut": "demandee", "date_demande": "2026-08-01", "controles_lies": []}
    base.update(kwargs)
    return base


# --- Lecture ---------------------------------------------------------------

def test_une_mission_sans_socle_ne_provoque_pas_d_erreur():
    assert dp.liste({}) == []
    assert dp.synthese({})["total"] == 0


def test_les_entrees_malformees_sont_ignorees_sans_planter():
    # Un fichier de mission édité à la main ne doit pas casser l'écran.
    mission = {"socle": {"demandes_preuves": [None, "texte", _demande()]}}
    assert len(dp.liste(mission)) == 1


# --- Ancienneté et relance -------------------------------------------------

def test_l_anciennete_se_compte_depuis_la_demande():
    d = _demande(date_demande="2026-08-01")
    assert dp.jours_depuis_demande(d, LE_JOUR) == 4


def test_une_relance_fait_repartir_le_compteur():
    # Le délai qui compte est celui écoulé depuis le dernier signal envoyé au
    # client, sinon toute demande relancée resterait éternellement « à relancer ».
    d = _demande(date_demande="2026-07-01", date_relance="2026-08-03", statut="relancee")
    assert dp.jours_depuis_demande(d, LE_JOUR) == 2


def test_une_date_absente_ou_illisible_ne_produit_pas_d_anciennete():
    assert dp.jours_depuis_demande(_demande(date_demande=""), LE_JOUR) is None
    assert dp.jours_depuis_demande(_demande(date_demande="pas-une-date"), LE_JOUR) is None


def test_a_relancer_au_dela_du_delai_admis():
    ancienne = _demande(date_demande="2026-07-20")
    recente = _demande(date_demande="2026-08-04")
    assert dp.a_relancer(ancienne, LE_JOUR) is True
    assert dp.a_relancer(recente, LE_JOUR) is False


def test_une_demande_close_n_est_jamais_a_relancer():
    for statut in ("recue", "refusee"):
        d = _demande(statut=statut, date_demande="2026-01-01")
        assert dp.a_relancer(d, LE_JOUR) is False


def test_une_demande_sans_date_n_est_pas_signalee_a_relancer():
    # Ne rien inventer : sans date, on ne sait pas depuis quand on attend.
    assert dp.a_relancer(_demande(date_demande=None), LE_JOUR) is False


# --- Synthèse --------------------------------------------------------------

def test_la_synthese_compte_chaque_statut_separement():
    mission = _mission([
        _demande(id="D1", statut="demandee", date_demande="2026-08-04"),
        _demande(id="D2", statut="relancee", date_demande="2026-07-01"),
        _demande(id="D3", statut="recue"),
        _demande(id="D4", statut="refusee"),
    ])
    s = dp.synthese(mission, LE_JOUR)
    assert s["total"] == 4
    assert s["en_attente"] == 2
    assert s["recues"] == 1
    assert s["refusees"] == 1
    assert s["a_relancer"] == 1


def test_la_synthese_remonte_la_plus_ancienne_attente():
    # C'est la doyenne qui met la restitution en danger, pas le volume.
    mission = _mission([
        _demande(id="D1", date_demande="2026-08-04"),
        _demande(id="D2", date_demande="2026-06-01"),
    ])
    assert dp.synthese(mission, LE_JOUR)["plus_ancienne_jours"] == 65


def test_un_refus_du_client_n_est_pas_compte_comme_une_attente():
    # Un refus est une réponse : le consultant sait à quoi s'en tenir.
    mission = _mission([_demande(statut="refusee", date_demande="2026-01-01")])
    s = dp.synthese(mission, LE_JOUR)
    assert s["en_attente"] == 0
    assert s["plus_ancienne_jours"] is None


# --- Revue avant export ----------------------------------------------------

def test_aucune_demande_ouverte_ne_produit_aucun_manque():
    assert dp.manques_pour_revue(_mission([_demande(statut="recue")])) == []


def test_les_demandes_ouvertes_sont_signalees_sans_bloquer_l_export():
    # Le consultant peut livrer en mentionnant qu'une pièce n'est pas venue :
    # le bloquer lui imposerait une exhaustivité que seul le client accorde.
    mission = _mission([_demande(id="D1"), _demande(id="D2", libelle="Contrat infogérance")])
    manques = dp.manques_pour_revue(mission, LE_JOUR)
    assert len(manques) == 1
    assert manques[0]["gravite"] == "recommande"
    assert "2 demande(s)" in manques[0]["champ"]
    assert "Contrat infogérance" in manques[0]["champ"]


def test_le_libelle_de_revue_reste_lisible_au_dela_de_trois_demandes():
    mission = _mission([_demande(id=f"D{i}", libelle=f"Doc {i}") for i in range(6)])
    champ = dp.manques_pour_revue(mission, LE_JOUR)[0]["champ"]
    assert "(+3)" in champ


# --- Contrôles sans preuve ni demande --------------------------------------

def test_un_controle_conforme_sans_preuve_ni_demande_est_signale():
    mission = _mission(controles=[
        {"id": "ISO-A.5", "referentiel_id": "iso27001", "status": "CONFORME", "title": "Politiques"},
    ])
    orphelins = dp.controles_sans_preuve_ni_demande(mission)
    assert len(orphelins) == 1
    assert orphelins[0]["control_id"] == "ISO-A.5"


def test_un_controle_couvert_par_une_preuve_n_est_pas_signale():
    mission = _mission(
        controles=[{"id": "ISO-A.5", "referentiel_id": "iso27001", "status": "CONFORME"}],
        preuves=[{"id": "PRV-01", "controles_lies": [
            {"referentiel_id": "iso27001", "control_id": "ISO-A.5"}]}],
    )
    assert dp.controles_sans_preuve_ni_demande(mission) == []


def test_une_demande_en_cours_suffit_a_ne_plus_signaler_le_controle():
    # Le consultant a déjà agi : le lui redire serait du bruit.
    mission = _mission(
        demandes=[_demande(controles_lies=[
            {"referentiel_id": "iso27001", "control_id": "ISO-A.5"}])],
        controles=[{"id": "ISO-A.5", "referentiel_id": "iso27001", "status": "CONFORME"}],
    )
    assert dp.controles_sans_preuve_ni_demande(mission) == []


def test_une_demande_close_ne_couvre_plus_le_controle():
    # Demande refusée par le client : le contrôle redevient sans justificatif.
    mission = _mission(
        demandes=[_demande(statut="refusee", controles_lies=[
            {"referentiel_id": "iso27001", "control_id": "ISO-A.5"}])],
        controles=[{"id": "ISO-A.5", "referentiel_id": "iso27001", "status": "CONFORME"}],
    )
    assert len(dp.controles_sans_preuve_ni_demande(mission)) == 1


def test_un_controle_non_conforme_n_appelle_aucune_preuve():
    # C'est l'absence qui est constatée : réclamer une pièce n'aurait pas de sens.
    mission = _mission(controles=[
        {"id": "ISO-A.8", "referentiel_id": "iso27001", "status": "NON_CONFORME"},
        {"id": "ISO-A.9", "referentiel_id": "iso27001", "status": "A_VERIFIER"},
    ])
    assert dp.controles_sans_preuve_ni_demande(mission) == []
