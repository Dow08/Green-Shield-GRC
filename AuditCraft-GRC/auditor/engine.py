"""engine.py — Le moteur d'évaluation GRC.

Charge le référentiel Policy-as-Code (grc_rules.yaml), lit les fichiers de la
cible (via parser.py), confronte chaque règle à la configuration réelle, puis
consolide un résultat d'audit factuel (statut par contrôle, score, comptages).

Aucun effet de bord réseau : lecture de fichiers uniquement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

import parser as cfg_parser

# Statuts possibles d'un contrôle.
COMPLIANT = "CONFORME"
NON_COMPLIANT = "NON_CONFORME"
NOT_APPLICABLE = "NON_APPLICABLE"

# Ordre de sévérité (pour tri et priorisation du plan d'action).
SEVERITY_ORDER = {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}


@dataclass(frozen=True)
class ControlResult:
    """Résultat d'évaluation d'une règle GRC contre la cible."""
    rule_id: str
    title: str
    target_file: str
    key: str
    expected: str
    actual: str | None
    status: str
    severity: str
    evidence: str
    ebios_event: str
    ebios_gravity: int
    frameworks: list[str]
    recommendation: str
    rationale: str

    @property
    def is_gap(self) -> bool:
        return self.status == NON_COMPLIANT


@dataclass
class AuditResult:
    """Consolidation d'un audit complet."""
    referential: str
    version: str
    target_dir: str
    generated_at: str
    controls: list[ControlResult] = field(default_factory=list)

    # --- indicateurs dérivés ---
    @property
    def evaluated(self) -> list[ControlResult]:
        """Contrôles réellement évaluables (hors NON_APPLICABLE)."""
        return [c for c in self.controls if c.status != NOT_APPLICABLE]

    @property
    def gaps(self) -> list[ControlResult]:
        return [c for c in self.controls if c.is_gap]

    @property
    def compliant(self) -> list[ControlResult]:
        return [c for c in self.controls if c.status == COMPLIANT]

    @property
    def score(self) -> int:
        """Score de conformité global en %, sur les seuls contrôles évaluables."""
        base = len(self.evaluated)
        if base == 0:
            return 0
        return round(len(self.compliant) / base * 100)

    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.gaps if c.severity == "Critique")

    @property
    def band(self) -> str:
        """Bande qualitative associée au score (pour la synthèse COMEX)."""
        s = self.score
        if s >= 85:
            return "Maîtrisée"
        if s >= 60:
            return "À surveiller"
        return "Critique"

    def gaps_sorted(self) -> list[ControlResult]:
        """Écarts triés par gravité décroissante (plan d'action)."""
        return sorted(self.gaps, key=lambda c: (SEVERITY_ORDER.get(c.severity, 9), c.rule_id))


# ------------------------------------------------------------------ règles

def load_rules(rules_path: str | Path) -> dict:
    """Charge et valide a minima le référentiel Policy-as-Code."""
    path = Path(rules_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "rules" not in data or not isinstance(data["rules"], list):
        raise ValueError("grc_rules.yaml invalide : clé 'rules' (liste) manquante.")
    return data


# ------------------------------------------------------------- évaluation

def _evaluate(rule: dict, directives: list[cfg_parser.Directive] | None) -> ControlResult:
    """Évalue une règle contre les directives d'un fichier déjà parsé."""
    key = rule["key"]
    operator = rule["operator"]
    expected = str(rule.get("expected", "")) or ", ".join(rule.get("forbidden", []))
    ebios = rule.get("ebios", {}) or {}

    # Fichier cible absent -> contrôle non applicable (jamais de faux résultat).
    if directives is None:
        return _result(rule, actual=None, status=NOT_APPLICABLE,
                       evidence=f"Fichier cible « {rule['target_file']} » introuvable.", expected=expected)

    directive = cfg_parser.effective(directives, key)
    actual = directive.value if directive else None
    evidence = directive.raw if directive else f"Directive « {key} » absente du fichier."

    if operator == "must_equal":
        ok = actual is not None and actual.strip().lower() == str(rule["expected"]).strip().lower()
        status = COMPLIANT if ok else NON_COMPLIANT

    elif operator == "must_not_equal":
        hit = actual is not None and actual.strip().lower() == str(rule["expected"]).strip().lower()
        status = NON_COMPLIANT if hit else COMPLIANT

    elif operator == "must_not_contain":
        if actual is None:
            # Directive absente : le défaut système prévaut -> à vérifier manuellement.
            status = NOT_APPLICABLE
            evidence = f"Directive « {key} » absente (comportement par défaut à vérifier)."
        else:
            tokens = actual.lower().split()
            forbidden = [f for f in rule.get("forbidden", []) if f.lower() in tokens]
            status = NON_COMPLIANT if forbidden else COMPLIANT
    else:
        # Opérateur inconnu -> non applicable (le référentiel reste maître, pas de crash).
        status = NOT_APPLICABLE
        evidence = f"Opérateur « {operator} » non supporté par le moteur."

    return _result(rule, actual=actual, status=status, evidence=evidence, expected=expected,
                   ebios_event=ebios.get("event", ""), ebios_gravity=int(ebios.get("gravity", 0)))


def _result(rule: dict, *, actual, status, evidence, expected,
            ebios_event="", ebios_gravity=0) -> ControlResult:
    ebios = rule.get("ebios", {}) or {}
    return ControlResult(
        rule_id=rule["id"],
        title=rule["title"],
        target_file=rule["target_file"],
        key=rule["key"],
        expected=expected,
        actual=actual,
        status=status,
        severity=rule.get("severity", "Moyen"),
        evidence=evidence,
        ebios_event=ebios_event or ebios.get("event", ""),
        ebios_gravity=ebios_gravity or int(ebios.get("gravity", 0)),
        frameworks=list(rule.get("frameworks", [])),
        recommendation=rule.get("recommendation", ""),
        rationale=rule.get("rationale", ""),
    )


def run_audit(rules_path: str | Path, target_dir: str | Path) -> AuditResult:
    """Exécute l'audit complet : parse la cible, évalue toutes les règles."""
    rules_doc = load_rules(rules_path)
    meta = rules_doc.get("metadata", {}) or {}
    target = Path(target_dir)

    # Parse chaque fichier cible UNE fois (mise en cache locale).
    parsed: dict[str, list[cfg_parser.Directive] | None] = {}
    for rule in rules_doc["rules"]:
        fname = rule["target_file"]
        if fname in parsed:
            continue
        fpath = target / fname
        if not fpath.is_file():
            parsed[fname] = None
            continue
        text = fpath.read_text(encoding="utf-8", errors="replace")
        parsed[fname] = cfg_parser.parse_file(fname, text)

    controls = [_evaluate(rule, parsed.get(rule["target_file"])) for rule in rules_doc["rules"]]

    return AuditResult(
        referential=meta.get("name", "Référentiel GRC"),
        version=str(meta.get("version", "1.0")),
        target_dir=str(target),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        controls=controls,
    )
