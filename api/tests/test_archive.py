"""Tests de l'export/import de mission en archive chiffrée (F14, F15).

Une archive importée est une **entrée non fiable** : la moitié de ces tests
porte sur ce qu'il faut refuser (traversée de chemin, bombe de décompression,
structure invalide, mauvais mot de passe), pas sur le chemin nominal.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pyzipper
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import archive  # noqa: E402

MDP = "un-mot-de-passe-solide"


@pytest.fixture()
def mission(tmp_path) -> Path:
    p_dir = tmp_path / "acme"
    (p_dir / "targets").mkdir(parents=True)
    (p_dir / "reports").mkdir(parents=True)
    (p_dir / "project.json").write_text(
        json.dumps({"id": "acme", "name": "Acme", "client": "Acme Corp", "steps": {}}),
        encoding="utf-8",
    )
    (p_dir / "targets" / "sshd_config").write_text("Port 22\n", encoding="utf-8")
    (p_dir / "reports" / "rapport.md").write_text("# Rapport\n", encoding="utf-8")
    return p_dir


def _archive_maison(entrees: dict[str, bytes], password: str = MDP) -> bytes:
    """Fabrique une archive arbitraire (pour tester ce qu'on doit refuser)."""
    tampon = io.BytesIO()
    with pyzipper.AESZipFile(
        tampon, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(password.encode("utf-8"))
        for nom, donnees in entrees.items():
            zf.writestr(nom, donnees)
    return tampon.getvalue()


# --- Export ---------------------------------------------------------------

def test_export_produit_une_archive_non_vide(mission):
    donnees = archive.export_archive(mission, MDP)
    assert len(donnees) > 0
    assert donnees[:2] == b"PK"  # signature ZIP


def test_export_embarque_project_json_targets_et_reports(mission):
    donnees = archive.export_archive(mission, MDP)
    with pyzipper.AESZipFile(io.BytesIO(donnees)) as zf:
        noms = set(zf.namelist())
    assert "project.json" in noms
    assert "targets/sshd_config" in noms
    assert "reports/rapport.md" in noms


def test_export_sans_mot_de_passe_est_refuse(mission):
    with pytest.raises(archive.ArchiveInvalide, match="mot de passe"):
        archive.export_archive(mission, "")


def test_export_d_une_mission_incomplete_est_refuse(tmp_path):
    vide = tmp_path / "vide"
    vide.mkdir()
    with pytest.raises(archive.ArchiveInvalide, match="introuvable|incomplète"):
        archive.export_archive(vide, MDP)


def test_l_archive_est_reellement_chiffree(mission):
    """Le contenu ne doit pas être lisible sans le mot de passe."""
    donnees = archive.export_archive(mission, MDP)
    with zipfile.ZipFile(io.BytesIO(donnees)) as zf:
        with pytest.raises(Exception):
            zf.read("project.json")


# --- Aller-retour ---------------------------------------------------------

def test_aller_retour_conserve_l_etat_et_les_fichiers(mission):
    donnees = archive.export_archive(mission, MDP)
    state, fichiers = archive.lire_archive(donnees, MDP)

    assert state["id"] == "acme"
    assert state["client"] == "Acme Corp"
    noms = {n for n, _ in fichiers}
    assert {"project.json", "targets/sshd_config", "reports/rapport.md"} <= noms


def test_ecriture_restaure_les_fichiers_sur_disque(mission, tmp_path):
    donnees = archive.export_archive(mission, MDP)
    _, fichiers = archive.lire_archive(donnees, MDP)

    destination = tmp_path / "restauree"
    archive.ecrire_fichiers(fichiers, destination)

    assert (destination / "targets" / "sshd_config").read_text(encoding="utf-8") == "Port 22\n"
    assert (destination / "reports" / "rapport.md").is_file()
    # project.json est écrit séparément par l'appelant, après migration.
    assert not (destination / "project.json").exists()


# --- Refus : mot de passe -------------------------------------------------

def test_mauvais_mot_de_passe_est_refuse(mission):
    donnees = archive.export_archive(mission, MDP)
    with pytest.raises(archive.ArchiveInvalide, match="Mot de passe incorrect|illisible"):
        archive.lire_archive(donnees, "mauvais-mot-de-passe")


def test_lecture_sans_mot_de_passe_est_refusee(mission):
    donnees = archive.export_archive(mission, MDP)
    with pytest.raises(archive.ArchiveInvalide, match="Mot de passe requis"):
        archive.lire_archive(donnees, "")


def test_donnees_qui_ne_sont_pas_une_archive(mission):
    with pytest.raises(archive.ArchiveInvalide):
        archive.lire_archive(b"ceci n'est pas un zip", MDP)


# --- Refus : structure ----------------------------------------------------

def test_archive_sans_project_json_est_refusee():
    donnees = _archive_maison({"targets/x.conf": b"rien"})
    with pytest.raises(archive.ArchiveInvalide, match="project.json absent"):
        archive.lire_archive(donnees, MDP)


def test_project_json_illisible_est_refuse():
    donnees = _archive_maison({"project.json": b"{ceci n'est pas du JSON"})
    with pytest.raises(archive.ArchiveInvalide, match="illisible"):
        archive.lire_archive(donnees, MDP)


def test_project_json_qui_n_est_pas_un_objet_est_refuse():
    donnees = _archive_maison({"project.json": json.dumps([1, 2, 3]).encode()})
    with pytest.raises(archive.ArchiveInvalide, match="n'est pas un objet"):
        archive.lire_archive(donnees, MDP)


# --- Refus : Zip Slip (traversée de chemin) -------------------------------

@pytest.mark.parametrize("nom_malveillant", [
    "../evasion.txt",
    "../../../etc/passwd",
    "targets/../../evasion.txt",
    "/etc/passwd",
])
def test_zip_slip_est_refuse_a_l_ecriture(tmp_path, nom_malveillant):
    donnees = _archive_maison({
        "project.json": json.dumps({"id": "x"}).encode(),
        nom_malveillant: b"charge utile",
    })
    _, fichiers = archive.lire_archive(donnees, MDP)

    destination = tmp_path / "cible"
    with pytest.raises(archive.ArchiveInvalide, match="refusé"):
        archive.ecrire_fichiers(fichiers, destination)


@pytest.mark.parametrize("nom_malveillant", [
    "..\\..\\windows\\evil.txt",
    "sous\\dossier.txt",
    "\\\\serveur\\partage\\fichier.txt",
])
def test_l_antislash_est_refuse_quel_que_soit_le_systeme(tmp_path, nom_malveillant):
    """La validation est testée directement, pas au travers d'un aller-retour
    ZIP : `zipfile` normalise les antislashs en `/` sous Windows mais les laisse
    tels quels sous Linux, ce qui rendrait le test dépendant du système.

    Or c'est précisément le point : une entrée contenant un antislash est un
    simple nom de fichier sous Linux, mais traverse à l'extraction sous Windows.
    La spécification ZIP impose `/` — l'antislash est donc refusé partout.
    Écart relevé par la CI Linux le 29/07/2026, invisible en développement
    sous Windows.
    """
    with pytest.raises(archive.ArchiveInvalide, match="antislash"):
        archive._nom_sur(nom_malveillant, tmp_path / "cible")


def test_un_nom_d_entree_legitime_est_accepte(tmp_path):
    destination = tmp_path / "cible"
    cible = archive._nom_sur("targets/sshd_config", destination)
    assert cible == (destination / "targets" / "sshd_config").resolve()


def test_aucun_fichier_n_est_ecrit_hors_de_la_destination(tmp_path):
    """Vérifie l'effet réel, pas seulement la levée d'exception."""
    sentinelle = tmp_path / "sentinelle.txt"
    donnees = _archive_maison({
        "project.json": json.dumps({"id": "x"}).encode(),
        "../sentinelle.txt": b"COMPROMIS",
    })
    _, fichiers = archive.lire_archive(donnees, MDP)

    destination = tmp_path / "cible"
    with pytest.raises(archive.ArchiveInvalide):
        archive.ecrire_fichiers(fichiers, destination)

    assert not sentinelle.exists(), "un fichier a été écrit hors de la destination"


# --- Refus : bombe de décompression ---------------------------------------

def test_bombe_de_decompression_est_refusee(monkeypatch):
    """Plafond volontairement abaissé pour le test : on vérifie la logique,
    pas la capacité à générer réellement 200 Mo."""
    monkeypatch.setattr(archive, "TAILLE_MAX_DECOMPRESSEE", 1024)
    donnees = _archive_maison({
        "project.json": json.dumps({"id": "x"}).encode(),
        "gros.bin": b"A" * 5000,
    })
    with pytest.raises(archive.ArchiveInvalide, match="décompressés|plafond"):
        archive.lire_archive(donnees, MDP)


def test_une_archive_de_taille_normale_passe_le_plafond(mission):
    donnees = archive.export_archive(mission, MDP)
    state, _ = archive.lire_archive(donnees, MDP)  # ne doit pas lever
    assert state["id"] == "acme"
