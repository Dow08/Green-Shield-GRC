"""reporter.py — Générateur de rapport d'audit (Markdown, orienté COMEX).

Consolide un `AuditResult` en un document Markdown structuré et professionnel :
Executive Summary, score de conformité, synthèse des écarts avec mapping
normatif, et Plan d'Action d'Amélioration (PAA) priorisé par gravité.
"""
from __future__ import annotations

from .engine import AuditResult, ControlResult, COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE

_STATUS_ICON = {COMPLIANT: "🟢", NON_COMPLIANT: "🔴", NOT_APPLICABLE: "⚪"}
_STATUS_LABEL = {COMPLIANT: "Conforme", NON_COMPLIANT: "Non conforme", NOT_APPLICABLE: "Non applicable"}


def _verdict(result: AuditResult) -> str:
    """Phrase de synthèse pour la direction, dérivée du score et des criticités."""
    if result.critical_count > 0:
        return (f"La configuration auditée présente **{result.critical_count} faille(s) critique(s)** "
                f"exposant l'organisation à un risque d'intrusion immédiat. Une remédiation prioritaire "
                f"est requise.")
    if result.score >= 85:
        return "La configuration auditée présente une posture de sécurité **maîtrisée**, sans écart critique."
    return ("La configuration auditée présente une posture **perfectible** : plusieurs écarts de "
            "durcissement doivent être corrigés pour atteindre un niveau de conformité satisfaisant.")


def _findings_table(controls: list[ControlResult]) -> str:
    lines = [
        "| Statut | Sévérité | Contrôle | Écart constaté | Référentiel |",
        "|:---:|:---|:---|:---|:---|",
    ]
    for c in controls:
        icon = _STATUS_ICON.get(c.status, "⚪")
        norm = c.frameworks[0] if c.frameworks else "—"
        if c.status == NON_COMPLIANT:
            ecart = f"`{c.key} = {c.actual}` (attendu : `{c.expected}`)"
        elif c.status == COMPLIANT:
            ecart = "Conforme à l'exigence"
        else:
            ecart = "Non évalué"
        lines.append(f"| {icon} | {c.severity} | {c.title} | {ecart} | {norm} |")
    return "\n".join(lines)


def _action_plan(result: AuditResult) -> str:
    gaps = result.gaps_sorted()
    if not gaps:
        return "_Aucun écart à traiter : la configuration est conforme au référentiel._"
    blocks = []
    for i, c in enumerate(gaps, start=1):
        frameworks = "\n".join(f"  - {f}" for f in c.frameworks) or "  - —"
        blocks.append(
            f"### {i}. [{c.severity}] {c.title}  \n"
            f"**Contrôle technique :** `{c.key}` dans `{c.target_file}`  \n"
            f"**Constat (preuve, ligne du fichier) :** `{c.evidence}`  \n"
            f"**Risque (EBIOS RM, gravité {c.ebios_gravity}/4) :** {c.ebios_event}  \n"
            f"**Exigences normatives :**  \n{frameworks}  \n"
            f"**Recommandation :** {c.recommendation}  \n"
            f"**Justification :** {c.rationale}"
        )
    return "\n\n".join(blocks)


def build_markdown(result: AuditResult) -> str:
    """Assemble le rapport d'audit complet au format Markdown."""
    total = len(result.controls)
    evaluated = len(result.evaluated)
    gaps = len(result.gaps)

    md = f"""# Rapport d'audit de conformité — AuditCraft GRC

**Référentiel :** {result.referential} (v{result.version})
**Cible auditée :** `{result.target_dir}`
**Date :** {result.generated_at}
**Méthode :** analyse hors-ligne des configurations (aucun scan réseau)

---

## 1. Executive Summary

{_verdict(result)}

| Indicateur | Valeur |
|:---|:---:|
| **Score de conformité global** | **{result.score} %** ({result.band}) |
| Failles critiques | {result.critical_count} |
| Écarts identifiés | {gaps} |
| Contrôles évalués | {evaluated} / {total} |

Le score est calculé sur les contrôles réellement évaluables : `contrôles conformes / contrôles évalués`.

---

## 2. Synthèse des contrôles

{_findings_table(result.controls)}

Légende : 🟢 conforme · 🔴 non conforme · ⚪ non applicable.

---

## 3. Plan d'Action d'Amélioration (PAA)

Écarts classés par gravité décroissante. Traiter les éléments critiques en priorité.

{_action_plan(result)}

---

*Rapport généré automatiquement par AuditCraft GRC — DP Cyber Consulting. Analyse factuelle : chaque constat est appuyé par la ligne de configuration correspondante.*
"""
    return md
