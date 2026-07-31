"""Tests de la bibliothèque de preuves multi-référentiels (G3bis, 31/07/2026)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import preuves  # noqa: E402


def _controles():
    return [
        {"id": "ISO-A.5", "referentiel_id": "iso27001", "title": "Politiques"},
        {"id": "DORA-ICT", "referentiel_id": "dora", "title": "Cadre de gestion des risques TIC"},
    ]


def test_aucune_preuve_ne_couvre_aucun_controle():
    resultat = preuves.couverture([], _controles())
    assert resultat == {"total": 2, "couverts": 0, "non_couverts": 2, "taux": 0}


def test_une_preuve_liee_a_un_seul_controle_couvre_un_seul_controle():
    p = [{"id": "PRV-01", "libelle": "PSSI signée", "controles_lies": [
        {"referentiel_id": "iso27001", "control_id": "ISO-A.5"},
    ]}]
    resultat = preuves.couverture(p, _controles())
    assert resultat == {"total": 2, "couverts": 1, "non_couverts": 1, "taux": 50}


def test_une_preuve_multi_referentiel_couvre_deux_controles_a_la_fois():
    """L'intérêt même de la bibliothèque : une preuve, plusieurs référentiels."""
    p = [{"id": "PRV-01", "libelle": "PSSI signée", "controles_lies": [
        {"referentiel_id": "iso27001", "control_id": "ISO-A.5"},
        {"referentiel_id": "dora", "control_id": "DORA-ICT"},
    ]}]
    resultat = preuves.couverture(p, _controles())
    assert resultat == {"total": 2, "couverts": 2, "non_couverts": 0, "taux": 100}


def test_un_meme_control_id_dans_deux_referentiels_n_est_pas_confondu():
    """Deux référentiels peuvent réutiliser le même identifiant de contrôle
    par coïncidence — la couverture doit distinguer (referentiel_id, control_id),
    pas seulement control_id."""
    controles = [
        {"id": "A.5", "referentiel_id": "iso27001", "title": "Politiques"},
        {"id": "A.5", "referentiel_id": "nis2", "title": "Autre exigence homonyme"},
    ]
    p = [{"id": "PRV-01", "libelle": "x", "controles_lies": [
        {"referentiel_id": "iso27001", "control_id": "A.5"},
    ]}]
    resultat = preuves.couverture(p, controles)
    assert resultat["couverts"] == 1


def test_preuves_pour_controle_retourne_les_preuves_liees():
    p = [
        {"id": "PRV-01", "libelle": "PSSI signée", "controles_lies": [
            {"referentiel_id": "iso27001", "control_id": "ISO-A.5"}]},
        {"id": "PRV-02", "libelle": "Contrat sous-traitant conforme", "controles_lies": [
            {"referentiel_id": "dora", "control_id": "DORA-ICT"}]},
    ]
    assert [x["id"] for x in preuves.preuves_pour_controle(p, "iso27001", "ISO-A.5")] == ["PRV-01"]
    assert [x["id"] for x in preuves.preuves_pour_controle(p, "dora", "DORA-ICT")] == ["PRV-02"]
    assert preuves.preuves_pour_controle(p, "iso27001", "ISO-A.6") == []
