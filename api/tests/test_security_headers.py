"""En-têtes de sécurité HTTP indépendants de nginx (V-06, audit combiné du
06/08/2026). `web/nginx.conf` ne protège que le déploiement Docker ;
l'exécutable de bureau et le mode développement servent ce même FastAPI sans
reverse proxy devant — ce middleware garantit les mêmes en-têtes partout.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402

client = TestClient(main.app)


def test_les_en_tetes_de_securite_sont_presents_sur_une_route_publique():
    reponse = client.get("/health")
    assert reponse.headers["X-Frame-Options"] == "DENY"
    assert reponse.headers["X-Content-Type-Options"] == "nosniff"
    assert reponse.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in reponse.headers["Content-Security-Policy"]


def test_les_en_tetes_de_securite_sont_presents_meme_sur_une_erreur():
    """Une réponse 404 doit rester protégée — pas seulement le chemin heureux.

    Un chemin `/api/...` sans mission correspondante plutôt qu'un chemin
    totalement inconnu : ce dernier retombe sur le fallback SPA (`servir_spa`,
    main.py) quand un build frontend est présent dans l'environnement de
    test, et répond 200 — un comportement de routage préexistant, distinct
    de ce que ce test vérifie."""
    reponse = client.get("/api/projects/mission-inexistante-xyz/report/tableau-restitution.html")
    assert reponse.status_code == 404
    assert reponse.headers["X-Frame-Options"] == "DENY"
    assert reponse.headers["Content-Security-Policy"]


def test_la_csp_correspond_a_celle_de_nginx():
    """Même politique que `web/nginx.conf`, pour un comportement identique
    quel que soit le mode d'exécution (Docker+nginx, exe de bureau, dev)."""
    reponse = client.get("/health")
    csp = reponse.headers["Content-Security-Policy"]
    for directive in (
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "object-src 'none'",
        "frame-ancestors 'none'",
    ):
        assert directive in csp
