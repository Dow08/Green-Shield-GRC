"""audit_log.py — journal d'audit des actions sensibles.

Répond au constat de l'audit du 28/07/2026 : aucune trace n'existait de qui
avait créé, modifié, exporté ou **supprimé** une mission. Pour un outil qui
vend de la traçabilité GRC à ses clients, c'était un angle mort.

Ce que ce journal enregistre : l'action, la mission concernée (identifiant),
le résultat, et un détail court non sensible (ex : nom du fichier importé,
type de document exporté).

Ce qu'il n'enregistre JAMAIS : le contenu des missions — constats
d'audit, vulnérabilités relevées, données personnelles des personnes
interrogées, texte des prompts envoyés au Copilote. L'identifiant de mission
est le seul élément potentiellement nominatif, et il est indispensable à la
traçabilité ; le journal vit dans le répertoire de données, couvert par la
même exigence de chiffrement de disque que les missions (F15).

Robustesse : aucune écriture de journal ne peut faire échouer une opération
métier. Si le disque est plein ou en lecture seule, l'action réussit quand
même et le journal est silencieusement ignoré.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from . import data_paths

_LOGGER_NAME = "greenshield.audit"
_MAX_BYTES = 1_000_000  # ~1 Mo par fichier
_BACKUP_COUNT = 5       # 5 rotations conservées

_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger | None:
    """Initialise le logger à la première utilisation. Renvoie None si le
    journal ne peut pas être ouvert (disque plein, droits insuffisants) —
    l'appelant doit alors simplement continuer sans journaliser."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    # Journal d'audit autonome : il ne doit pas remonter dans la configuration
    # de logging de l'application hôte (uvicorn), ni polluer la sortie console.
    logger.propagate = False

    if not logger.handlers:
        try:
            log_dir = data_paths.resolve_data_root() / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                log_dir / "audit.log",
                maxBytes=_MAX_BYTES,
                backupCount=_BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
            logger.addHandler(handler)
        except OSError:
            return None

    _logger = logger
    return _logger


def record(action: str, target: str = "-", outcome: str = "ok", detail: str = "") -> None:
    """Journalise une action sensible. Ne lève jamais d'exception.

    action  : verbe court et stable (ex: "project.delete", "framework.import")
    target  : identifiant de la ressource concernée (id de mission, id de référentiel)
    outcome : "ok" | "denied" | "error"
    detail  : complément court NON SENSIBLE (nom de fichier, type de document)
    """
    try:
        logger = _get_logger()
        if logger is None:
            return
        message = f"{action} | target={target} | outcome={outcome}"
        if detail:
            message += f" | {detail}"
        logger.info(message)
    except Exception:
        # Le journal ne doit jamais casser une opération métier.
        pass
