"""path_safety.py — validation unique des segments de chemin disque construits
à partir d'une entrée utilisateur (identifiant de mission, de référentiel, nom
de fichier importé...).

Découvert lors de l'audit combiné du 28/07/2026 : plusieurs endpoints
construisaient un chemin disque directement à partir d'une valeur fournie par
le client (p_id, fw_id, nom de fichier uploadé) sans aucune validation,
ouvrant un path traversal exploitable — ex: p_id=".." fait résoudre
`PROJECTS_DIR / ".."` vers le répertoire PARENT de PROJECTS_DIR, exploitable
via `DELETE /api/projects/..` pour détruire toutes les missions. Point de
passage unique désormais obligatoire pour toute valeur qui alimente une
jointure de chemin.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException


def safe_path_component(value: str, field_name: str = "identifiant") -> str:
    """Valide qu'une valeur peut servir sans risque de segment de chemin
    disque unique (identifiant de mission, de référentiel...).

    Autorise les lettres/chiffres Unicode (ex: « cassiopé », identifiants déjà
    en usage réel — `isalnum()` est volontairement Unicode-aware, comme le
    filtre déjà utilisé par `create_project`), `_` et `-` ; rejette tout le
    reste — en particulier `.`, `/` et `\\`, ce qui bloque par construction
    toute séquence `..` et tout séparateur de chemin, sans avoir besoin de
    les détecter explicitement. Lève HTTPException 400 sinon.
    """
    if value and all(c.isalnum() or c in "_-" for c in value):
        return value
    raise HTTPException(status_code=400, detail=f"{field_name} invalide : caractères non autorisés")


def safe_filename(filename: str | None) -> str:
    """Réduit un nom de fichier fourni par le client à son seul nom de base
    (aucun composant de répertoire), et rejette les cas dégénérés ('', '.',
    '..'). À utiliser pour tout fichier reçu via upload multipart : le nom
    original du fichier est entièrement contrôlé par le client."""
    name = Path(filename or "").name
    if not name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    return name
