"""schemas.py — Modèles Pydantic pour la validation des entrées/sorties API.

Lot A de la commercialisation : remplace les `data: dict` non validés par des
structures typées, documentées et auto-publiées dans le Swagger de FastAPI.

Chaque modèle est nommé d'après la route qu'il sert. Les modèles de réponse
ne sont pas systématiques : FastAPI sait sérialiser un dict. On ne type que là
où la clarté (Swagger) ou la sécurité (validation) l'exige.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, TypeVar
import re

T = TypeVar("T", bound=BaseModel)


def coerce(model_class: type[T], data) -> T:
    if isinstance(data, model_class):
        return data
    if isinstance(data, dict):
        try:
            return model_class(**data)
        except Exception as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return data


# ---------------------------------------------------------------------------
#  Auth
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Inscription d'un nouvel utilisateur."""
    email: str = Field(..., min_length=5, max_length=254, examples=["auditeur@cabinet.fr"])
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        # Validation minimale : présence du @ et d'un domaine avec point.
        # Un EmailStr pydantic[email-validator] serait plus strict mais ajoute
        # une dépendance. Ce filtre suffit à rejeter les saisies aberrantes.
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Format d'adresse email invalide.")
        return v


class LoginRequest(BaseModel):
    """Connexion d'un utilisateur existant."""
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Réponse à une connexion réussie."""
    access_token: str
    token_type: str = "bearer"
    is_premium: bool
    email: str


class ActivateLicenseRequest(BaseModel):
    """Activation d'une clé de licence."""
    license_key: str = Field(..., min_length=5, max_length=512)


class UserProfileResponse(BaseModel):
    """Profil de l'utilisateur connecté."""
    email: str
    role: str
    is_premium: bool
    license_key: Optional[str] = None
    plan: str = "free"


# ---------------------------------------------------------------------------
#  Projects
# ---------------------------------------------------------------------------

class CreateProjectRequest(BaseModel):
    """Création d'une nouvelle mission."""
    name: str = Field(..., min_length=1, max_length=200, examples=["Audit ISO 27001 — Acme Corp"])
    client: str = Field(default="Client Anonyme", max_length=200)
    type: Literal["consulting", "grc"] = "consulting"
    framework_id: str = Field(default="iso27001", max_length=100)
    framework_ids: Optional[list[str]] = None


class UpdateRgpdRequest(BaseModel):
    """Mise à jour de la politique RGPD d'une mission."""
    duree_conservation_mois: int = Field(default=36, ge=1, le=120)
    date_fin_mission: Optional[str] = None

    @field_validator("date_fin_mission")
    @classmethod
    def date_format(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            v = v.strip()
            from datetime import date
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("Date de fin de mission invalide (AAAA-MM-JJ)")
            return v
        return None


# ---------------------------------------------------------------------------
#  TPRM
# ---------------------------------------------------------------------------

class AddTiersRequest(BaseModel):
    """Ajout d'un tiers à évaluer."""
    name: str = Field(..., min_length=1, max_length=200)
    dependence: int = Field(default=3, ge=1, le=5)
    penetration: int = Field(default=3, ge=1, le=5)
    maturity: int = Field(default=3, ge=1, le=5)
    trust: int = Field(default=3, ge=1, le=5)


class UpdateExigenceTiersRequest(BaseModel):
    """Mise à jour d'une exigence de conformité d'un tiers."""
    satisfait: bool = False
    preuve: Optional[str] = Field(default="", max_length=500)


# ---------------------------------------------------------------------------
#  Temps
# ---------------------------------------------------------------------------

PHASES_TEMPS_VALIDES = ("cadrage", "diagnostic", "tprm", "ebios", "resilience", "traitement", "autre")


class AddTempsRequest(BaseModel):
    """Ajout d'une entrée de temps consommé."""
    phase: str = Field(default="autre")
    minutes: int = Field(..., gt=0, le=1440)  # max 24h
    date: Optional[str] = None
    note: Optional[str] = Field(default="")

    @field_validator("phase")
    @classmethod
    def phase_valide(cls, v: str) -> str:
        if v not in PHASES_TEMPS_VALIDES:
            raise ValueError(f"Phase inconnue : {v}. Valeurs autorisées : {', '.join(PHASES_TEMPS_VALIDES)}")
        return v


# ---------------------------------------------------------------------------
#  Copilot (mission)
# ---------------------------------------------------------------------------

class CopilotMissionRequest(BaseModel):
    """Requête au copilote IA dans le contexte d'une mission."""
    prompt: str = Field(..., min_length=1, max_length=5000)
    key: Optional[str] = Field(default="", max_length=256)


# ---------------------------------------------------------------------------
#  Archive
# ---------------------------------------------------------------------------

class ExportArchiveRequest(BaseModel):
    """Export d'une mission en archive chiffrée."""
    password: str = Field(..., min_length=4, max_length=128)


# ---------------------------------------------------------------------------
#  Frameworks
# ---------------------------------------------------------------------------

class ExigenceImport(BaseModel):
    """Une exigence dans un référentiel importé."""
    id: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default="", max_length=2000)


class ImportFrameworkRequest(BaseModel):
    """Import ou création d'un référentiel personnel."""
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)
    requirements: list[ExigenceImport] = Field(default_factory=list)


# ---------------------------------------------------------------------------
#  Export DOCX (identité de l'auditeur)
# ---------------------------------------------------------------------------

class DocxExportRequest(BaseModel):
    """Identité de l'auditeur pour la personnalisation du livrable Word."""
    auditeur: str = Field(default="", max_length=200)
    cabinet: str = Field(default="", max_length=200)
    logo: str = Field(default="", max_length=500_000)  # base64 du logo PNG/JPEG


# ---------------------------------------------------------------------------
#  Copilot GRC (transverse, hors mission)
# ---------------------------------------------------------------------------

class CopilotAskRequest(BaseModel):
    """Requête au copilote GRC transverse."""
    prompt: str = Field(..., min_length=1, max_length=5000)
    key: str = Field(default="", max_length=256)


# ---------------------------------------------------------------------------
#  Collecte technique
# ---------------------------------------------------------------------------

class FingerprintRequest(BaseModel):
    """Analyse d'un fichier de configuration."""
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=500_000)


class ImportAssetRequest(BaseModel):
    """Import d'un actif suggéré par la collecte technique."""
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="Logiciel", max_length=100)
    description: str = Field(default="", max_length=500)
    owner: str = Field(default="", max_length=200)


# ---------------------------------------------------------------------------
#  Copilot Project Generation
# ---------------------------------------------------------------------------

class CopilotGenerateProjectRequest(BaseModel):
    """Génération d'une mission par le copilote."""
    prompt: str = Field(..., min_length=1, max_length=2000)


# ---------------------------------------------------------------------------
#  Connecteurs
# ---------------------------------------------------------------------------

class ConnectorScanRequest(BaseModel):
    """Lancement d'un scan via connecteur."""
    connector_id: str = Field(..., min_length=1, max_length=100)
    credentials: Optional[dict] = None
