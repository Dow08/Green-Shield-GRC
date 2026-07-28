"""ai_gateway.py — passerelle sortante unique vers un LLM en ligne (Gemini).

Point de passage unique pour tout appel réseau vers un fournisseur de LLM :
GREEN SHIELD reste 100 % hors-ligne par défaut (cf. REFERENTIEL.md) ; ce module
n'est sollicité que si le consultant a explicitement saisi sa propre clé d'API
dans les Réglages. Toute erreur (réseau, clé invalide, quota, format de réponse
inattendu) renvoie None pour laisser l'appelant basculer silencieusement sur
l'intelligence experte locale — jamais d'exception qui casserait le Copilote.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

_GEMINI_MODEL = "gemini-2.0-flash"
_GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent"


def call_gemini(api_key: str, system_context: str, user_prompt: str, timeout: int = 20) -> str | None:
    """Appelle Gemini avec la clé fournie par le consultant. Renvoie le texte
    généré, ou None en cas d'échec quel qu'il soit."""
    payload = {
        "contents": [{"parts": [{"text": f"{system_context}\n\nDemande du consultant : {user_prompt}"}]}]
    }
    request = Request(
        f"{_GEMINI_URL}?key={quote(api_key)}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (URLError, HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None
