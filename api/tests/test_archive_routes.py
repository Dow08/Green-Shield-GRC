"""Tests des routes d'export/import d'archive de mission."""
from __future__ import annotations

import asyncio
import io
import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import archive, projects  # noqa: E402

MDP = "mot-de-passe-mission"


@pytest.fixture()
def registre(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    p_dir = tmp_path / "acme"
    (p_dir / "targets").mkdir(parents=True)
    (p_dir / "reports").mkdir(parents=True)
    (p_dir / "project.json").write_text(
        json.dumps({"id": "acme", "name": "Acme", "client": "Acme Corp", "steps": {}}),
        encoding="utf-8",
    )
    (p_dir / "targets" / "sshd_config").write_text("Port 22\n", encoding="utf-8")
    return tmp_path


def _importer(donnees: bytes, password: str = MDP, filename: str = "mission.zip") -> dict:
    upload = UploadFile(io.BytesIO(donnees), filename=filename)
    return asyncio.run(projects.import_project_archive(file=upload, password=password))


# --- Export ---------------------------------------------------------------

def test_export_renvoie_un_zip_en_piece_jointe(registre):
    reponse = projects.export_project_archive("acme", {"password": MDP})
    assert reponse.media_type == "application/zip"
    assert "attachment" in reponse.headers["content-disposition"]
    assert "mission_acme.zip" in reponse.headers["content-disposition"]
    assert reponse.body[:2] == b"PK"


def test_export_sur_mission_introuvable_renvoie_404(registre):
    with pytest.raises(HTTPException) as exc:
        projects.export_project_archive("inexistante", {"password": MDP})
    assert exc.value.status_code == 404


def test_export_sans_mot_de_passe_renvoie_400(registre):
    with pytest.raises(HTTPException) as exc:
        projects.export_project_archive("acme", {"password": ""})
    assert exc.value.status_code == 400


def test_export_avec_p_id_traverse_est_rejete(registre):
    with pytest.raises(HTTPException) as exc:
        projects.export_project_archive("..", {"password": MDP})
    assert exc.value.status_code == 400


# --- Import ---------------------------------------------------------------

def test_import_restaure_une_mission_supprimee(registre):
    """Le scénario qui justifie F14 : perte de la mission, restauration depuis
    l'archive."""
    donnees = projects.export_project_archive("acme", {"password": MDP}).body

    import shutil
    shutil.rmtree(registre / "acme")
    assert not (registre / "acme").exists()

    state = _importer(donnees)

    assert state["id"] == "acme"
    assert state["client"] == "Acme Corp"
    assert (registre / "acme" / "project.json").is_file()
    assert (registre / "acme" / "targets" / "sshd_config").read_text(encoding="utf-8") == "Port 22\n"


def test_import_applique_la_migration_de_schema(registre):
    """Une archive d'une version antérieure doit ressortir au schéma courant."""
    donnees = projects.export_project_archive("acme", {"password": MDP}).body
    import shutil
    shutil.rmtree(registre / "acme")

    state = _importer(donnees)

    from modules import schema_migration
    assert state["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert "temps" in state["socle"]


def test_import_refuse_d_ecraser_une_mission_existante(registre):
    donnees = projects.export_project_archive("acme", {"password": MDP}).body
    with pytest.raises(HTTPException) as exc:
        _importer(donnees)
    assert exc.value.status_code == 409


def test_import_avec_mauvais_mot_de_passe_renvoie_400(registre):
    donnees = projects.export_project_archive("acme", {"password": MDP}).body
    import shutil
    shutil.rmtree(registre / "acme")

    with pytest.raises(HTTPException) as exc:
        _importer(donnees, password="mauvais")
    assert exc.value.status_code == 400


def test_import_d_un_fichier_qui_n_est_pas_une_archive_renvoie_400(registre):
    with pytest.raises(HTTPException) as exc:
        _importer(b"pas un zip du tout")
    assert exc.value.status_code == 400


def test_import_ne_laisse_pas_de_mission_partielle_en_cas_d_echec(registre, monkeypatch):
    """Si l'écriture échoue à mi-parcours, aucun répertoire de mission
    incomplet ne doit subsister."""
    donnees = projects.export_project_archive("acme", {"password": MDP}).body
    import shutil
    shutil.rmtree(registre / "acme")

    def echoue(*args, **kwargs):
        raise OSError("disque plein")

    monkeypatch.setattr(archive, "ecrire_fichiers", echoue)
    with pytest.raises(HTTPException) as exc:
        _importer(donnees)
    assert exc.value.status_code == 500
    assert not (registre / "acme").exists(), "mission partielle laissée sur disque"


def test_import_avec_flux_brut_trop_volumineux_est_rejete(registre, monkeypatch):
    """V-07 (audit combiné du 06/08/2026) : `await file.read()` chargeait le
    flux brut en mémoire sans plafond, avant même que `archive.lire_archive`
    ait la moindre chance de contrôler la taille décompressée."""
    monkeypatch.setattr(projects.crud, "TAILLE_MAX_UPLOAD_ARCHIVE", 1024)
    with pytest.raises(HTTPException) as exc:
        _importer(b"A" * 5000)
    assert exc.value.status_code == 413


def test_import_d_une_archive_a_identifiant_malveillant_est_rejete(registre):
    """L'identifiant vient de l'archive : il reste une donnée non fiable."""
    tampon = io.BytesIO()
    import pyzipper
    with pyzipper.AESZipFile(tampon, "w", compression=pyzipper.ZIP_DEFLATED,
                             encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(MDP.encode())
        zf.writestr("project.json", json.dumps({"id": "../evasion"}))

    with pytest.raises(HTTPException) as exc:
        _importer(tampon.getvalue())
    assert exc.value.status_code == 400
    assert not (registre.parent / "evasion").exists()
