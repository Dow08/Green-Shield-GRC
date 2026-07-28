"""Tests du catalogue de mesures réutilisable (décision G3)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import mesures_catalogue  # noqa: E402


def test_catalogue_se_charge_et_n_est_pas_vide():
    mesures = mesures_catalogue.list_mesures()
    assert len(mesures) >= 15


def test_chaque_mesure_a_un_axe_valide():
    for m in mesures_catalogue.list_mesures():
        assert m["axe"] in mesures_catalogue.AXES_VALIDES


def test_identifiants_uniques():
    ids = [m["id"] for m in mesures_catalogue.list_mesures()]
    assert len(ids) == len(set(ids))


def test_get_mesure_par_id():
    mfa = mesures_catalogue.get_mesure("MFA-ACCES-DISTANTS")
    assert mfa is not None
    assert mfa["axe"] == "Protection"
    assert "A.8.5" in mfa["mappings"]["iso27001"]


def test_get_mesure_inconnue_renvoie_none_pas_une_exception():
    assert mesures_catalogue.get_mesure("N-EXISTE-PAS") is None


def test_filtre_par_axe():
    gouvernance = mesures_catalogue.mesures_par_axe("Gouvernance")
    assert len(gouvernance) > 0
    assert all(m["axe"] == "Gouvernance" for m in gouvernance)


def test_filtre_par_referentiel_nis2():
    """Vérifie le point d'usage prévu au Jalon 3 : construire le plan NIS2
    à partir des mesures déjà mappées, sans en réécrire."""
    nis2 = mesures_catalogue.mesures_pour_referentiel("nis2")
    assert len(nis2) >= 5
    assert all("nis2" in m["mappings"] for m in nis2)


def test_g2_architecture_couverte_segmentation_et_zero_trust():
    """La décision G2 (checklist architecture) doit trouver ses mesures ici."""
    ids = {m["id"] for m in mesures_catalogue.list_mesures()}
    assert "SEGMENTATION-RESEAU" in ids
    assert "ZERO-TRUST-MATURITE" in ids


def test_g1_homologation_et_g4_exercice_de_crise_couverts():
    ids = {m["id"] for m in mesures_catalogue.list_mesures()}
    assert "HOMOLOGATION-DECISION-FORMELLE" in ids
    assert "EXERCICE-CRISE-CYBER" in ids


def test_mesure_avec_mappings_absents_est_acceptee(tmp_path, monkeypatch):
    """Une mesure sans mapping vers un référentiel donné (ex: pas encore de
    mapping DORA) ne doit pas planter le chargement du catalogue entier."""
    catalogue = tmp_path / "cat.yaml"
    catalogue.write_text(
        "mesures:\n"
        "  - id: TEST-01\n"
        "    titre: Test\n"
        "    axe: Protection\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mesures_catalogue, "CATALOGUE_PATH", catalogue)
    assert mesures_catalogue.mesures_pour_referentiel("dora") == []


def test_axe_invalide_leve_une_erreur_explicite(tmp_path, monkeypatch):
    catalogue = tmp_path / "cat.yaml"
    catalogue.write_text(
        "mesures:\n  - id: X\n    titre: Y\n    axe: PasUnAxe\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mesures_catalogue, "CATALOGUE_PATH", catalogue)
    with pytest.raises(ValueError, match="Axe invalide"):
        mesures_catalogue.list_mesures()


def test_identifiant_duplique_leve_une_erreur_explicite(tmp_path, monkeypatch):
    catalogue = tmp_path / "cat.yaml"
    catalogue.write_text(
        "mesures:\n"
        "  - {id: DUP, titre: A, axe: Protection}\n"
        "  - {id: DUP, titre: B, axe: Défense}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mesures_catalogue, "CATALOGUE_PATH", catalogue)
    with pytest.raises(ValueError, match="dupliqué"):
        mesures_catalogue.list_mesures()
