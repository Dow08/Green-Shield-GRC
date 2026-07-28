"""Tests du validateur unique de segments de chemin (api/modules/path_safety.py).

Introduit suite à l'audit combiné du 28/07/2026 : plusieurs endpoints
construisaient un chemin disque à partir d'une entrée client non validée,
ouvrant un path traversal. Ces tests couvrent le validateur isolément ; les
tests de non-régression par endpoint vivent dans test_projects_security.py,
test_workflow_loader.py et test_collecte_technique.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import path_safety  # noqa: E402


# --- safe_path_component ---------------------------------------------------

def test_accepte_un_identifiant_alphanumerique_simple():
    assert path_safety.safe_path_component("acme") == "acme"


def test_accepte_underscore_et_tiret():
    assert path_safety.safe_path_component("mon_projet-2026") == "mon_projet-2026"


def test_accepte_les_identifiants_unicode_deja_en_usage_reel():
    # "cassiopé" est un identifiant de mission réel généré par create_project
    # (isalnum() est Unicode-aware) : le validateur ne doit pas le casser.
    assert path_safety.safe_path_component("cassiopé") == "cassiopé"


def test_rejette_une_sequence_de_traversee():
    with pytest.raises(HTTPException) as exc_info:
        path_safety.safe_path_component("..")
    assert exc_info.value.status_code == 400


def test_rejette_une_traversee_avec_separateur():
    with pytest.raises(HTTPException):
        path_safety.safe_path_component("../../etc/passwd")


def test_rejette_un_separateur_windows():
    with pytest.raises(HTTPException):
        path_safety.safe_path_component("..\\..\\Windows")


def test_rejette_une_chaine_vide():
    with pytest.raises(HTTPException):
        path_safety.safe_path_component("")


def test_message_erreur_inclut_le_nom_du_champ():
    with pytest.raises(HTTPException) as exc_info:
        path_safety.safe_path_component("..", "identifiant de référentiel")
    assert "identifiant de référentiel" in exc_info.value.detail


# --- safe_filename -----------------------------------------------------

def test_conserve_un_nom_de_fichier_simple():
    assert path_safety.safe_filename("sshd_config") == "sshd_config"
    assert path_safety.safe_filename("nginx.conf") == "nginx.conf"


def test_reduit_un_chemin_avec_traversee_au_seul_nom_de_base():
    assert path_safety.safe_filename("../../sentinel/pwned.txt") == "pwned.txt"


def test_reduit_un_chemin_absolu_au_seul_nom_de_base():
    assert path_safety.safe_filename("/etc/passwd") == "passwd"


def test_rejette_un_nom_vide():
    with pytest.raises(HTTPException):
        path_safety.safe_filename("")


def test_rejette_none():
    with pytest.raises(HTTPException):
        path_safety.safe_filename(None)


def test_rejette_un_nom_reduit_a_une_traversee_pure():
    with pytest.raises(HTTPException):
        path_safety.safe_filename("../..")
