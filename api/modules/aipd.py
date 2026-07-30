"""aipd.py — obligations organisationnelles de l'AIPD (§14.2.1).

Le module codé jusqu'ici couvrait les **quatre volets d'analyse** de l'AIPD
(description systématique, nécessité/proportionnalité, risques pour les droits
et libertés, mesures d'atténuation). C'est le contenu de l'analyse.

Manquaient les cinq obligations **de procédure** du RGPD, qui ne relèvent pas de
l'analyse mais de sa conduite : sans elles, une AIPD peut être parfaitement
argumentée et néanmoins irrégulière.

La cinquième — saisir la CNIL avant la mise en œuvre (Art. 36 §1) — n'est due
que si un risque résiduel élevé subsiste *après* mesures. Elle est donc
conditionnelle, et c'est le consultant qui qualifie ce risque résiduel : rien
ici ne le déduit à sa place.

Aucun texte normatif n'est recopié (F3) : références d'articles et intitulés
courts reformulés.
"""
from __future__ import annotations

RISQUE_RESIDUEL = ("non_evalue", "acceptable", "eleve")

# `conditionnelle` : due seulement si le risque résiduel reste élevé.
OBLIGATIONS = (
    {
        "id": "DPO",
        "libelle": "Avis du délégué à la protection des données recueilli",
        "reference": "RGPD Art. 35 §2",
        "aide": "Obligatoire dès qu'un DPO est désigné. Son avis, et les suites qui lui sont données, se consignent.",
        "conditionnelle": False,
    },
    {
        "id": "PERSONNES",
        "libelle": "Avis des personnes concernées recueilli (ou motif de non-consultation)",
        "reference": "RGPD Art. 35 §9",
        "aide": "À solliciter le cas échéant. Ne pas consulter est possible, mais la raison doit être documentée.",
        "conditionnelle": False,
    },
    {
        "id": "LISTES_CNIL",
        "libelle": "Confrontation aux listes CNIL des traitements soumis / exemptés",
        "reference": "RGPD Art. 35 §4-5",
        "aide": "Les deux listes déterminent si l'AIPD est obligatoire ou explicitement dispensée.",
        "conditionnelle": False,
    },
    {
        "id": "REEXAMEN",
        "libelle": "Réexamen prévu à chaque évolution du niveau de risque",
        "reference": "RGPD Art. 35 §11",
        "aide": "L'AIPD n'est pas un document daté une fois pour toutes : préciser l'événement déclencheur du réexamen.",
        "conditionnelle": False,
    },
    {
        "id": "ART36",
        "libelle": "Consultation préalable de la CNIL avant mise en œuvre",
        "reference": "RGPD Art. 36 §1",
        "aide": "Due uniquement si un risque résiduel élevé subsiste malgré les mesures d'atténuation.",
        "conditionnelle": True,
    },
)


def obligations_par_defaut() -> list[dict]:
    """Les cinq obligations, non traitées."""
    return [{"id": o["id"], "satisfait": False, "commentaire": ""} for o in OBLIGATIONS]


def _index(aipd: dict) -> dict[str, dict]:
    return {o.get("id"): o for o in (aipd.get("obligations") or [])}


def art36_requise(aipd: dict) -> bool:
    """La consultation préalable n'est due que sur risque résiduel élevé."""
    return aipd.get("risque_residuel") == "eleve"


def etat(aipd: dict) -> dict:
    """Avancement des obligations organisationnelles.

    L'obligation conditionnelle n'entre au dénominateur que lorsqu'elle est
    effectivement due : compter une obligation non exigible ferait afficher un
    taux de conformité inférieur à la réalité.
    """
    saisies = _index(aipd)
    art36 = art36_requise(aipd)

    dues, satisfaites, manquantes = [], 0, []
    for obligation in OBLIGATIONS:
        if obligation["conditionnelle"] and not art36:
            continue
        dues.append(obligation["id"])
        if saisies.get(obligation["id"], {}).get("satisfait"):
            satisfaites += 1
        else:
            manquantes.append(obligation["libelle"])

    total = len(dues)
    return {
        "satisfaites": satisfaites,
        "total": total,
        "taux": round(satisfaites / total * 100) if total else 0,
        "complete": total > 0 and satisfaites == total,
        "manquantes": manquantes,
        "art36_requise": art36,
        "risque_residuel": aipd.get("risque_residuel", "non_evalue"),
    }


def alerte_bloquante(aipd: dict) -> str | None:
    """Message à afficher quand le traitement ne peut pas démarrer en l'état.

    Un risque résiduel élevé non soumis à la CNIL interdit la mise en œuvre :
    c'est le seul cas où l'application affiche un blocage, et il mérite d'être
    dit en toutes lettres plutôt que noyé dans une case à cocher.
    """
    if not art36_requise(aipd):
        return None
    if _index(aipd).get("ART36", {}).get("satisfait"):
        return None
    return ("Risque résiduel élevé : le traitement ne peut pas être mis en œuvre "
            "avant consultation de la CNIL (RGPD Art. 36 §1).")
