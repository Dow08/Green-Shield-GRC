"""Génération des livrables Word (.docx) à partir des données d'une mission.

Principe directeur : **aucune donnée inventée**. Un champ non renseigné par le
consultant apparaît explicitement comme non renseigné dans le livrable ; il n'est
jamais comblé par une valeur plausible. De même, un score n'est calculé que s'il
existe des contrôles réellement évalués — sinon le rapport indique « non évalué »
plutôt que 0 %, qui se lirait à tort comme une non-conformité totale.
"""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
ISO27001_TEMPLATE = TEMPLATES_DIR / "rapport_iso27001.docx"

NON_RENSEIGNE = "— non renseigné —"

# Libellés lisibles pour les statuts de contrôle stockés en base.
STATUS_LABELS = {
    "A_VERIFIER": "À vérifier",
    "CONFORME": "Conforme",
    "NON_CONFORME": "Non conforme",
    "NON_APPLICABLE": "Non applicable",
    "PARTIEL": "Partiellement conforme",
}


def _txt(value) -> str:
    """Rend une valeur affichable sans jamais inventer de contenu."""
    if value is None:
        return NON_RENSEIGNE
    text = str(value).strip()
    return text if text else NON_RENSEIGNE


def data_fingerprint(state: dict) -> str:
    """Empreinte SHA-256 des données source du rapport.

    Permet de prouver a posteriori que le document émis à une date donnée
    correspondait bien à un état précis de la mission (cf. spec §11, #5).
    Les clés sont triées pour que l'empreinte soit stable d'une exécution à l'autre.
    """
    payload = json.dumps(state, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mention_reserve(date_emission: str, client: str) -> str:
    """Mention de réserve : délimite la portée des constats (spec §13.4).

    C'est ce qui protège réellement le consultant — pas une clause auto-générée :
    le rapport dit sur quoi il se fonde et à quelle date.
    """
    return (
        f"Les constats figurant dans le présent rapport reposent exclusivement sur les "
        f"éléments communiqués par {client} et sur les preuves collectées à la date du "
        f"{date_emission}, dans le périmètre défini au chapitre 2. "
        "Les déclarations recueillies auprès des interlocuteurs n'ont fait l'objet d'une "
        "vérification technique que lorsque la colonne « Preuve » le mentionne "
        "explicitement. "
        "Le présent rapport constitue une évaluation à un instant donné et ne saurait "
        "valoir garantie d'absence de vulnérabilité ni de conformité future, le niveau "
        "de sécurité évoluant avec le système d'information et l'état de la menace."
    )


def _collect_constats(steps: dict) -> list[dict]:
    """Fusionne les contrôles évalués manuellement et les preuves techniques.

    Les résultats techniques proviennent du scan réel AuditCraft-GRC : ils portent
    une preuve factuelle (la ligne de configuration constatée), là où un contrôle
    manuel ne porte que la note de l'auditeur.
    """
    constats: list[dict] = []

    for ctrl in steps.get("evaluation", {}).get("manual_controls", []) or []:
        constats.append({
            "id": _txt(ctrl.get("id")),
            "title": _txt(ctrl.get("title")),
            "status": STATUS_LABELS.get(ctrl.get("status"), _txt(ctrl.get("status"))),
            "severity": "—",
            "evidence": _txt(ctrl.get("notes")) if ctrl.get("notes") else "Preuve à collecter",
        })

    technical = steps.get("evaluation", {}).get("technical_results") or {}
    for ctrl in technical.get("controls", []) or []:
        constats.append({
            "id": _txt(ctrl.get("id")),
            "title": _txt(ctrl.get("title")),
            "status": STATUS_LABELS.get(ctrl.get("status"), _txt(ctrl.get("status"))),
            "severity": _txt(ctrl.get("severity")),
            "evidence": _txt(ctrl.get("evidence")),
        })

    return constats


def _score_and_band(steps: dict, constats: list[dict]) -> tuple[str, str]:
    """Score de conformité — uniquement si des contrôles ont réellement été évalués."""
    technical = steps.get("evaluation", {}).get("technical_results") or {}
    if technical.get("score") is not None:
        return str(technical["score"]), _txt(technical.get("band"))

    evalues = [c for c in constats if c["status"] in ("Conforme", "Non conforme",
                                                      "Partiellement conforme")]
    if not evalues:
        return "non évalué", "évaluation en cours"

    conformes = sum(1 for c in evalues if c["status"] == "Conforme")
    return str(round(conformes / len(evalues) * 100)), "calculé sur les contrôles évalués"


def build_iso27001_context(state: dict, auditeur: str = "", cabinet: str = "") -> dict:
    """Traduit l'état d'une mission en variables du gabarit Word."""
    steps = state.get("steps", {}) or {}
    cadrage = steps.get("cadrage", {}) or {}
    client = _txt(state.get("client"))
    date_emission = datetime.now().strftime("%d/%m/%Y")

    constats = _collect_constats(steps)
    score, band = _score_and_band(steps, constats)
    ecarts = [c for c in constats if c["status"] == "Non conforme"]

    return {
        "titre_rapport": "Rapport d'audit de conformité",
        "client": client,
        "mission": _txt(state.get("name")),
        "referentiel": _txt(cadrage.get("framework_name") or cadrage.get("framework_id")),
        "auditeur": _txt(auditeur),
        "cabinet": _txt(cabinet),
        "perimetre": _txt(cadrage.get("scope")),
        "date_emission": date_emission,
        "version": "1.0",

        "synthese_executive": _txt(steps.get("restitution", {}).get("exec_summary")),
        "score": score,
        "band": band,
        "nb_ecarts": str(len(ecarts)),
        "nb_critiques": str(sum(1 for c in ecarts if c["severity"] == "Critique")),

        "methodologie": _txt(cadrage.get("client_missions")),

        "valeurs_metier": [
            {
                "id": _txt(a.get("id")),
                "name": _txt(a.get("name")),
                "description": _txt(a.get("description")),
                "personal": "Oui" if a.get("is_personal_data") else "Non",
            }
            for a in cadrage.get("assets_metier", []) or []
        ],
        "biens_supports": [
            {
                "id": _txt(a.get("id")),
                "name": _txt(a.get("name")),
                "type": _txt(a.get("type")),
                "owner": _txt(a.get("owner")),
            }
            for a in cadrage.get("assets_support", []) or []
        ],
        "constats": constats,
        "actions": [
            {
                "id": _txt(r.get("id")),
                "axe": _txt(r.get("axe")),
                "measure": _txt(r.get("measure")),
                "priority": _txt(r.get("priority")),
            }
            for r in steps.get("traitement", {}).get("remediations", []) or []
        ],

        "mention_reserve": _mention_reserve(date_emission, client),
        "hash_donnees": data_fingerprint(state),
    }


def render_iso27001(state: dict, auditeur: str = "", cabinet: str = "") -> bytes:
    """Produit le rapport ISO 27001 au format .docx et le renvoie en octets."""
    if not ISO27001_TEMPLATE.is_file():
        raise FileNotFoundError(
            f"Gabarit introuvable : {ISO27001_TEMPLATE}. "
            "Le générer avec : py -3 api/templates/build_templates.py"
        )
    doc = DocxTemplate(str(ISO27001_TEMPLATE))
    doc.render(build_iso27001_context(state, auditeur, cabinet))
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
