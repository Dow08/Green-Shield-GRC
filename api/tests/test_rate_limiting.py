"""Rate limiting dédié sur les routes d'export et /copilot/ask (V-04, audit
combiné du 06/08/2026).

Avant ce correctif, seules `/api/auth/login` et `/api/auth/register`
avaient un frein explicite ; les 14 routes d'export et `/copilot/ask`
n'étaient couvertes que par le plafond partagé de 60/minute par IP
(`main.py`, SlowAPIMiddleware) — un seul endpoint coûteux (génération de
rapport, appel LLM) pouvait consommer tout ce budget pour les autres routes.

`conftest.py` désactive le limiteur partagé pour le reste de la suite (la
plupart des tests appellent les fonctions de route directement, sans objet
`Request` HTTP). Ces tests le réactivent ponctuellement et passent par un
vrai `TestClient` HTTP, seul chemin où slowapi peut effectivement compter les
requêtes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402
from modules import auth  # noqa: E402

client = TestClient(main.app)


@pytest.fixture()
def limiteur_actif():
    """Réactive le limiteur partagé pour la durée du test, avec un compteur
    remis à zéro — sinon un test précédent (ou un ordre d'exécution différent)
    pourrait laisser des requêtes déjà comptabilisées."""
    auth.limiter._storage.reset()
    auth.limiter.enabled = True
    yield
    auth.limiter.enabled = False


def test_route_d_export_est_limitee_en_debit(limiteur_actif):
    """30/minute sur les routes d'export (ex: tableau de restitution HTML) —
    la mission n'a pas besoin d'exister : le plafond se déclenche avant même
    que la route ne cherche le projet."""
    for _ in range(30):
        reponse = client.get("/api/projects/inexistante-rate-test/report/tableau-restitution.html")
        assert reponse.status_code == 404

    reponse = client.get("/api/projects/inexistante-rate-test/report/tableau-restitution.html")
    assert reponse.status_code == 429


def test_copilot_ask_est_limite_en_debit(limiteur_actif):
    """20/minute sur /copilot/ask — la route la plus coûteuse (appel LLM
    potentiel) est celle qui avait le plus besoin d'un frein dédié."""
    for _ in range(20):
        reponse = client.post("/api/copilot/ask", json={"prompt": "test"})
        assert reponse.status_code != 429

    reponse = client.post("/api/copilot/ask", json={"prompt": "test"})
    assert reponse.status_code == 429


def test_les_deux_routes_ont_des_plafonds_independants(limiteur_actif):
    """Épuiser le plafond d'une route ne doit pas affecter une autre route —
    chaque endpoint a son propre compteur (comportement slowapi par défaut,
    vérifié explicitement car c'est la propriété dont dépend le reste de la
    suite : une mission de démo abondamment exportée ailleurs ne doit pas
    priver /copilot/ask de son propre budget, et inversement)."""
    for _ in range(30):
        client.get("/api/projects/inexistante-rate-test-2/report/tableau-restitution.html")

    reponse = client.post("/api/copilot/ask", json={"prompt": "test"})
    assert reponse.status_code != 429
