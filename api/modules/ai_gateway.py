"""ai_gateway.py — passerelle sortante unique vers un LLM.

Point de passage unique pour tout appel vers un modèle de langage, local ou
en ligne. GREEN SHIELD reste hors-ligne par défaut : ce module n'est sollicité
que si le consultant a explicitement choisi un fournisseur dans les Réglages.
Toute erreur (réseau, clé invalide, quota, format inattendu) renvoie None pour
laisser l'appelant basculer sur l'intelligence experte locale — jamais
d'exception qui casserait le Copilote.

Cinq fournisseurs :

  * ollama    — 100 % local (127.0.0.1:11434), aucune clé, aucune sortie réseau
  * gemini    — Google
  * anthropic — Claude
  * openai    — ChatGPT
  * kimi      — Moonshot (API compatible OpenAI)

Appels en HTTP brut via `urllib` plutôt qu'avec les SDK officiels : cinq SDK
pour cinq fournisseurs alourdiraient l'exécutable PyInstaller et contrediraient
la règle « stdlib autant que possible » du projet. Le format de chaque requête
suit la documentation officielle du fournisseur concerné.

La clé n'est jamais journalisée, jamais stockée côté serveur : elle transite
en mémoire le temps de l'appel et repart avec la réponse.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

FOURNISSEURS = ("ollama", "gemini", "anthropic", "openai", "kimi")

# Fournisseurs ne nécessitant aucune clé : Ollama tourne sur la machine du
# consultant, il n'y a personne à authentifier.
FOURNISSEURS_LOCAUX = ("ollama",)

OLLAMA_URL = "http://127.0.0.1:11434"

# Un modèle local tourne sur le processeur du poste : il lui faut des minutes
# là où une API en ligne répond en secondes.
TIMEOUT_LOCAL = 300
TIMEOUT_EN_LIGNE = 60

_MODELES_PAR_DEFAUT = {
    "ollama": "mistral",
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-opus-5",
    "openai": "gpt-4o",
    "kimi": "moonshot-v1-8k",
}

# Erreurs de transport et de désérialisation traitées identiquement : dans tous
# les cas l'appelant doit basculer hors-ligne, pas afficher une trace.
_ERREURS = (URLError, HTTPError, KeyError, IndexError, TypeError, ValueError,
            json.JSONDecodeError)


def modele_par_defaut(fournisseur: str) -> str:
    return _MODELES_PAR_DEFAUT.get(fournisseur, "")


def _poster_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _appeler_ollama(system_context: str, user_prompt: str, modele: str, timeout: int) -> str | None:
    """Modèle local via Ollama. Aucune donnée ne quitte la machine.

    `stream: False` est indispensable : par défaut Ollama renvoie un flux de
    lignes JSON, illisible pour `json.loads` en une passe.
    """
    body = _poster_json(
        f"{OLLAMA_URL}/api/chat",
        {
            "model": modele,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_prompt},
            ],
        },
        {},
        timeout,
    )
    return body["message"]["content"]


def _appeler_gemini(api_key: str, system_context: str, user_prompt: str, modele: str, timeout: int) -> str | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
    body = _poster_json(
        f"{url}?key={quote(api_key)}",
        {"contents": [{"parts": [{"text": f"{system_context}\n\nDemande du consultant : {user_prompt}"}]}]},
        {},
        timeout,
    )
    return body["candidates"][0]["content"]["parts"][0]["text"]


def _appeler_anthropic(api_key: str, system_context: str, user_prompt: str, modele: str, timeout: int) -> str | None:
    """Messages API d'Anthropic.

    `anthropic-version` est un en-tête obligatoire, pas optionnel. La réponse
    est une LISTE de blocs typés : on filtre sur `type == "text"` plutôt que de
    lire `content[0]`, qui peut être un bloc de raisonnement sur les modèles
    récents. `stop_reason == "refusal"` renvoie un HTTP 200 avec un contenu
    vide : sans ce test, l'accès au premier bloc lèverait une IndexError.
    """
    body = _poster_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": modele,
            "max_tokens": 4096,
            "system": system_context,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout,
    )
    if body.get("stop_reason") == "refusal":
        return None
    return next(bloc["text"] for bloc in body["content"] if bloc.get("type") == "text")


def _appeler_openai_compatible(url: str, api_key: str, system_context: str,
                               user_prompt: str, modele: str, timeout: int) -> str | None:
    """OpenAI et Moonshot (Kimi) exposent le même format de requête et de
    réponse — un seul appelant pour les deux, seule l'URL de base change."""
    body = _poster_json(
        url,
        {
            "model": modele,
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_prompt},
            ],
        },
        {"Authorization": f"Bearer {api_key}"},
        timeout,
    )
    return body["choices"][0]["message"]["content"]


