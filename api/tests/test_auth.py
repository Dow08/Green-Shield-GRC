"""Tests de la révocation de session (V-03, audit combiné du 06/08/2026).

Avant ce correctif, un jeton JWT restait valable jusqu'à son expiration
naturelle (24h) même après un `/logout` : la déconnexion n'avait d'effet que
côté client (jeton oublié), pas côté serveur. Ces tests exercent le vrai flux
HTTP (register -> login -> route protégée -> logout -> même route rejetée),
donc ils retirent explicitement le mock global de `get_current_user` posé par
`conftest.py::override_dependency` pour les autres suites.
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

EMAIL = "auditeur.test@dpcyber.local"
PASSWORD = "MotDePasse1"


@pytest.fixture(autouse=True)
def _vrai_flux_auth():
    """`conftest.py` mocke `get_current_user` pour toutes les autres suites —
    ici on veut le vrai comportement JWT, donc on retire ce mock pour la durée
    de chaque test de ce fichier (restauré par le teardown de `conftest.py`)."""
    main.app.dependency_overrides.pop(auth.get_current_user, None)
    yield


def _inscrire_et_connecter(email: str = EMAIL, password: str = PASSWORD) -> str:
    client.post("/api/auth/register", json={"email": email, "password": password})
    reponse = client.post("/api/auth/login", json={"email": email, "password": password})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["access_token"]


def _entete(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_un_jeton_valide_donne_acces_a_une_route_protegee():
    token = _inscrire_et_connecter()
    reponse = client.get("/api/auth/me", headers=_entete(token))
    assert reponse.status_code == 200
    assert reponse.json()["email"] == EMAIL


def test_logout_revoque_le_jeton_et_les_requetes_suivantes_sont_rejetees():
    token = _inscrire_et_connecter()

    reponse = client.post("/api/auth/logout", headers=_entete(token))
    assert reponse.status_code == 200

    reponse = client.get("/api/auth/me", headers=_entete(token))
    assert reponse.status_code == 401


def test_logout_ne_revoque_pas_les_autres_jetons_du_meme_compte():
    """Un jeton révoqué ne doit invalider QUE lui-même — pas toutes les
    sessions actives du compte (jti unique par jeton, pas par utilisateur)."""
    token_a = _inscrire_et_connecter()
    reponse = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    token_b = reponse.json()["access_token"]
    assert token_a != token_b

    client.post("/api/auth/logout", headers=_entete(token_a))

    assert client.get("/api/auth/me", headers=_entete(token_a)).status_code == 401
    assert client.get("/api/auth/me", headers=_entete(token_b)).status_code == 200


def test_logout_sans_jeton_est_rejete():
    reponse = client.post("/api/auth/logout")
    assert reponse.status_code == 401


def test_logout_avec_un_jeton_deja_revoque_est_rejete():
    token = _inscrire_et_connecter()
    client.post("/api/auth/logout", headers=_entete(token))
    reponse = client.post("/api/auth/logout", headers=_entete(token))
    assert reponse.status_code == 401
