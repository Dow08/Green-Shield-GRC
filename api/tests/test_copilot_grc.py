"""Tests du Copilote GRC transverse : agrégation factuelle des constats de
toutes les missions du registre, et bascule en ligne (Gemini) / hors-ligne."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import copilot_grc  # noqa: E402
from modules import projects  # noqa: E402


def _write_project(base: Path, project_id: str, state: dict) -> None:
    p_dir = base / project_id
    p_dir.mkdir()
    (p_dir / "project.json").write_text(json.dumps(state), encoding="utf-8")


@pytest.fixture()
def empty_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    return tmp_path


@pytest.fixture()
def populated_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    _write_project(tmp_path, "acme", {
        "id": "acme", "name": "Acme", "client": "Acme Corp", "type": "grc", "progress": 60,
        "steps": {
            "tprm": {"tiers": [
                {"name": "Infogéreur X", "score": 4.5, "rating": "Critique"},
                {"name": "Cabinet compta", "score": 2.0, "rating": "Faible"},
            ]},
            "ebios": {"redoute_events": [
                {"event": "Ransomware sur SI production", "gravity": 4},
                {"event": "Incident mineur", "gravity": 1},
            ]},
            "evaluation": {"technical_results": {"controls": [
                {"title": "PermitRootLogin doit être désactivé", "status": "NON_CONFORME", "severity": "Critique"},
                {"title": "Port SSH standard", "status": "CONFORME", "severity": "Faible"},
            ]}},
            "traitement": {"validated": False, "quick_wins": ["a", "b", "c"]},
        },
    })
    _write_project(tmp_path, "cassiope", {
        "id": "cassiope", "name": "Cassiopé", "client": "Cassiopé Asso", "type": "consulting", "progress": 40,
        "steps": {
            "tprm": {"tiers": [{"name": "Hébergeur cloud", "score": 3.5, "rating": "Élevé"}]},
            "traitement": {"validated": True, "quick_wins": ["x", "y"]},
        },
    })
    return tmp_path


# --- aggregate_context ----------------------------------------------------

def test_aggregate_context_sur_registre_vide_ne_fabrique_aucune_donnee(empty_registry):
    ctx = copilot_grc.aggregate_context()
    assert ctx["total_projects"] == 0
    assert ctx["avg_progress"] == 0
    assert ctx["tiers_critiques"] == []
    assert ctx["redoute_events"] == []
    assert ctx["non_conformites"] == []
    assert ctx["quick_wins_en_attente"] == 0


def test_aggregate_context_compte_les_missions_par_type(populated_registry):
    ctx = copilot_grc.aggregate_context()
    assert ctx["total_projects"] == 2
    assert ctx["by_type"] == {"grc": 1, "consulting": 1}
    # list_projects() recalcule la progression à partir des étapes
    # (calculate_progress) : le champ "progress" écrit dans la fixture est ignoré.
    # La valeur exacte dépend du barème, qui a évolué le 30/07/2026 pour ne plus
    # créditer la maturité du client — on vérifie donc la moyenne, pas un nombre
    # arbitraire à réécrire à chaque ajustement.
    par_mission = [p["progress"] for p in projects.list_projects()]
    assert ctx["avg_progress"] == round(sum(par_mission) / len(par_mission))


def test_aggregate_context_ne_retient_que_les_tiers_critiques_ou_eleves(populated_registry):
    ctx = copilot_grc.aggregate_context()
    noms = {t["tiers_name"] for t in ctx["tiers_critiques"]}
    assert noms == {"Infogéreur X", "Hébergeur cloud"}
    assert "Cabinet compta" not in noms  # rating Faible : exclu


def test_aggregate_context_trie_les_tiers_par_score_decroissant(populated_registry):
    ctx = copilot_grc.aggregate_context()
    scores = [t["score"] for t in ctx["tiers_critiques"]]
    assert scores == sorted(scores, reverse=True)


def test_aggregate_context_ne_retient_que_les_evenements_graves(populated_registry):
    ctx = copilot_grc.aggregate_context()
    events = {e["event"] for e in ctx["redoute_events"]}
    assert events == {"Ransomware sur SI production"}


def test_aggregate_context_agrege_les_non_conformites_techniques(populated_registry):
    ctx = copilot_grc.aggregate_context()
    assert len(ctx["non_conformites"]) == 1
    assert ctx["non_conformites"][0]["control"] == "PermitRootLogin doit être désactivé"


def test_aggregate_context_compte_les_quick_wins_seulement_pour_les_missions_non_validees(populated_registry):
    ctx = copilot_grc.aggregate_context()
    # Acme (non validé) : 3 quick wins comptés. Cassiopé (validé) : ignoré.
    assert ctx["quick_wins_en_attente"] == 3


# --- ask_copilot : hors-ligne ---------------------------------------------

def test_ask_sans_projets_indique_le_portefeuille_vide(empty_registry):
    result = copilot_grc.ask_copilot({"prompt": "priorise mes risques"})
    assert result["source"] == "offline"
    assert "vide" in result["response"].lower() or "aucune mission" in result["response"].lower()


def test_ask_hors_ligne_utilise_les_chiffres_reels_agreges(populated_registry):
    result = copilot_grc.ask_copilot({"prompt": "priorise mes risques"})
    assert result["source"] == "offline"
    assert "Infogéreur X" in result["response"]
    assert "Ransomware sur SI production" in result["response"]
    assert "PermitRootLogin doit être désactivé" in result["response"]


# --- ask_copilot : en ligne / repli ----------------------------------------

def test_ask_avec_cle_valide_appelle_gemini(populated_registry, monkeypatch):
    captured = {}

    def fake_call(api_key, system_context, prompt):
        captured["api_key"] = api_key
        captured["system_context"] = system_context
        return "Synthèse générée par Gemini"

    monkeypatch.setattr(copilot_grc.ai_gateway, "call_gemini", fake_call)
    result = copilot_grc.ask_copilot({"prompt": "priorise", "key": "fake-key"})
    assert result == {
        "status": "success",
        "response": "Synthèse générée par Gemini",
        "source": "online",
        "context": result["context"],
    }
    assert captured["api_key"] == "fake-key"
    assert "2 mission(s)" in captured["system_context"]


def test_ask_avec_cle_invalide_bascule_vers_le_repli_hors_ligne(populated_registry, monkeypatch):
    monkeypatch.setattr(copilot_grc.ai_gateway, "call_gemini", lambda *a, **k: None)
    result = copilot_grc.ask_copilot({"prompt": "priorise", "key": "bad-key"})
    assert result["source"] == "offline_fallback"
    assert "Infogéreur X" in result["response"]


# --- endpoint GET /api/copilot/context ------------------------------------

def test_get_copilot_context_endpoint_renvoie_l_agregat(populated_registry):
    assert copilot_grc.get_copilot_context() == copilot_grc.aggregate_context()
