"""materiel.py — détection des capacités du poste et recommandation de modèle local.

Objectif : qu'un consultant sans culture d'infrastructure sache quel modèle
Ollama son ordinateur peut réellement faire tourner, sans aller lire des
tableaux de VRAM sur un forum.

Deux niveaux, du moins au plus fiable :

  * `inspecter()` — lecture de la RAM, des cœurs et du GPU. Instantané, mais
    ce n'est qu'une estimation : la vitesse réelle dépend aussi du modèle,
    de la quantisation et de ce qui tourne déjà sur la machine.
  * `mesurer()` — envoie une vraie question courte au modèle et chronomètre.
    C'est la seule mesure honnête, et elle prend le temps qu'elle prend.

Aucune dépendance native (règle n°1 du projet) : `ctypes` et `subprocess`
appartiennent à la bibliothèque standard, et chaque sonde échoue en silence
si elle n'est pas disponible sur la plateforme.
"""
from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import time

from . import ai_gateway

# Un modèle quantisé occupe en mémoire un peu plus que sa taille sur disque
# (contexte, tampons). Marge retenue après mesure sur poste Windows.
_SURCOUT_MEMOIRE = 1.3

# Au-delà, la mémoire restante devient trop juste pour le système lui-même.
_FRACTION_UTILISABLE = 0.7


def _ram_totale_go() -> float | None:
    """RAM physique, sans dépendance externe (psutil est hors périmètre)."""
    if os.name == "nt":
        class _MemoryStatusEx(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        try:
            stat = _MemoryStatusEx()
            stat.dwLength = ctypes.sizeof(_MemoryStatusEx)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return round(stat.ullTotalPhys / 1e9, 1)
        except (AttributeError, OSError):
            return None
        return None
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1)
    except (AttributeError, ValueError, OSError):
        return None


def _gpu_nvidia() -> dict | None:
    """Interroge `nvidia-smi` s'il est présent.

    Absence de GPU, pilote manquant ou machine AMD/Intel : on renvoie None
    plutôt qu'une erreur — le poste tournera simplement sur processeur.
    """
    # Sans ce drapeau, une fenêtre de console clignote à chaque appel sous
    # Windows, ce qui est très visible depuis une application de bureau.
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        sortie = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, creationflags=creationflags,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    if sortie.returncode != 0 or not sortie.stdout.strip():
        return None
    premiere = sortie.stdout.strip().splitlines()[0]
    nom, _, vram = premiere.partition(",")
    try:
        vram_go = round(float(vram.strip()) / 1024, 1)
    except ValueError:
        return None
    return {"nom": nom.strip(), "vram_go": vram_go}


