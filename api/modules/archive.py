"""archive.py — export et import d'une mission en archive chiffrée (F14, F15).

Répond à deux frictions de l'audit critique :
  * F14 — aucune sauvegarde ni portabilité : toutes les missions vivaient dans
    un unique répertoire local, sans mécanisme d'export. Point unique de
    défaillance, incohérent pour un outil qui vend du PCA/PRA à ses clients.
  * F15 — l'archive est le vecteur le plus exposé : elle quitte le disque
    chiffré du poste (clé USB, pièce jointe, remise au client en fin de
    mission). Elle est donc chiffrée en AES-256 (standard WinZip AES, lisible
    par 7-Zip et WinZip) par un mot de passe choisi par le consultant.

Sécurité de l'import : une archive est une **entrée non fiable**. Trois
protections, chacune couverte par un test :
  * traversée de chemin (« Zip Slip ») — toute entrée dont le chemin résolu
    sort du répertoire cible est refusée ;
  * bombe de décompression — taille décompressée totale plafonnée ;
  * structure — l'archive doit contenir un `project.json` valide.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pyzipper

# Plafond de décompression : une mission réaliste pèse quelques Mo (le gros des
# données étant du JSON et des configurations texte). 200 Mo laisse une marge
# confortable tout en bloquant une bombe de décompression.
TAILLE_MAX_DECOMPRESSEE = 200 * 1024 * 1024

# Répertoires de la mission embarqués dans l'archive. `snapshots` en fait
# partie : l'historique versionné (F9) doit voyager avec la mission, sinon une
# restauration depuis archive repartirait sans aucun point de retour.
SOUS_DOSSIERS = ("targets", "reports", "evidence", "snapshots")


class ArchiveInvalide(Exception):
    """Archive illisible, malformée, ou dont le mot de passe est incorrect."""


def _fichiers_de_mission(p_dir: Path) -> list[tuple[Path, str]]:
    """Liste (chemin absolu, nom dans l'archive) des fichiers à embarquer."""
    fichiers: list[tuple[Path, str]] = []

    project_json = p_dir / "project.json"
    if project_json.is_file():
        fichiers.append((project_json, "project.json"))

    for sous in SOUS_DOSSIERS:
        racine = p_dir / sous
        if not racine.is_dir():
            continue
        for chemin in sorted(racine.rglob("*")):
            if chemin.is_file():
                fichiers.append((chemin, f"{sous}/{chemin.relative_to(racine).as_posix()}"))

    return fichiers


def export_archive(p_dir: Path, password: str) -> bytes:
    """Produit l'archive chiffrée d'une mission."""
    if not password:
        raise ArchiveInvalide("Un mot de passe est obligatoire pour chiffrer l'archive")
    if not (p_dir / "project.json").is_file():
        raise ArchiveInvalide("Mission introuvable ou incomplète (project.json absent)")

    tampon = io.BytesIO()
    with pyzipper.AESZipFile(
        tampon, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(password.encode("utf-8"))
        for chemin, nom_archive in _fichiers_de_mission(p_dir):
            zf.write(chemin, nom_archive)

    return tampon.getvalue()


def _nom_sur(nom_archive: str, destination: Path) -> Path:
    """Valide qu'une entrée d'archive reste bien sous `destination`.

    Protection « Zip Slip » : une archive malveillante peut contenir des noms
    comme `../../etc/passwd` ou un chemin absolu. On résout et on vérifie
    l'appartenance plutôt que de faire confiance au nom.

    L'antislash est refusé **explicitement**, indépendamment du système : la
    spécification ZIP impose `/` comme séparateur, donc un antislash dans un
    nom d'entrée est au mieux anormal, au pire une attaque. Sans ce refus, une
    entrée `..\\..\\windows\\evil.txt` serait un simple nom de fichier sous
    Linux (l'antislash y est un caractère valide) et traverserait à
    l'extraction sous Windows — la validation ne peut pas dépendre du système
    qui extrait. Écart relevé par la CI Linux le 29/07/2026, invisible en
    développement sous Windows.
    """
    if "\\" in nom_archive:
        raise ArchiveInvalide(f"Chemin d'archive refusé (antislash) : {nom_archive}")
    if nom_archive.startswith("/") or ":" in nom_archive:
        raise ArchiveInvalide(f"Chemin d'archive refusé : {nom_archive}")
    cible = (destination / nom_archive).resolve()
    if not cible.is_relative_to(destination.resolve()):
        raise ArchiveInvalide(f"Chemin d'archive refusé (traversée) : {nom_archive}")
    return cible


def lire_archive(donnees: bytes, password: str) -> tuple[dict, list[tuple[str, bytes]]]:
    """Ouvre et valide une archive. Renvoie (état de la mission, fichiers).

    N'écrit rien sur disque : l'appelant décide où et sous quel identifiant.
    """
    if not password:
        raise ArchiveInvalide("Mot de passe requis pour déchiffrer l'archive")

    try:
        zf = pyzipper.AESZipFile(io.BytesIO(donnees))
    except Exception as exc:
        raise ArchiveInvalide(f"Archive illisible : {exc}") from exc

    with zf:
        zf.setpassword(password.encode("utf-8"))

        total = sum(info.file_size for info in zf.infolist())
        if total > TAILLE_MAX_DECOMPRESSEE:
            raise ArchiveInvalide(
                f"Archive refusée : {total // (1024 * 1024)} Mo décompressés "
                f"(plafond {TAILLE_MAX_DECOMPRESSEE // (1024 * 1024)} Mo)"
            )

        fichiers: list[tuple[str, bytes]] = []
        try:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                fichiers.append((info.filename, zf.read(info.filename)))
        except RuntimeError as exc:
            # pyzipper lève RuntimeError sur mot de passe incorrect.
            raise ArchiveInvalide("Mot de passe incorrect ou archive corrompue") from exc
        except Exception as exc:
            raise ArchiveInvalide(f"Archive illisible : {exc}") from exc

    contenu_json = next((data for nom, data in fichiers if nom == "project.json"), None)
    if contenu_json is None:
        raise ArchiveInvalide("Archive invalide : project.json absent")

    try:
        state = json.loads(contenu_json.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveInvalide("Archive invalide : project.json illisible") from exc

    if not isinstance(state, dict):
        raise ArchiveInvalide("Archive invalide : project.json n'est pas un objet")

    return state, fichiers


def ecrire_fichiers(fichiers: list[tuple[str, bytes]], destination: Path) -> None:
    """Écrit les fichiers d'une archive validée dans `destination`.

    Chaque nom repasse par la validation anti-traversée : la validation à la
    lecture ne dispense pas de la refaire au moment d'écrire.
    """
    destination.mkdir(parents=True, exist_ok=True)
    for nom_archive, donnees in fichiers:
        if nom_archive == "project.json":
            continue  # écrit séparément, après migration de schéma
        cible = _nom_sur(nom_archive, destination)
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(donnees)
