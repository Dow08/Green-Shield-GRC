"""controles_techniques.py — rattachement des pratiques relevées aux référentiels (§14.2.4).

Quatre données de mission décrivaient déjà une pratique de sécurité sans jamais
dire à quelle exigence elle répond : `vulnerabilities_active`, `logging_active`,
l'inventaire des biens supports et l'évaluation des fournisseurs. Un booléen
coché ne vaut rien devant un client s'il ne se rattache à rien.

Ce module ne juge pas et ne calcule pas de score : il rapproche un état déjà
saisi ailleurs des contrôles CIS v8 et NIST CSF 2.0 correspondants. La source de
chaque état reste son propriétaire d'origine (phase 2, phase 5, phase 1,
phase 3) — rien n'est dupliqué ici, seulement lu.

Copyright (F3) : identifiants de contrôles et intitulés courts reformulés. CIS
Controls et NIST CSF sont publiés librement, mais la règle du projet reste de ne
jamais recopier un texte normatif.
"""
from __future__ import annotations

# Chaque pratique déclare où lire son état — un seul propriétaire par donnée.
PRATIQUES = (
    {
        "id": "inventaire",
        "libelle": "Inventaire des biens supports tenu sur tout le cycle de vie",
        "phase": 1,
        "phase_libelle": "Cadrage & Patrimoine",
        "mappings": (
            {"referentiel": "NIST CSF 2.0", "ref": "ID.AM", "intitule": "Gestion des actifs"},
            {"referentiel": "CIS v8", "ref": "CIS 1", "intitule": "Inventaire des actifs matériels"},
            {"referentiel": "CIS v8", "ref": "CIS 2", "intitule": "Inventaire des actifs logiciels"},
        ),
    },
    {
        "id": "vulnerabilites",
        "libelle": "Gestion continue des vulnérabilités",
        "phase": 2,
        "phase_libelle": "Diagnostic & RGPD",
        "mappings": (
            {"referentiel": "CIS v8", "ref": "CIS 7", "intitule": "Gestion continue des vulnérabilités"},
            {"referentiel": "NIST CSF 2.0", "ref": "ID.RA-01",
             "intitule": "Vulnérabilités des actifs identifiées et consignées"},
        ),
    },
    {
        "id": "journalisation",
        "libelle": "Journalisation collectée, conservée et exploitable",
        "phase": 5,
        "phase_libelle": "Résilience & E3R",
        "mappings": (
            {"referentiel": "CIS v8", "ref": "CIS 8", "intitule": "Gestion des journaux d'audit"},
        ),
    },
    {
        "id": "evaluation_fournisseurs",
        "libelle": "Fournisseurs évalués avant acquisition",
        "phase": 3,
        "phase_libelle": "Risques Tiers (TPRM)",
        "mappings": (
            {"referentiel": "NIST CSF 2.0", "ref": "ID.RA-10",
             "intitule": "Évaluation des fournisseurs critiques avant acquisition"},
        ),
    },
)

_PAR_ID = {p["id"]: p for p in PRATIQUES}


def _etat_inventaire(steps: dict) -> tuple[bool, str]:
    supports = (steps.get("cadrage") or {}).get("assets_support") or []
    if not supports:
        return False, "Aucun bien support inventorié."
    return True, f"{len(supports)} bien(s) support inventorié(s) en phase 1."


def _etat_vulnerabilites(steps: dict) -> tuple[bool, str]:
    actif = bool((steps.get("diagnostic") or {}).get("vulnerabilities_active"))
    return actif, "Déclaré actif en phase 2." if actif else "Non déclaré en phase 2."


def _etat_journalisation(steps: dict) -> tuple[bool, str]:
    actif = bool((steps.get("resilience") or {}).get("logging_active"))
    return actif, "Déclarée active en phase 5." if actif else "Non déclarée en phase 5."


def _etat_evaluation_fournisseurs(steps: dict) -> tuple[bool, str]:
    """Lu depuis les exigences TPRM du volet GRC, seul endroit où c'est tracé.

    Sur une mission Consulting, l'exigence n'existe pas : la pratique est alors
    « non renseignée », pas « non satisfaite » — l'écart serait inventé.
    """
    tiers = (steps.get("tprm") or {}).get("tiers") or []
    concernes = [t for t in tiers if t.get("exigences")]
    if not concernes:
        return False, "Non tracé : exigence propre au volet GRC."

    evalues = sum(
        1 for t in concernes
        if any(e.get("id") == "NIST-ID.RA-10" and e.get("satisfait") for e in t["exigences"])
    )
    return evalues == len(concernes), f"{evalues} tiers évalué(s) avant acquisition sur {len(concernes)}."


_LECTEURS = {
    "inventaire": _etat_inventaire,
    "vulnerabilites": _etat_vulnerabilites,
    "journalisation": _etat_journalisation,
    "evaluation_fournisseurs": _etat_evaluation_fournisseurs,
}


def referentiel() -> list[dict]:
    """Le rattachement seul, sans état de mission."""
    return [{**p, "mappings": [dict(m) for m in p["mappings"]]} for p in PRATIQUES]


def mappings_de(pratique_id: str) -> list[dict]:
    """Contrôles rattachés à une pratique — pour étiqueter une case à l'écran."""
    pratique = _PAR_ID.get(pratique_id)
    return [dict(m) for m in pratique["mappings"]] if pratique else []


def etat(state: dict) -> dict:
    """État des quatre pratiques pour une mission, avec leurs rattachements."""
    steps = state.get("steps") or {}

    pratiques = []
    for pratique in PRATIQUES:
        couverte, justification = _LECTEURS[pratique["id"]](steps)
        pratiques.append({
            "id": pratique["id"],
            "libelle": pratique["libelle"],
            "phase": pratique["phase"],
            "phase_libelle": pratique["phase_libelle"],
            "couverte": couverte,
            "justification": justification,
            "mappings": [dict(m) for m in pratique["mappings"]],
        })

    couvertes = sum(1 for p in pratiques if p["couverte"])
    return {
        "pratiques": pratiques,
        "couvertes": couvertes,
        "total": len(pratiques),
        "taux": round(couvertes / len(pratiques) * 100) if pratiques else 0,
    }
