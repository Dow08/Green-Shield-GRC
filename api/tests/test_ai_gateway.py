"""Tests de la passerelle sortante unique vers un LLM (api/modules/ai_gateway.py)."""
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


# --- V-05 (audit combiné du 06/08/2026) : validation de `modele` dans l'URL Gemini
# `modele` est le seul cas où une valeur transite dans l'URL plutôt que dans un
# corps JSON échappé — sans validation, un modèle contenant "/", "?" ou "#"
# pouvait dévier la requête vers un autre chemin/paramètre de la même API.

def test_modele_gemini_avec_caractere_de_chemin_est_refuse(monkeypatch):
    def ne_doit_pas_etre_appele(request, timeout):
        raise AssertionError("urlopen ne doit pas être appelé avec un modèle invalide")

    monkeypatch.setattr(ai_gateway, "urlopen", ne_doit_pas_etre_appele)
    assert ai_gateway.appeler_llm("gemini", "k", "ctx", "prompt", modele="../v1/other") is None


def test_modele_gemini_avec_point_d_interrogation_est_refuse(monkeypatch):
    def ne_doit_pas_etre_appele(request, timeout):
        raise AssertionError("urlopen ne doit pas être appelé avec un modèle invalide")

    monkeypatch.setattr(ai_gateway, "urlopen", ne_doit_pas_etre_appele)
    assert ai_gateway.appeler_llm("gemini", "k", "ctx", "prompt", modele="gemini-2.0-flash?x=1") is None


