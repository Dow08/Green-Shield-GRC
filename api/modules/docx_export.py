"""docx_export.py — utilitaires communs aux livrables d'une mission.

Jusqu'au 31/07/2026, ce module produisait aussi le rapport Word (via un
gabarit `docxtpl` statique, `api/templates/rapport_iso27001.docx`). Ce gabarit
n'était jamais mis à jour au fil des jalons — resté à 7 sections génériques
pendant que le reste de l'application montait à 13 — et son titre était écrit
en dur, faux sur une mission de conseil. Le rendu Word vit désormais dans
`report_docx.py`, sur le même modèle que `report_html.py` : plus de gabarit
intermédiaire, un rendu programmatique qui lit les mêmes champs partout.

Ce qui reste ici est réellement partagé entre les trois formats de sortie
(Markdown, HTML, Word) : le principe **aucune donnée inventée** — un champ non
renseigné apparaît comme non renseigné, jamais comblé par une valeur
plausible —, l'empreinte d'intégrité et la mention de réserve.
"""
from __future__ import annotations

import hashlib
import json

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


def mention_reserve(date_emission: str, client: str) -> str:
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
