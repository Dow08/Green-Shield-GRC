"""Tests du Copilote IA (endpoint /projects/{id}/copilot) : bascule
en-ligne (Gemini, si clé API fournie) / hors-ligne (intelligence locale)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import ai_gateway, projects  # noqa: E402


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    p_dir = tmp_path / "acme"
    p_dir.mkdir()
    (p_dir / "project.json").write_text(
        json.dumps({"client": "Acme Corp"}), encoding="utf-8"
    )
    return "acme"


def test_sans_cle_api_utilise_l_intelligence_locale(project_dir):
    result = projects.run_project_copilot(project_dir, {"prompt": "Analyse EBIOS RM"})
    assert result["source"] == "offline"
    assert "Acme Corp" in result["response"]


def test_avec_cle_api_valide_appelle_gemini_et_retourne_le_texte(project_dir, monkeypatch):
    def fake_call(api_key, client, prompt):
        assert api_key == "fake-key"
        assert client == "Acme Corp"
        return "Réponse générée par Gemini"

    monkeypatch.setattr(projects, "_call_gemini_copilot", fake_call)
    monkeypatch.setattr(projects.crud, "_call_gemini_copilot", fake_call)
    result = projects.run_project_copilot(project_dir, {"prompt": "Analyse EBIOS RM", "key": "fake-key"})
    assert result == {"status": "success", "response": "Réponse générée par Gemini", "source": "online"}


def test_avec_cle_api_invalide_bascule_silencieusement_en_local(project_dir, monkeypatch):
    monkeypatch.setattr(projects, "_call_gemini_copilot", lambda *a, **k: None)
    monkeypatch.setattr(projects.crud, "_call_gemini_copilot", lambda *a, **k: None)
    result = projects.run_project_copilot(project_dir, {"prompt": "Analyse EBIOS RM", "key": "bad-key"})
    assert result["source"] == "offline_fallback"
    assert "Acme Corp" in result["response"]


def test_projet_introuvable_renvoie_404(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        projects.run_project_copilot("does_not_exist", {"prompt": "x"})
    assert exc_info.value.status_code == 404


def test_call_gemini_copilot_retourne_none_si_reseau_indisponible(monkeypatch):
    def raise_url_error(*args, **kwargs):
        from urllib.error import URLError
        raise URLError("no network")

    monkeypatch.setattr(ai_gateway, "urlopen", raise_url_error)
    assert projects._call_gemini_copilot("some-key", "Acme Corp", "prompt") is None
