"""snapshots.py — historique versionné d'une mission (F9 de l'audit critique).

Constat d'origine : `project.json` est monolithique et chaque sauvegarde le
réécrit intégralement. Une erreur de saisie ou une suppression malheureuse
était donc irrattrapable, et rien ne datait les états successifs — alors que la
méthodologie Hermes exige que « tout livrable soit daté et versionné ».

Un instantané est pris à chaque **validation de phase** : c'est le jalon
métier qui a du sens, et non chaque frappe au clavier. Les instantanés vivent
dans `<mission>/snapshots/`, donc à l'intérieur de l'archive d'export (F14) :
l'historique voyage avec la mission.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

# Au-delà, les plus anciens sont supprimés : l'historique sert à rattraper une
# erreur récente, pas à archiver indéfiniment (l'archive chiffrée est faite
# pour ça).
MAX_SNAPSHOTS = 30

DOSSIER = "snapshots"
_FORMAT_HORODATAGE = "%Y%m%d-%H%M%S"


def _dossier(p_dir: Path) -> Path:
    return p_dir / DOSSIER


def creer(
    p_dir: Path,
    state: dict,
    motif: str,
    chiffrer: Callable[[bytes], bytes] | None = None,
) -> str | None:
    """Enregistre un instantané de la mission. Renvoie son nom, ou None si
    l'écriture échoue — un instantané raté ne doit jamais empêcher une
    sauvegarde d'aboutir. `chiffrer` est optionnel (rétrocompatibilité des
    appels existants) : sans lui, l'instantané reste en clair comme avant."""
    try:
        dossier = _dossier(p_dir)
        dossier.mkdir(parents=True, exist_ok=True)

        horodatage = datetime.now().strftime(_FORMAT_HORODATAGE)
        motif_sur = "".join(c if c.isalnum() or c in "-_" else "-" for c in motif)[:40]
        nom = f"{horodatage}_{motif_sur}.json"

        cible = dossier / nom
        tmp = cible.with_name(cible.name + ".tmp")
        contenu = json.dumps(state, indent=2, ensure_ascii=False).encode("utf-8")
        if chiffrer:
            contenu = chiffrer(contenu)
        tmp.write_bytes(contenu)
        os.replace(tmp, cible)

        _elaguer(dossier)
        return nom
    except OSError:
        return None


def _elaguer(dossier: Path) -> None:
    instantanes = sorted(dossier.glob("*.json"))
    for vieux in instantanes[:-MAX_SNAPSHOTS]:
        try:
            vieux.unlink()
        except OSError:
            pass


def lister(p_dir: Path) -> list[dict]:
    """Instantanés disponibles, du plus récent au plus ancien."""
    dossier = _dossier(p_dir)
    if not dossier.is_dir():
        return []

    resultat = []
    for chemin in sorted(dossier.glob("*.json"), reverse=True):
        tige = chemin.stem
        horodatage, _, motif = tige.partition("_")
        try:
            date_lisible = datetime.strptime(horodatage, _FORMAT_HORODATAGE).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            date_lisible = horodatage
        resultat.append({
            "nom": chemin.name,
            "date": date_lisible,
            "motif": motif.replace("-", " ") or "sauvegarde",
            "octets": chemin.stat().st_size,
        })
    return resultat


def lire(
    p_dir: Path,
    nom: str,
    dechiffrer: Callable[[bytes], bytes] | None = None,
) -> dict:
    """Relit un instantané. Le nom est validé par l'appelant (path_safety).
    `dechiffrer` est optionnel : sans lui, le fichier est lu tel quel (clair),
    comme avant l'activation du chiffrement par défaut."""
    chemin = _dossier(p_dir) / nom
    if not chemin.is_file():
        raise FileNotFoundError(f"Instantané introuvable : {nom}")
    # Défense en profondeur : le nom a déjà été validé, on vérifie tout de même
    # que le chemin résolu reste dans le dossier d'instantanés.
    if not chemin.resolve().is_relative_to(_dossier(p_dir).resolve()):
        raise FileNotFoundError(f"Instantané introuvable : {nom}")
    contenu = chemin.read_bytes()
    if dechiffrer:
        contenu = dechiffrer(contenu)
    return json.loads(contenu.decode("utf-8"))
