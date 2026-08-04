"""Catalogue de mesures de sécurité réutilisable (décision G3, cf. spec §14.1).

Une mesure est rédigée une seule fois dans `frameworks/mesures_catalogue.yaml`
et référencée par son id partout où elle est utile : plan de traitement d'une
mission, quick wins, compléments NIS2/DORA/RGPD (Jalon 3). Sans ce catalogue,
les mêmes mesures auraient été recopiées en dur dans 5 parcours différents,
puis désynchronisées dès la première correction.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from . import ressources

CATALOGUE_PATH = ressources.frameworks_dir() / "mesures_catalogue.yaml"

AXES_VALIDES = {"Gouvernance", "Protection", "Défense", "Résilience"}


def load_catalogue() -> dict:
    """Charge et valide a minima le catalogue."""
    if not CATALOGUE_PATH.is_file():
        raise FileNotFoundError(f"Catalogue introuvable : {CATALOGUE_PATH}")

    data = yaml.safe_load(CATALOGUE_PATH.read_text(encoding="utf-8")) or {}
    mesures = data.get("mesures")
    if not isinstance(mesures, list) or not mesures:
        raise ValueError(f"{CATALOGUE_PATH} invalide : clé 'mesures' (liste non vide) manquante")

    vus: set[str] = set()
    for mesure in mesures:
        for cle in ("id", "titre", "axe"):
            if cle not in mesure:
                raise ValueError(f"{CATALOGUE_PATH} invalide : mesure sans '{cle}' ({mesure})")
        if mesure["axe"] not in AXES_VALIDES:
            raise ValueError(f"Axe invalide « {mesure['axe']} » pour {mesure['id']} — attendu parmi {AXES_VALIDES}")
        if mesure["id"] in vus:
            raise ValueError(f"Identifiant de mesure dupliqué : {mesure['id']}")
        vus.add(mesure["id"])

    return data


def list_mesures() -> list[dict]:
    return load_catalogue()["mesures"]


def get_mesure(mesure_id: str) -> dict | None:
    return next((m for m in list_mesures() if m["id"] == mesure_id), None)


def mesures_par_axe(axe: str) -> list[dict]:
    return [m for m in list_mesures() if m["axe"] == axe]


def mesures_pour_referentiel(referentiel_id: str) -> list[dict]:
    """Mesures dont le mapping cite le référentiel donné (ex: 'nis2', 'iso27001').

    Sert notamment au Jalon 3 : construire le plan de mise en conformité NIS2/DORA
    à partir des mesures déjà rédigées, plutôt que d'en écrire de nouvelles.
    """
    return [m for m in list_mesures() if referentiel_id in (m.get("mappings") or {})]
