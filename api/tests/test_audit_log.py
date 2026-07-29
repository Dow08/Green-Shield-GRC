"""Tests du journal d'audit (api/modules/audit_log.py).

Deux exigences non négociables couvertes ici :
  1. le journal enregistre bien les actions sensibles ;
  2. il ne fait JAMAIS échouer une opération métier, quoi qu'il arrive au disque.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import audit_log, data_paths  # noqa: E402


@pytest.fixture()
def journal(tmp_path, monkeypatch):
    """Isole le journal dans un répertoire jetable et réinitialise le logger
    mémorisé entre deux tests."""
    monkeypatch.setattr(data_paths, "resolve_data_root", lambda: tmp_path)
    monkeypatch.setattr(audit_log, "_logger", None)
    # Le logger nommé est global au process : on le vide pour repartir propre.
    logging.getLogger("greenshield.audit").handlers.clear()
    yield tmp_path / "logs" / "audit.log"
    logging.getLogger("greenshield.audit").handlers.clear()


def _lire(journal_path: Path) -> str:
    for handler in logging.getLogger("greenshield.audit").handlers:
        handler.flush()
    return journal_path.read_text(encoding="utf-8")


def test_enregistre_une_action_avec_sa_cible(journal):
    audit_log.record("project.delete", target="acme")
    contenu = _lire(journal)
    assert "project.delete" in contenu
    assert "target=acme" in contenu
    assert "outcome=ok" in contenu


def test_enregistre_le_detail_quand_il_est_fourni(journal):
    audit_log.record("project.export", target="acme", detail="format=docx")
    assert "format=docx" in _lire(journal)


def test_enregistre_un_echec_avec_son_outcome(journal):
    audit_log.record("project.delete", target="acme", outcome="error")
    assert "outcome=error" in _lire(journal)


def test_horodate_chaque_entree(journal):
    audit_log.record("project.create", target="acme")
    premiere_ligne = _lire(journal).splitlines()[0]
    # Format "%(asctime)s | ..." -> commence par une date ISO-like
    assert premiere_ligne[:4].isdigit()
    assert " | " in premiere_ligne


def test_plusieurs_actions_s_accumulent(journal):
    audit_log.record("project.create", target="a")
    audit_log.record("project.update", target="a")
    audit_log.record("project.delete", target="a")
    assert len(_lire(journal).strip().splitlines()) == 3


def test_ne_leve_jamais_meme_si_le_journal_est_inouvrable(tmp_path, monkeypatch):
    """Disque plein, droits insuffisants, chemin invalide : l'opération métier
    doit continuer sans exception."""
    def raise_os_error():
        raise OSError("disque plein")

    monkeypatch.setattr(audit_log, "_logger", None)
    monkeypatch.setattr(data_paths, "resolve_data_root", raise_os_error)
    logging.getLogger("greenshield.audit").handlers.clear()

    # Ne doit rien lever.
    audit_log.record("project.delete", target="acme")


def test_ne_leve_jamais_si_l_ecriture_echoue(journal, monkeypatch):
    logger = audit_log._get_logger()
    assert logger is not None

    def raise_on_info(*args, **kwargs):
        raise OSError("écriture impossible")

    monkeypatch.setattr(logger, "info", raise_on_info)
    audit_log.record("project.delete", target="acme")  # ne doit rien lever


def test_le_journal_ne_remonte_pas_dans_le_logging_de_l_application(journal):
    """propagate=False : le journal d'audit ne doit pas polluer la sortie
    console d'uvicorn ni être capté par la config de logging hôte."""
    audit_log._get_logger()
    assert logging.getLogger("greenshield.audit").propagate is False