def appeler_llm(fournisseur: str, api_key: str, system_context: str, user_prompt: str,
                modele: str | None = None, timeout: int | None = None) -> str | None:
    """Appelle le fournisseur choisi. Renvoie le texte généré, ou None sur
    n'importe quel échec (réseau, clé, quota, refus, format inattendu).

    Le délai dépend du fournisseur : une API en ligne répond en quelques
    secondes, un modèle local sur CPU met beaucoup plus longtemps. Mesuré le
    05/08/2026 sur ce poste : 113 s pour deux phrases avec `gemma4:12b`. Un
    délai unique de 60 s aurait fait échouer l'appel local alors que le modèle
    répondait correctement.
    """
    fournisseur = (fournisseur or "").strip().lower()
    if fournisseur not in FOURNISSEURS:
        return None

    api_key = (api_key or "").strip()
    if not api_key and fournisseur not in FOURNISSEURS_LOCAUX:
        return None

    modele = (modele or "").strip() or modele_par_defaut(fournisseur)
    if timeout is None:
        timeout = TIMEOUT_LOCAL if fournisseur in FOURNISSEURS_LOCAUX else TIMEOUT_EN_LIGNE

    try:
        if fournisseur == "ollama":
            return _appeler_ollama(system_context, user_prompt, modele, timeout)
        if fournisseur == "gemini":
            return _appeler_gemini(api_key, system_context, user_prompt, modele, timeout)
        if fournisseur == "anthropic":
            return _appeler_anthropic(api_key, system_context, user_prompt, modele, timeout)
        if fournisseur == "openai":
            return _appeler_openai_compatible(
                "https://api.openai.com/v1/chat/completions",
                api_key, system_context, user_prompt, modele, timeout)
        if fournisseur == "kimi":
            return _appeler_openai_compatible(
                "https://api.moonshot.cn/v1/chat/completions",
                api_key, system_context, user_prompt, modele, timeout)
    except _ERREURS:
        return None
    except StopIteration:
        # Réponse Anthropic sans aucun bloc de texte exploitable.
        return None
    return None


def lister_modeles_ollama(timeout: int = 3) -> list[str]:
    """Modèles réellement installés localement, pour l'écran de Réglages.

    Sert aussi de test de présence : une liste vide signifie qu'Ollama n'est
    pas lancé, ce que l'interface annonce plutôt que de laisser l'utilisateur
    saisir un nom de modèle qui échouera à l'appel.
    """
    try:
        with urlopen(Request(f"{OLLAMA_URL}/api/tags"), timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return sorted(m["name"] for m in body.get("models", []) if m.get("name"))
    except _ERREURS:
        return []


def call_gemini(api_key: str, system_context: str, user_prompt: str, timeout: int = 20) -> str | None:
    """Conservé pour les appelants historiques (Copilote de mission et de
    portefeuille) tant qu'ils n'ont pas migré vers `appeler_llm`."""
    return appeler_llm("gemini", api_key, system_context, user_prompt, timeout=timeout)
