"""auth.py — Sécurisation de l'API.

Gère l'authentification par jeton porteur (Bearer Token).
Lit `GREENSHIELD_API_SECRET` dans l'environnement, sinon génère un token éphémère.
"""
import os
import secrets
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

# Si l'utilisateur n'a pas défini de secret, on en génère un aléatoire à chaque
# démarrage, affiché dans les logs. Cela garantit que l'API n'est jamais ouverte
# par défaut, tout en ne compliquant pas la vie d'un utilisateur solo.
_ENV_SECRET = os.environ.get("GREENSHIELD_API_SECRET", "").strip()

if _ENV_SECRET:
    API_SECRET = _ENV_SECRET
else:
    API_SECRET = secrets.token_hex(16)
    print("\n" + "="*60)
    print("[AUTH] GREEN SHIELD — AUTHENTIFICATION API")
    print("Aucune variable GREENSHIELD_API_SECRET détectée dans l'environnement.")
    print(f"Jeton généré pour cette session : {API_SECRET}")
    print("Utilisez ce jeton pour vous connecter depuis l'interface web.")
    print("="*60 + "\n")

async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> None:
    """Vérifie que le jeton Bearer correspond au secret de l'API.
    
    Lève 401 Unauthorized si le jeton est absent ou invalide.
    Utilisé en dépendance globale ou ciblée.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Non authentifié. Jeton d'accès manquant ou invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validation en temps constant (secrets.compare_digest) pour éviter
    # les attaques temporelles, même si l'outil est local.
    print(f"DEBUG: received='{credentials.credentials}', expected='{API_SECRET}'")
    if not secrets.compare_digest(credentials.credentials, API_SECRET):
        raise HTTPException(
            status_code=401,
            detail="Jeton d'accès incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Utilisé par les tests pour contourner l'authentification
def override_auth():
    pass
