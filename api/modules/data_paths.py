"""data_paths.py — résolution unique des emplacements de données hors dépôt.

Les missions et le journal d'audit contiennent des informations client
confidentielles : ils vivent HORS du dépôt git (cf. docs/audit-critique-plan.md,
F13) et hors du répertoire d'installation, pour survivre à une mise à jour de
l'application.

  GREENSHIELD_DATA_DIR : override explicite du répertoire des missions
                         (utilisé par Docker : /data/projects)
  Windows              : %APPDATA%\\GreenShield\\projects
  Linux/macOS          : $XDG_DATA_HOME/greenshield/projects (défaut ~/.local/share)

La « racine de données » est le parent du répertoire des missions : c'est là que
vivent les artefacts non-missions (journal d'audit dans `logs/`).
"""
from __future__ import annotations

import os
from pathlib import Path


def resolve_projects_dir() -> Path:
    override = os.environ.get("GREENSHIELD_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
        return Path(base) / "GreenShield" / "projects"
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "greenshield" / "projects"


def resolve_data_root() -> Path:
    """Racine de données = parent du répertoire des missions."""
    return resolve_projects_dir().parent
