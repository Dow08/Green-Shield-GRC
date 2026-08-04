"""desktop.py — point d'entrée de l'exécutable Windows.

Démarre le serveur local puis ouvre le navigateur. Ce n'est pas un service :
fermer la fenêtre arrête l'application, et rien n'écoute au-delà de la boucle
locale.

Deux garanties reprises de l'architecture, à ne pas perdre en empaquetant :

  * **écoute sur 127.0.0.1 uniquement** — jamais `0.0.0.0`, sans quoi le poste
    exposerait les données d'audit au réseau local ;
  * **secret de session persistant** — `modules.auth` le conserve dans la
    racine de données, ce qui évite de déconnecter l'utilisateur à chaque
    lancement.

Lancement depuis les sources, pour tester le comportement du binaire :

    cd api && py -3 desktop.py
"""
from __future__ import annotations

import socket
import sys
import threading
import webbrowser

import uvicorn

HOTE = "127.0.0.1"
PORT_PREFERE = 8000


def _port_disponible(hote: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonde:
        sonde.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sonde.connect_ex((hote, port)) != 0


def choisir_port() -> int:
    """Premier port libre à partir du port habituel.

    Un autre GREEN SHIELD déjà lancé, ou n'importe quel service occupant le
    8000, ferait échouer le démarrage avec une trace illisible pour
    l'utilisateur final.
    """
    for port in range(PORT_PREFERE, PORT_PREFERE + 20):
        if _port_disponible(HOTE, port):
            return port
    raise SystemExit("Aucun port libre entre 8000 et 8019 — fermez l'instance déjà ouverte.")


def main() -> None:
    port = choisir_port()
    url = f"http://{HOTE}:{port}"

    print("GREEN SHIELD")
    print(f"  Interface : {url}")
    print("  Fermez cette fenêtre pour arrêter l'application.\n")

    # Le navigateur est ouvert en différé : appelé avant `uvicorn.run`, il
    # tomberait sur un serveur qui n'écoute pas encore.
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    # `main` est importé ici et non en tête de fichier : l'import déclenche la
    # construction de l'application (routes, base, secret), qu'on ne veut pas
    # payer si le choix du port échoue.
    from main import app

    uvicorn.run(app, host=HOTE, port=port, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as exc:  # noqa: BLE001 — dernier filet avant la console
        print(f"\nErreur au démarrage : {exc}")
        input("Appuyez sur Entrée pour fermer…")
        sys.exit(1)
