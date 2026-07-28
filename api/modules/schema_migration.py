"""Versionnement du schéma des missions et chaîne de migration.

Le schéma de `project.json` va encore évoluer (volet Consulting au jalon 2,
référentiels complémentaires au jalon 3). Un script de migration unique ne suffit
donc pas : il faut une **chaîne** ordonnée, rejouable, qui amène une mission de
n'importe quelle version passée à la version courante (cf. docs/audit-critique-plan.md, F4).

Règles :
  * une migration n'efface jamais une donnée — elle ajoute ou déplace ;
  * une mission déjà à jour traverse la chaîne sans être modifiée ;
  * une mission sans `schema_version` est réputée en version 1 (état d'avant le jalon 1).
"""
from __future__ import annotations

from typing import Callable

CURRENT_SCHEMA_VERSION = 2


def _to_v2(state: dict) -> dict:
    """v1 → v2 : introduction du socle commun et du volet GRC structuré.

    Le socle rassemble ce qui est commun aux deux volets (qualification, cadrage
    contractuel, entretiens). Les données de cadrage déjà saisies restent à leur
    place historique dans `steps.cadrage` : elles sont référencées, pas recopiées,
    pour qu'il n'existe jamais deux vérités pour un même champ.
    """
    socle = state.setdefault("socle", {})
    socle.setdefault("qualification", {
        "declencheur": "",
        "sponsor_executif": "",
        "budget": "",
        "maturite_actuelle": "",
        "equipe_interne": "",
        "echeance_cible": "",
    })
    socle.setdefault("contractualisation", {
        "perimetre_inclus": "",
        "perimetre_exclu": "",
        "livrables": [],
        "modalites": "",
        "acces_si": "",
    })
    socle.setdefault("kickoff", {
        "date": "",
        "participants": [],
        "gouvernance": "",
    })
    socle.setdefault("entretiens", [])

    grc = state.setdefault("grc", {})
    grc.setdefault("active", state.get("type") == "grc")
    fw = (state.get("steps", {}).get("cadrage", {}) or {}).get("framework_id")
    grc.setdefault("referentiels_actifs", [fw] if fw else [])
    # Avancement des parcours référentiels : {referentiel: {etape_id: {...}}}
    grc.setdefault("parcours", {})

    consulting = state.setdefault("consulting", {})
    consulting.setdefault("active", state.get("type") != "grc")

    return state


# Chaîne ordonnée : version cible -> fonction qui y amène.
_MIGRATIONS: list[tuple[int, Callable[[dict], dict]]] = [
    (2, _to_v2),
]


def migrate(state: dict) -> dict:
    """Amène une mission à la version courante du schéma."""
    version = int(state.get("schema_version", 1))
    for target, migration in _MIGRATIONS:
        if version < target:
            state = migration(state)
            version = target
    state["schema_version"] = version
    return state


def needs_migration(state: dict) -> bool:
    return int(state.get("schema_version", 1)) < CURRENT_SCHEMA_VERSION
