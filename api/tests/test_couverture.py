"""Tests du taux de couverture technique (F10).

L'audit relève que la promesse « preuve technique plutôt que déclaratif » est
vraie mais partielle. Afficher le taux réel est plus honnête que le taire — à
condition que le chiffre soit juste, d'où ces tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import couverture  # noqa: E402


def mission(controles=None, regles=None, scan=True) -> dict:
    evaluation = {"manual_controls": controles if controles is not None else []}
    if scan:
        evaluation["technical_results"] = {"controls": regles or []}
    return {"steps": {"evaluation": evaluation}}


CONTROLES = [
    {"id": "ISO-A.5", "title": "Politiques"},
    {"id": "ISO-A.8.2", "title": "Droits d'accès privilégiés"},
    {"id": "ISO-A.8.5", "title": "Authentification"},
]

REGLES = [
    {"id": "SSH-ROOT-01", "frameworks": ["ISO 27001:2022 — A.8.2 Droits d'accès privilégiés",
                                          "ISO 27001:2022 — A.8.5 Authentification sécurisée"]},
    {"id": "SSH-EMPTY-01", "frameworks": ["ISO 27001:2022 — A.8.5 Authentification sécurisée"]},
]


# --- Calcul ----------------------------------------------------------------

def test_compte_les_controles_reellement_appuyes():
    c = couverture.couverture_technique(mission(CONTROLES, REGLES))
    assert c["controles_total"] == 3
    assert c["controles_couverts"] == 2  # A.8.2 et A.8.5 ; A.5 ne l'est pas
    assert c["taux"] == 67


def test_liste_les_regles_qui_appuient_chaque_controle():
    c = couverture.couverture_technique(mission(CONTROLES, REGLES))
    par_id = {d["controle"]: d for d in c["details"]}
    assert par_id["ISO-A.8.5"]["preuves"] == ["SSH-ROOT-01", "SSH-EMPTY-01"]
    assert par_id["ISO-A.5"]["preuves"] == []
    assert par_id["ISO-A.5"]["couvert"] is False


def test_une_clause_proche_ne_compte_pas_comme_couverte():
    """A.8.2 ne doit pas être considérée couverte par une règle qui ne
    mentionne qu'A.8.20 — la confusion gonflerait artificiellement le taux."""
    regles = [{"id": "NET-01", "frameworks": ["ISO 27001:2022 — A.8.20 Sécurité des réseaux"]}]
    c = couverture.couverture_technique(mission([{"id": "ISO-A.8.2", "title": "x"}], regles))
    assert c["controles_couverts"] == 0


def test_la_clause_exacte_est_bien_reconnue():
    regles = [{"id": "NET-01", "frameworks": ["ISO 27001:2022 — A.8.20 Sécurité des réseaux"]}]
    c = couverture.couverture_technique(mission([{"id": "ISO-A.8.20", "title": "x"}], regles))
    assert c["controles_couverts"] == 1


def test_un_identifiant_sans_prefixe_est_accepte():
    regles = [{"id": "R1", "frameworks": ["ISO 27001:2022 — A.8.2 Droits"]}]
    c = couverture.couverture_technique(mission([{"id": "A.8.2", "title": "x"}], regles))
    assert c["controles_couverts"] == 1


def test_sans_scan_le_taux_est_nul_et_signale():
    c = couverture.couverture_technique(mission(CONTROLES, scan=False))
    assert c["scan_execute"] is False
    assert c["controles_couverts"] == 0


def test_sans_controle_le_taux_ne_divise_pas_par_zero():
    c = couverture.couverture_technique(mission([], REGLES))
    assert c["taux"] == 0


def test_une_mission_vide_ne_plante_pas():
    assert couverture.couverture_technique({})["controles_total"] == 0


# --- Formulation destinée au client ---------------------------------------

def test_la_phrase_donne_les_deux_nombres_et_le_taux():
    p = couverture.phrase(couverture.couverture_technique(mission(CONTROLES, REGLES)))
    assert "2 contrôle(s) sur 3" in p
    assert "67 %" in p


def test_la_phrase_precise_que_le_reste_est_declaratif():
    """C'est le point : ne pas laisser croire que tout l'audit est automatisé."""
    p = couverture.phrase(couverture.couverture_technique(mission(CONTROLES, REGLES)))
    assert "déclaratif" in p


def test_la_phrase_annonce_l_absence_de_scan_sans_detour():
    p = couverture.phrase(couverture.couverture_technique(mission(CONTROLES, scan=False)))
    assert "Aucun scan technique" in p
    assert "déclaratif" in p


def test_la_phrase_gere_l_absence_de_controle():
    p = couverture.phrase(couverture.couverture_technique(mission([], REGLES)))
    assert "Aucun contrôle organisationnel" in p


# --- Intégration au rapport d'audit ---------------------------------------

def test_le_rapport_d_audit_affiche_la_couverture():
    from modules import report_builder
    etat = mission(CONTROLES, REGLES)
    etat.update({"id": "acme", "name": "M", "client": "C"})
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "Couverture technique de cet audit" in contenu
    assert "2 contrôle(s) sur 3" in contenu


def test_le_rapport_annonce_l_absence_de_scan():
    from modules import report_builder
    etat = mission(CONTROLES, scan=False)
    etat.update({"id": "acme", "name": "M", "client": "C"})
    _, contenu = report_builder.build_document(etat, "acme", "audit_report")
    assert "Aucun scan technique" in contenu


# --- Route ----------------------------------------------------------------

def test_la_route_renvoie_le_detail_et_la_phrase(tmp_path, monkeypatch):
    import json
    from fastapi import HTTPException
    from modules import projects

    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    p_dir = tmp_path / "acme"
    p_dir.mkdir()
    etat = mission(CONTROLES, REGLES)
    etat.update({"id": "acme"})
    (p_dir / "project.json").write_text(json.dumps(etat), encoding="utf-8")

    resultat = projects.get_couverture_technique("acme")
    assert resultat["controles_couverts"] == 2
    assert "2 contrôle(s) sur 3" in resultat["phrase"]

    with pytest.raises(HTTPException):
        projects.get_couverture_technique("inexistante")