def _modeles_installes() -> list[dict]:
    """Modèles Ollama présents localement, avec leur taille sur disque."""
    import json
    from urllib.request import Request

    try:
        with ai_gateway.urlopen(
            Request(f"{ai_gateway.OLLAMA_URL}/api/tags"), timeout=3
        ) as reponse:
            corps = json.loads(reponse.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — Ollama absent ou arrêté : cas normal
        return []
    modeles = []
    for m in corps.get("models", []):
        if m.get("name"):
            modeles.append({"nom": m["name"], "taille_go": round(m.get("size", 0) / 1e9, 1)})
    return sorted(modeles, key=lambda m: m["taille_go"])


def inspecter() -> dict:
    """État du poste et recommandation, sans rien exécuter."""
    ram = _ram_totale_go()
    gpu = _gpu_nvidia()
    modeles = _modeles_installes()

    # Un modèle tourne vite s'il tient en VRAM ; sinon il déborde sur la RAM
    # et le processeur, d'où un ordre de grandeur de différence en vitesse.
    memoire_utile = gpu["vram_go"] if gpu else (ram or 0)
    budget = memoire_utile * _FRACTION_UTILISABLE

    tiennent = [m for m in modeles if m["taille_go"] * _SURCOUT_MEMOIRE <= budget]
    # Le plus gros modèle qui tienne : à mémoire égale, plus gros = meilleur.
    recommande = tiennent[-1]["nom"] if tiennent else None

    if not modeles:
        conseil = ("Ollama n'est pas lancé, ou aucun modèle n'est installé. "
                   "Lancez Ollama, puis téléchargez un modèle (par exemple : ollama pull mistral).")
    elif recommande:
        support = "la carte graphique" if gpu else "le processeur"
        conseil = (f"« {recommande} » est le plus gros modèle installé qui tienne en mémoire "
                   f"sur ce poste. Il s'exécutera sur {support}.")
    else:
        plus_petit = modeles[0]
        conseil = (f"Aucun modèle installé ne tient confortablement en mémoire "
                   f"({memoire_utile:.0f} Go disponibles). Le plus léger est "
                   f"« {plus_petit['nom']} » ({plus_petit['taille_go']} Go) : il fonctionnera "
                   f"peut-être, mais lentement. Un modèle plus petit serait plus adapté.")

    return {
        "systeme": f"{platform.system()} {platform.release()}",
        "ram_go": ram,
        "coeurs": os.cpu_count(),
        "gpu": gpu,
        "modeles_installes": modeles,
        "modele_recommande": recommande,
        "conseil": conseil,
        # L'estimation ne remplace pas la mesure : l'interface doit inviter à
        # lancer le vrai test avant de s'engager sur un modèle.
        "estimation": True,
    }


def precharger(modele: str) -> bool:
    """Charge le modèle en mémoire graphique sans attendre de réponse utile.

    Ollama décharge un modèle inutilisé au bout de quelques minutes ; le
    rappeler ensuite impose de le relire depuis le disque. Appelé à
    l'ouverture du panneau Copilote, ce préchargement rend la première vraie
    question aussi rapide que les suivantes.
    """
    return ai_gateway.appeler_llm(
        "ollama", "", "", "ok", modele=modele, timeout=ai_gateway.TIMEOUT_LOCAL
    ) is not None


def mesurer(modele: str) -> dict:
    """Chronomètre le modèle en séparant chargement et vitesse de réponse.

    Distinction essentielle, constatée le 05/08/2026 sur ce poste (RTX 4080) :
    113 s au premier appel contre 8 s aux suivants. Ne mesurer que le premier
    appel conduirait à déconseiller à tort un modèle parfaitement utilisable,
    et à afficher un temps que l'utilisateur ne reverra jamais.
    """
    question = "Réponds en une seule phrase courte : qu'est-ce qu'un audit de conformité ?"
    contexte = "Tu réponds de façon brève et factuelle, en français."

    depart_chargement = time.monotonic()
    charge = precharger(modele)
    duree_chargement = round(time.monotonic() - depart_chargement, 1)

    if not charge:
        return {"ok": False, "modele": modele, "duree_chargement_s": duree_chargement,
                "verdict": "Le modèle n'a pas répondu. Vérifiez qu'Ollama est lancé "
                           "et que ce modèle est bien installé."}

    depart = time.monotonic()
    reponse = ai_gateway.appeler_llm("ollama", "", contexte, question, modele=modele)
    duree = round(time.monotonic() - depart, 1)

    if reponse is None:
        return {"ok": False, "modele": modele, "duree_chargement_s": duree_chargement,
                "verdict": "Le modèle s'est chargé mais n'a pas répondu à la question."}

    # Seuils calés sur l'usage : au-delà d'une minute par phrase une fois
    # chargé, le copilote devient pénible en cours de mission.
    if duree <= 15:
        verdict = f"Confortable : {duree} s par réponse une fois le modèle chargé."
    elif duree <= 60:
        verdict = (f"Utilisable mais lent : {duree} s par réponse. "
                   f"Correct pour une question ponctuelle, pénible en usage continu.")
    else:
        verdict = (f"Trop lent pour un usage confortable : {duree} s par réponse. "
                   f"Essayez un modèle plus petit.")

    if duree_chargement > 20:
        verdict += (f" Premier chargement : {duree_chargement} s — payé une seule fois, "
                    f"puis le modèle reste en mémoire.")

    return {"ok": True, "modele": modele, "duree_s": duree,
            "duree_chargement_s": duree_chargement,
            "extrait": reponse.strip()[:300], "verdict": verdict}
