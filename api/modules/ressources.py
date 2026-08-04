"""ressources.py — localisation des fichiers livrés avec l'application.

Les référentiels (`frameworks/*.yaml`) et le frontend compilé sont des
ressources **embarquées** : elles accompagnent le programme, contrairement aux
missions qui vivent hors du dépôt (cf. `data_paths.py`).

Leur emplacement change selon le mode d'exécution :

  * depuis les sources, elles sont à côté du code (`api/frameworks/`) ;
  * dans l'exécutable Windows, PyInstaller les extrait dans un répertoire
    temporaire dont il donne le chemin via `sys._MEIPASS`.

Sans ce point de passage unique, l'exécutable démarre puis échoue à la
première lecture de référentiel — le répertoire `frameworks/` n'existant pas
à côté du `.exe`.
"""
from __future__ import annotations

import sys
from pathlib import Path


def racine_application() -> Path:
    """Répertoire contenant les ressources embarquées (`frameworks/`, `web/`)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:  # exécutable PyInstaller
        return Path(base)
    # Depuis les sources : `api/`, parent de ce module.
    return Path(__file__).resolve().parent.parent


def frameworks_dir() -> Path:
    return racine_application() / "frameworks"


def frontend_dir() -> Path:
    """Frontend compilé, présent uniquement dans l'exécutable de bureau.

    En développement, Vite le sert lui-même ; en Docker, c'est nginx. Le
    répertoire est donc légitimement absent dans ces deux cas.
    """
    return racine_application() / "web"


def est_execute_depuis_un_binaire() -> bool:
    return bool(getattr(sys, "frozen", False))
