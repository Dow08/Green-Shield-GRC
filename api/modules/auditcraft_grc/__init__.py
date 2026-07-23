"""Module AuditCraft-GRC — audit de conformité (offline parsing + Policy-as-Code).

Expose deux choses au shell GREEN SHIELD :
  * MODULE : le descripteur (identité + métadonnées) pour le registre / la nav ;
  * run()  : exécute l'audit et renvoie un dict JSON-sérialisable (+ rapport Markdown).
"""
from __future__ import annotations

from pathlib import Path

from . import engine, reporter

_BASE = Path(__file__).resolve().parent
_RULES = _BASE / "grc_rules.yaml"

# Descripteur consommé par le registre du shell (construit la navigation).
MODULE = {
    "id": "auditcraft_grc",
    "name": "AuditCraft-GRC",
    "icon": "shield",
    "category": "Conformité",
    "description": "Audit de conformité par offline parsing + Policy-as-Code (ISO 27001 / RGPD / EBIOS).",
    "status": "active",
    "endpoint": "/api/auditcraft/run",
}


def run(target_dir: str) -> dict:
    """Exécute l'audit sur `target_dir` et renvoie un résultat sérialisable."""
    result = engine.run_audit(_RULES, target_dir)
    return {
        "referential": result.referential,
        "version": result.version,
        "target_dir": result.target_dir,
        "generated_at": result.generated_at,
        "score": result.score,
        "band": result.band,
        "critical_count": result.critical_count,
        "counts": {
            "total": len(result.controls),
            "evaluated": len(result.evaluated),
            "compliant": len(result.compliant),
            "gaps": len(result.gaps),
        },
        "controls": [
            {
                "id": c.rule_id,
                "title": c.title,
                "file": c.target_file,
                "key": c.key,
                "expected": c.expected,
                "actual": c.actual,
                "status": c.status,
                "severity": c.severity,
                "evidence": c.evidence,
                "ebios_event": c.ebios_event,
                "ebios_gravity": c.ebios_gravity,
                "frameworks": c.frameworks,
                "recommendation": c.recommendation,
                "rationale": c.rationale,
            }
            for c in result.controls
        ],
        "report_markdown": reporter.build_markdown(result),
    }
