"""Tests de la passerelle sortante unique vers Gemini (api/modules/ai_gateway.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import ai_gateway  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_call_gemini_retourne_le_texte_genere(monkeypatch):
    def fake_urlopen(request, timeout):
        return _FakeResponse({"candidates": [{"content": {"parts": [{"text": "Réponse Gemini"}]}}]})

    monkeypatch.setattr(ai_gateway, "urlopen", fake_urlopen)
    result = ai_gateway.call_gemini("some-key", "contexte système", "prompt")
    assert result == "Réponse Gemini"


def test_call_gemini_renvoie_none_sur_erreur_reseau(monkeypatch):
    def raise_url_error(request, timeout):
        raise URLError("no network")

    monkeypatch.setattr(ai_gateway, "urlopen", raise_url_error)
    assert ai_gateway.call_gemini("some-key", "ctx", "prompt") is None


def test_call_gemini_renvoie_none_sur_cle_invalide(monkeypatch):
    def raise_http_error(request, timeout):
        raise HTTPError(url="", code=400, msg="API key not valid", hdrs=None, fp=None)

    monkeypatch.setattr(ai_gateway, "urlopen", raise_http_error)
    assert ai_gateway.call_gemini("bad-key", "ctx", "prompt") is None


def test_call_gemini_renvoie_none_si_reponse_malformee(monkeypatch):
    def fake_urlopen(request, timeout):
        return _FakeResponse({"unexpected": "shape"})

    monkeypatch.setattr(ai_gateway, "urlopen", fake_urlopen)
    assert ai_gateway.call_gemini("some-key", "ctx", "prompt") is None


def test_call_gemini_transmet_la_cle_dans_l_url(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return _FakeResponse({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    monkeypatch.setattr(ai_gateway, "urlopen", fake_urlopen)
    ai_gateway.call_gemini("ma-cle-secrete", "ctx", "prompt")
    assert "ma-cle-secrete" in captured["url"]
