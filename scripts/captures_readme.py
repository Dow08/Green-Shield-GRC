"""captures_readme.py — génère les captures d'écran du README.

Outil de **développement**, jamais requis pour faire tourner l'application :
Playwright n'est pas dans `api/requirements.txt`. À installer seulement quand
on veut régénérer les captures :

    py -3 -m pip install playwright
    py -3 -m playwright install chromium

Puis, l'API et le frontend étant démarrés :

    py -3 scripts/captures_readme.py

Le script se connecte, crée la mission de démonstration si elle n'existe pas,
puis capture chaque écran en 1280x800 dans `docs/assets/`. Passer par un
navigateur piloté plutôt que par des captures manuelles garantit un cadrage
identique d'une capture à l'autre, sans barre de favoris ni fenêtre d'OS —
et permet de tout régénérer d'un coup après une évolution de l'interface.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

API = os.environ.get("GS_API", "http://127.0.0.1:8000")
WEB = os.environ.get("GS_WEB", "http://localhost:5173")
EMAIL = os.environ.get("GS_EMAIL", "demo@greenshield.local")
MOTDEPASSE = os.environ.get("GS_PASSWORD", "Demo1234")

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "docs" / "assets"
LARGEUR, HAUTEUR = 1280, 800
DEMO_ID = "demo_green_shield"


def _appel(chemin: str, methode: str = "GET", corps: dict | None = None, jeton: str = "") -> tuple[int, dict]:
    donnees = json.dumps(corps).encode() if corps is not None else None
    requete = urllib.request.Request(f"{API}{chemin}", data=donnees, method=methode)
    requete.add_header("Content-Type", "application/json")
    if jeton:
        requete.add_header("Authorization", f"Bearer {jeton}")
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            brut = reponse.read().decode()
            return reponse.status, (json.loads(brut) if brut else {})
    except urllib.error.HTTPError as exc:
        brut = exc.read().decode()
        try:
            return exc.code, json.loads(brut)
        except json.JSONDecodeError:
            return exc.code, {"detail": brut[:200]}


def preparer_compte_et_demo() -> str:
    """Compte de capture + mission de démonstration, créés au besoin."""
    _appel("/api/auth/register", "POST", {"email": EMAIL, "password": MOTDEPASSE})
    statut, reponse = _appel("/api/auth/login", "POST", {"email": EMAIL, "password": MOTDEPASSE})
    if statut != 200:
        sys.exit(f"Connexion impossible ({statut}) : {reponse.get('detail')}")
    jeton = reponse["access_token"]

    statut, _ = _appel(f"/api/projects/{DEMO_ID}", jeton=jeton)
    if statut != 200:
        statut, reponse = _appel("/api/projects/demo", "POST", {}, jeton)
        if statut != 200:
            sys.exit(f"Création de la démo impossible ({statut}) : {reponse.get('detail')}")
        print("  mission de démonstration créée")
    return jeton


# (fichier, phase, ancre) — l'ancre est un texte de la page vers lequel faire
# défiler avant la capture : sans elle on photographie toujours le haut de la
# page et les panneaux qui font l'intérêt de la phase restent hors champ.
ECRANS = [
    ("02-phase1-cadrage", 1, None),
    ("03-phase2-violations", 2, "Registre des Violations"),
    ("04-multi-referentiel", 5, None),
    ("05-soa", 5, "Déclaration d'Applicabilité (SoA)"),
    ("06-phase6-livrables", 6, None),
]


def capturer() -> None:
    jeton = preparer_compte_et_demo()
    SORTIE.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        page = navigateur.new_page(viewport={"width": LARGEUR, "height": HAUTEUR},
                                   device_scale_factor=2)  # rendu net sur écran HiDPI

        # Injecter le jeton avant le premier rendu : l'application vérifie la
        # session au démarrage et renverrait sinon vers l'écran de connexion.
        page.goto(WEB, wait_until="domcontentloaded")
        page.evaluate("t => localStorage.setItem('greenshield_token', t)", jeton)
        page.goto(WEB, wait_until="networkidle")

        def cliquer(texte: str) -> bool:
            cible = page.get_by_role("button", name=texte, exact=False).first
            if cible.count() == 0:
                return False
            cible.click()
            page.wait_for_timeout(900)
            return True

        cliquer("Registre de missions")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(SORTIE / "01-registre-missions.png"))
        print("  01-registre-missions.png")

        # Ouvrir la mission de démonstration par le titre de sa carte. Cibler
        # le texte brut ne suffit pas : le nom de la mission apparaît aussi
        # dans la frise des remédiations, où il n'est pas cliquable.
        titre = page.get_by_role("heading", name="DÉMO", exact=False).first
        if titre.count() == 0:
            sys.exit("Carte de la mission de démonstration introuvable.")
        titre.click()
        page.wait_for_timeout(2000)

        # Les pastilles du stepper affichent une coche dès qu'une phase est
        # validée : on les cible par leur libellé accessible, pas par le
        # numéro qui disparaît alors du rendu.
        for nom, numero, ancre in ECRANS:
            pastille = page.get_by_role("button", name=f"Phase {numero} —", exact=False).first
            if pastille.count() == 0:
                sys.exit(f"Pastille de la phase {numero} introuvable — le stepper a changé.")
            pastille.click()
            page.wait_for_timeout(1500)

            if ancre:
                cible = page.get_by_text(ancre, exact=False).first
                if cible.count() == 0:
                    sys.exit(f"Ancre « {ancre} » introuvable en phase {numero}.")
                cible.scroll_into_view_if_needed()
                # Quelques pixels de marge au-dessus du titre de section.
                page.mouse.wheel(0, -80)
                page.wait_for_timeout(700)

            page.screenshot(path=str(SORTIE / f"{nom}.png"))
            print(f"  {nom}.png")

        navigateur.close()


if __name__ == "__main__":
    print("Génération des captures du README…")
    capturer()
    print(f"Terminé — {SORTIE}")