def test_modele_gemini_legitime_fonctionne_toujours(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return _FakeResponse({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    monkeypatch.setattr(ai_gateway, "urlopen", fake_urlopen)
    result = ai_gateway.appeler_llm("gemini", "k", "ctx", "prompt", modele="gemini-1.5-pro-latest")
    assert result == "ok"
    assert "gemini-1.5-pro-latest:generateContent" in captured["url"]


def test_modele_gemini_par_defaut_reste_valide(monkeypatch):
    """Le modèle par défaut (utilisé quand le client n'en fournit aucun) doit
    lui-même satisfaire la validation — sinon le Copilote basculerait à tort
    hors-ligne sur le cas d'usage le plus courant."""
    assert ai_gateway._MODELE_GEMINI_VALIDE.match(ai_gateway.modele_par_defaut("gemini"))


# --- Passerelle multi-fournisseurs (05/08/2026) -----------------------------
# Les réponses simulées reproduisent le format réel documenté de chaque API :
# une erreur de forme ici signifierait que le code parse la mauvaise structure.

def _capture(payload: dict, captured: dict):
    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.data.decode("utf-8")) if request.data else None
        captured["timeout"] = timeout
        return _FakeResponse(payload)
    return fake_urlopen


def test_ollama_lit_le_contenu_du_message(monkeypatch):
    captured = {}
    monkeypatch.setattr(ai_gateway, "urlopen",
                        _capture({"message": {"content": "Réponse locale"}}, captured))
    assert ai_gateway.appeler_llm("ollama", "", "ctx", "prompt") == "Réponse locale"
    assert captured["url"].startswith("http://127.0.0.1:11434")
    # Sans `stream: False`, Ollama renvoie un flux de lignes JSON illisible.
    assert captured["body"]["stream"] is False


def test_ollama_ne_reclame_aucune_cle(monkeypatch):
    monkeypatch.setattr(ai_gateway, "urlopen",
                        _capture({"message": {"content": "ok"}}, {}))
    assert ai_gateway.appeler_llm("ollama", "", "ctx", "prompt") == "ok"


def test_anthropic_extrait_le_bloc_texte(monkeypatch):
    captured = {}
    payload = {"stop_reason": "end_turn",
               "content": [{"type": "thinking", "thinking": ""},
                           {"type": "text", "text": "Réponse Claude"}]}
    monkeypatch.setattr(ai_gateway, "urlopen", _capture(payload, captured))
    assert ai_gateway.appeler_llm("anthropic", "k", "ctx", "prompt") == "Réponse Claude"
    # En-tête de version obligatoire sur la Messages API.
    assert captured["headers"]["Anthropic-version"] == "2023-06-01"
    assert captured["headers"]["X-api-key"] == "k"


def test_anthropic_renvoie_none_sur_un_refus(monkeypatch):
    # Un refus est un HTTP 200 au contenu vide : lire content[0] lèverait
    # une IndexError au lieu de basculer proprement hors-ligne.
    monkeypatch.setattr(ai_gateway, "urlopen",
                        _capture({"stop_reason": "refusal", "content": []}, {}))
    assert ai_gateway.appeler_llm("anthropic", "k", "ctx", "prompt") is None


def test_openai_et_kimi_partagent_le_meme_format(monkeypatch):
    for fournisseur, hote in (("openai", "api.openai.com"), ("kimi", "api.moonshot.cn")):
        captured = {}
        payload = {"choices": [{"message": {"content": f"Réponse {fournisseur}"}}]}
        monkeypatch.setattr(ai_gateway, "urlopen", _capture(payload, captured))
        assert ai_gateway.appeler_llm(fournisseur, "k", "ctx", "p") == f"Réponse {fournisseur}"
        assert hote in captured["url"]
        assert captured["headers"]["Authorization"] == "Bearer k"


def test_cle_absente_refusee_pour_un_fournisseur_en_ligne(monkeypatch):
    def ne_doit_pas_etre_appele(*a, **k):
        raise AssertionError("aucun appel réseau ne doit partir sans clé")
    monkeypatch.setattr(ai_gateway, "urlopen", ne_doit_pas_etre_appele)
    for fournisseur in ("gemini", "anthropic", "openai", "kimi"):
        assert ai_gateway.appeler_llm(fournisseur, "", "ctx", "prompt") is None


def test_fournisseur_inconnu_ne_declenche_aucun_appel(monkeypatch):
    def ne_doit_pas_etre_appele(*a, **k):
        raise AssertionError("fournisseur inconnu : aucun appel ne doit partir")
    monkeypatch.setattr(ai_gateway, "urlopen", ne_doit_pas_etre_appele)
    assert ai_gateway.appeler_llm("fournisseur-inexistant", "k", "ctx", "p") is None


@pytest.mark.parametrize("fournisseur", ["ollama", "gemini", "anthropic", "openai", "kimi"])
def test_chaque_fournisseur_retombe_sur_none_en_cas_de_panne(monkeypatch, fournisseur):
    def raise_url_error(request, timeout=None):
        raise URLError("no network")
    monkeypatch.setattr(ai_gateway, "urlopen", raise_url_error)
    assert ai_gateway.appeler_llm(fournisseur, "cle", "ctx", "prompt") is None


@pytest.mark.parametrize("fournisseur", ["ollama", "gemini", "anthropic", "openai", "kimi"])
def test_chaque_fournisseur_retombe_sur_none_si_reponse_malformee(monkeypatch, fournisseur):
    monkeypatch.setattr(ai_gateway, "urlopen", _capture({"forme": "inattendue"}, {}))
    assert ai_gateway.appeler_llm(fournisseur, "cle", "ctx", "prompt") is None


def test_le_modele_local_recoit_un_delai_plus_long(monkeypatch):
    delais = {}

    def fake_urlopen(request, timeout=None):
        delais[request.full_url] = timeout
        return _FakeResponse({"message": {"content": "ok"},
                              "choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(ai_gateway, "urlopen", fake_urlopen)
    ai_gateway.appeler_llm("ollama", "", "ctx", "p")
    ai_gateway.appeler_llm("openai", "k", "ctx", "p")
    local = [v for u, v in delais.items() if "11434" in u][0]
    en_ligne = [v for u, v in delais.items() if "openai" in u][0]
    assert local == ai_gateway.TIMEOUT_LOCAL
    assert en_ligne == ai_gateway.TIMEOUT_EN_LIGNE
    assert local > en_ligne


def test_lister_modeles_ollama_renvoie_une_liste_vide_si_absent(monkeypatch):
    # Ollama non lancé : l'interface doit pouvoir le dire, pas planter.
    def raise_url_error(request, timeout=None):
        raise URLError("connection refused")
    monkeypatch.setattr(ai_gateway, "urlopen", raise_url_error)
    assert ai_gateway.lister_modeles_ollama() == []


def test_lister_modeles_ollama_trie_les_noms(monkeypatch):
    payload = {"models": [{"name": "mistral-small:24b"}, {"name": "gemma4:12b"}]}
    monkeypatch.setattr(ai_gateway, "urlopen", _capture(payload, {}))
    assert ai_gateway.lister_modeles_ollama() == ["gemma4:12b", "mistral-small:24b"]
