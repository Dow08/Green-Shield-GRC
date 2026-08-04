"""soa.py — Déclaration d'Applicabilité ISO/IEC 27001:2022 Annexe A.

Manque identifié en revue GRC senior le 30/07/2026 : sans SoA, une mission
ISO 27001 ne peut pas passer un audit de certification — c'est le document
que l'auditeur externe demande en premier, il justifie l'inclusion *et*
l'exclusion de chacun des 93 contrôles de l'Annexe A (clause 6.1.3 d).

Le catalogue (code, intitulé court, thème) est importé du skill Hermes de
l'utilisateur — aucun texte normatif ISO n'est recopié (F3), seulement des
identifiants et intitulés reformulés courts, déjà au format retenu par
`api/frameworks/iso27001.yaml`.

Zéro invention : `applicable` démarre à `None` (non statué), jamais à `Oui`.
Un consultant qui n'a pas encore tranché ne doit jamais voir 93 décisions
qu'il n'a pas prises s'afficher comme si elles l'étaient.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from . import ressources

_CATALOGUE_PATH = ressources.frameworks_dir() / "soa_iso27001.yaml"

STATUTS = ("Implémenté", "Partiel", "Planifié")
THEMES = ("Organisationnel", "Personnel", "Physique", "Technologique")


def catalogue() -> list[dict]:
    """Les 93 contrôles de l'Annexe A 2022, structure seule (code/titre/thème)."""
    data = yaml.safe_load(_CATALOGUE_PATH.read_text(encoding="utf-8"))
    return data["controles"]


def entrees_par_defaut() -> list[dict]:
    """Les 93 entrées de la SoA, aucune décision d'applicabilité prise."""
    return [
        {
            "code": c["code"], "titre": c["titre"], "theme": c["theme"],
            "applicable": None, "statut": None, "justification": "",
            "document_reference": "", "owner": "", "date_revue": "",
        }
        for c in catalogue()
    ]


def par_theme(soa: list[dict]) -> list[dict]:
    """Synthèse par thème — c'est cette vue condensée qui figure dans le
    rapport de mission ; le détail des 93 lignes reste dans le livrable SoA
    dédié, où il a sa place."""
    resultat = []
    for theme in THEMES:
        entrees = [c for c in soa if c.get("theme") == theme]
        resultat.append({
            "theme": theme,
            "total": len(entrees),
            "applicables": sum(1 for c in entrees if c.get("applicable") is True),
            "exclus": sum(1 for c in entrees if c.get("applicable") is False),
            "non_statues": sum(1 for c in entrees if c.get("applicable") is None),
        })
    return resultat


def etat(soa: list[dict]) -> dict:
    """Avancement de la SoA : combien de contrôles ont reçu une décision
    d'applicabilité, indépendamment du sens de cette décision."""
    total = len(soa)
    statues = sum(1 for c in soa if c.get("applicable") is not None)
    applicables = sum(1 for c in soa if c.get("applicable") is True)
    exclus = sum(1 for c in soa if c.get("applicable") is False)
    return {
        "total": total,
        "statues": statues,
        "non_statues": total - statues,
        "applicables": applicables,
        "exclus": exclus,
        "taux": round(statues / total * 100) if total else 0,
        "complete": total > 0 and statues == total,
    }
