"""couverture.py — taux de contrôles appuyés par une preuve technique (F10).

L'audit critique relève que la promesse « preuve technique réelle plutôt que
déclaratif » est vraie mais **partielle** : le moteur de règles ne couvre qu'une
poignée de contrôles. Deux réactions possibles — la taire, ou l'afficher.

Afficher est à la fois plus honnête et plus différenciant : aucune plateforme
GRC concurrente ne dit au client quelle proportion de son audit repose sur une
mesure automatisée plutôt que sur du déclaratif. Ce module calcule ce taux à
partir des données réelles de la mission ; il n'estime rien.

Rapprochement : un contrôle organisationnel porte un identifiant de clause
(`ISO-A.8.2`), et chaque règle technique déclare les clauses qu'elle appuie
(`ISO 27001:2022 — A.8.2 Droits d'accès privilégiés`). La correspondance se
fait sur la référence de clause, en évitant qu'`A.8.2` ne se confonde avec
`A.8.20`.
"""
from __future__ import annotations

import re


def _reference_clause(control_id: str) -> str:
    """Extrait la référence de clause d'un identifiant de contrôle manuel.

    `ISO-A.8.2` -> `A.8.2`. Un identifiant sans préfixe est renvoyé tel quel.
    """
    ref = str(control_id or "").strip()
    if "-" in ref:
        ref = ref.split("-", 1)[1]
    return ref


def _appuie(reference: str, frameworks: list[str]) -> bool:
    """Une règle technique appuie-t-elle cette clause ?

    La frontière est indispensable : sans elle, `A.8.2` serait considérée comme
    couverte par une règle qui ne mentionne en réalité qu'`A.8.20`.
    """
    if not reference:
        return False
    motif = re.compile(rf"(?<![\w.]){re.escape(reference)}(?![\d.])")
    return any(motif.search(str(f)) for f in frameworks or [])


def couverture_technique(state: dict) -> dict:
    """Part des contrôles organisationnels appuyés par une preuve technique."""
    evaluation = (state.get("steps") or {}).get("evaluation") or {}
    controles = evaluation.get("manual_controls") or []
    resultats = evaluation.get("technical_results") or {}
    regles = resultats.get("controls") or []

    details = []
    for c in controles:
        reference = _reference_clause(c.get("id"))
        preuves = [
            r.get("id") for r in regles
            if _appuie(reference, r.get("frameworks") or [])
        ]
        details.append({
            "controle": c.get("id"),
            "titre": c.get("title", ""),
            "couvert": bool(preuves),
            "preuves": preuves,
        })

    total = len(details)
    couverts = sum(1 for d in details if d["couvert"])
    return {
        "controles_total": total,
        "controles_couverts": couverts,
        "taux": round(couverts / total * 100) if total else 0,
        "scan_execute": bool(resultats),
        "details": details,
    }


def phrase(couv: dict) -> str:
    """Formulation destinée au client, dans les livrables comme à l'écran."""
    if not couv["scan_execute"]:
        return ("Aucun scan technique n'a été exécuté : à ce stade, "
                "l'ensemble des constats repose sur du déclaratif.")
    if couv["controles_total"] == 0:
        return "Aucun contrôle organisationnel n'est défini pour cette mission."
    return (
        f"{couv['controles_couverts']} contrôle(s) sur {couv['controles_total']} "
        f"({couv['taux']} %) sont appuyés par une preuve technique automatisée ; "
        f"les autres reposent sur des éléments déclaratifs."
    )
