"""Tests du chiffrement au repos par défaut (P0 de l'audit du 06/08/2026).

Avant ce correctif, `project.json` était écrit en clair sauf si l'opérateur
définissait manuellement `GREENSHIELD_STORAGE_KEY` — ce qui contredisait le
positionnement « souverain » du produit. Le chiffrement est désormais actif
par défaut, via une clé Fernet générée une fois puis persistée hors dépôt
(même schéma que le secret JWT dans `auth.py::_secret_persistant`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import data_paths, projects  # noqa: E402


def test_write_json_atomic_ecrit_des_octets_chiffres_non_json(tmp_path):
    cible = tmp_path / "project.json"
    projects._write_json_atomic(cible, {"id": "acme", "client": "Acme Corp"})
    brut = cible.read_bytes()
    # Le fichier sur disque n'est pas du JSON lisible tel quel.
    with pytest.raises(json.JSONDecodeError):
        json.loads(brut.decode("utf-8"))


def test_write_puis_read_state_restitue_l_etat_d_origine(tmp_path):
    cible = tmp_path / "project.json"
    projects._write_json_atomic(cible, {"id": "acme", "client": "Acme Corp", "steps": {}})
    state = projects._read_state(cible)
    assert state["id"] == "acme"
    assert state["client"] == "Acme Corp"


def test_read_state_relit_un_fichier_pre_existant_en_clair(tmp_path):
    """Rétrocompatibilité : une mission créée avant l'activation du
    chiffrement par défaut doit rester lisible sans migration manuelle."""
    cible = tmp_path / "project.json"
    cible.write_text(
        json.dumps({"id": "ancienne", "client": "Client historique", "steps": {}}),
        encoding="utf-8",
    )
    state = projects._read_state(cible)
    assert state["id"] == "ancienne"
    assert state["client"] == "Client historique"


def test_chiffrer_dechiffrer_font_un_aller_retour():
    original = b'{"id": "acme"}'
    protege = projects._chiffrer(original)
    assert protege != original
    assert projects._dechiffrer(protege) == original


def test_dechiffrer_retombe_silencieusement_sur_les_octets_bruts():
    """`_dechiffrer` ne doit jamais lever : un contenu non chiffré (mission
    historique) doit être renvoyé tel quel plutôt que faire planter la
    lecture d'une mission entière."""
    brut = b'{"id": "clair"}'
    assert projects._dechiffrer(brut) == brut


def test_la_cle_de_chiffrement_est_persistee_hors_du_depot():
    chemin = data_paths.resolve_data_root() / ".storage_key"
    assert chemin.is_file()
    assert chemin.read_text(encoding="utf-8").strip()
