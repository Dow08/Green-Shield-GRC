"""Chargement des parcours méthodologiques (`workflow.yaml`).

Source unique alimentant 3 vues distinctes (cf. docs/spec-refonte-grc-consulting.md §10.3, §13.1) :
  * Kanban            — colonnes = macro_phases, cartes = etapes
  * Agenda            — jour_relatif / duree converti en dates réelles
  * Grille d'entretien — role_a_rencontrer + questions[] par étape

Ajouter un référentiel devient un fichier YAML posé dans `api/frameworks/<id>/workflow.yaml` :
aucune modification de code n'est nécessaire (cf. audit F2 — le contenu se
planifie séparément du code).
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from . import ressources

import yaml

from . import path_safety

FRAMEWORKS_DIR = ressources.frameworks_dir()


def list_workflow_ids() -> list[str]:
    """Référentiels disposant d'un parcours structuré (par opposition aux
    référentiels qui n'ont encore qu'une checklist d'exigences plates)."""
    if not FRAMEWORKS_DIR.is_dir():
        return []
    return sorted(
        d.name for d in FRAMEWORKS_DIR.iterdir()
        if d.is_dir() and (d / "workflow.yaml").is_file()
    )


def load_workflow(referentiel_id: str) -> dict:
    """Charge et valide a minima un workflow.yaml."""
    referentiel_id = path_safety.safe_path_component(referentiel_id, "identifiant de référentiel")
    path = FRAMEWORKS_DIR / referentiel_id / "workflow.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Aucun workflow pour le référentiel « {referentiel_id} »")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "macro_phases" not in data or not isinstance(data["macro_phases"], list):
        raise ValueError(f"{path} invalide : clé 'macro_phases' (liste) manquante")

    for phase in data["macro_phases"]:
        for cle in ("id", "titre", "etapes"):
            if cle not in phase:
                raise ValueError(f"{path} invalide : macro_phase sans '{cle}'")

    return data


def resolve_agenda(workflow: dict, date_demarrage: date) -> list[dict]:
    """Convertit les jour_relatif en dates réelles à partir du jour 1 du projet.

    jour_relatif=1 correspond au jour de démarrage lui-même (cohérent avec la
    convention Hermes « Réunion de lancement (jour 1) »), pas J+1.
    """
    agenda: list[dict] = []
    for phase in workflow.get("macro_phases", []):
        for etape in phase.get("etapes", []):
            jour = etape.get("jour_relatif")
            if jour is None:
                continue
            agenda.append({
                "macro_phase_id": phase["id"],
                "macro_phase_titre": phase["titre"],
                "etape_id": etape["id"],
                "etape_titre": etape["titre"],
                "date": (date_demarrage + timedelta(days=jour - 1)).isoformat(),
                "duree": etape.get("duree", ""),
                "role_a_rencontrer": etape.get("role_a_rencontrer", []),
            })
    agenda.sort(key=lambda item: item["date"])
    return agenda
