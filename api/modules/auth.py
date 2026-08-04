"""auth.py — Sécurisation de l'API avec JWT et SQLAlchemy.

Audit du 01/08/2026 :
  * le secret par défaut en dur ("super-secret-key-for-dev") permettait la
    forgerie de tokens à quiconque lisant le dépôt — remplacé par une
    génération aléatoire au démarrage si GREENSHIELD_API_SECRET est vide ;
  * `verify_token` (no-op) et `override_auth` supprimés — les tests utilisent
    désormais `get_current_user` comme dépendance à surcharger ;
  * `datetime.utcnow()` remplacé par `datetime.now(timezone.utc)` (déprécié
    depuis Python 3.12) ;
  * ajout d'une validation de force de mot de passe (`validate_password`).
"""
from __future__ import annotations

import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from . import data_paths
from .database.session import get_db
from .database.models import User

_log = logging.getLogger("greenshield.auth")

security = HTTPBearer(auto_error=False)

# Limiteur de débit partagé (défini ici plutôt que dans main.py pour être
# importable par auth_routes.py sans import circulaire). Le monter avec
# `SlowAPIMiddleware` ne suffit pas : `default_limits` ne s'applique qu'aux
# routes explicitement décorées `@limiter.limit(...)` — corrigé le
# 31/07/2026, le limiteur était instancié mais n'agissait sur aucune route,
# `/api/auth/login` compris (bruteforce non freiné).
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

def _secret_persistant() -> str:
    """Secret JWT stable entre deux démarrages.

    Recette du 31/07/2026 : le secret était régénéré à chaque démarrage
    (`secrets.token_hex(32)`), ce qui invalidait **tous** les tokens déjà
    émis. Symptôme constaté : « Token invalide » sur toute l'application
    après un simple redémarrage du serveur, sans possibilité de s'en sortir.

    Le secret est donc généré une seule fois puis conservé dans la racine de
    données (hors du dépôt, comme les missions — F13). Il y vit en clair,
    sur un disque dont le chiffrement est déjà un prérequis d'exploitation
    documenté (F15) ; c'est strictement plus sûr que l'ancien secret en dur,
    et utilisable là où l'ancien comportement rendait l'outil inutilisable.
    """
    chemin = data_paths.resolve_data_root() / ".jwt_secret"
    try:
        if chemin.is_file():
            existant = chemin.read_text(encoding="utf-8").strip()
            if existant:
                return existant
    except OSError as exc:
        _log.warning("Secret JWT illisible (%s) — secret volatil pour cette session.", exc)
        return secrets.token_hex(32)

    nouveau = secrets.token_hex(32)
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(nouveau, encoding="utf-8")
        # Lecture réservée au propriétaire quand la plateforme le permet.
        try:
            os.chmod(chemin, 0o600)
        except (OSError, NotImplementedError):
            pass
    except OSError as exc:
        _log.warning(
            "Secret JWT non persistable (%s) — les sessions ne survivront pas "
            "au redémarrage.", exc
        )
    return nouveau


# La variable d'environnement reste prioritaire (déploiement Docker) ; sinon
# on retombe sur le secret persistant du poste.
_env_secret = (os.environ.get("GREENSHIELD_API_SECRET") or "").strip()
SECRET_KEY = _env_secret or _secret_persistant()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60

# Règles de mot de passe : min 8 caractères, au moins 1 majuscule, 1 chiffre.
MIN_PASSWORD_LENGTH = 8
_PASSWORD_UPPER = re.compile(r"[A-Z]")
_PASSWORD_DIGIT = re.compile(r"\d")


def validate_password(password: str) -> None:
    """Vérifie la force d'un mot de passe. Lève HTTPException 400 si trop faible."""
    erreurs: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        erreurs.append(f"au moins {MIN_PASSWORD_LENGTH} caractères")
    if not _PASSWORD_UPPER.search(password):
        erreurs.append("au moins une lettre majuscule")
    if not _PASSWORD_DIGIT.search(password):
        erreurs.append("au moins un chiffre")
    if erreurs:
        raise HTTPException(
            status_code=400,
            detail=f"Mot de passe trop faible : {', '.join(erreurs)}.",
        )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Non authentifié. Jeton d'accès manquant ou invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user
