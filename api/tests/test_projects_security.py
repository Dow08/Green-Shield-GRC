"""Tests de non-régression pour les 5 vulnérabilités CRITIQUES confirmées par
PoC lors de l'audit combiné du 28/07/2026 et corrigées dans la foulée :

  V-02 : DELETE /api/projects/{p_id} — p_id=".." détruisait le répertoire
         PARENT de PROJECTS_DIR (shutil.rmtree non protégé).
  V-03 : POST /api/projects/{p_id}/upload — file.filename non assaini
         permettait une écriture arbitraire hors de targets/.
  V-04 : POST /api/frameworks/import — id non assaini permettait d'écraser
         un référentiel officiel (ex: iso27001.yaml) via "../iso27001".
  V-05 : signature "SHA256:{hash(p_id)}" sur le NDA/rapport d'audit — hash()
         Python natif, ni SHA256 ni reproductible.
  V-06 : GET /api/projects/{p_id}/export/{doc_type} — le nom de fichier
         exporté dérivait du champ libre "client", non assaini.

Chaque test reproduit exactement le vecteur confirmé par le PoC isolé de
l'audit (répertoire jetable, jamais les données réelles).
"""
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

from modules import projects, docx_export  # noqa: E402


@pytest.fixture()
def isolated_dirs(tmp_path, monkeypatch):
    projects_dir = tmp_path / "real_projects_dir"
    projects_dir.mkdir()
    frameworks_dir = tmp_path / "frameworks"
    (frameworks_dir / "custom").mkdir(parents=True)
    monkeypatch.setattr(projects, "PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", projects_dir, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", projects_dir, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", projects_dir, raising=False)
    monkeypatch.setattr(projects, "FRAMEWORKS_DIR", frameworks_dir)
    monkeypatch.setattr(projects.crud, "FRAMEWORKS_DIR", frameworks_dir, raising=False)
    monkeypatch.setattr(projects.exports, "FRAMEWORKS_DIR", frameworks_dir, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "FRAMEWORKS_DIR", frameworks_dir, raising=False)
    return tmp_path


@pytest.fixture()
def legit_project(isolated_dirs):
    p_dir = projects.PROJECTS_DIR / "legit"
    p_dir.mkdir()
    (p_dir / "targets").mkdir()
    (p_dir / "reports").mkdir()
    (p_dir / "project.json").write_text(
        json.dumps({"id": "legit", "name": "Legit", "client": "Legit Corp", "steps": {}}),
        encoding="utf-8",
    )
    return "legit"


# --- V-02 : delete_project / get_project / update_project ------------------

def test_v02_delete_project_avec_traversee_est_rejete(isolated_dirs):
    with pytest.raises(HTTPException) as exc_info:
        projects.delete_project("..")
    assert exc_info.value.status_code == 400
    # Le répertoire parent de PROJECTS_DIR doit être intact.
    assert isolated_dirs.is_dir()
    assert (isolated_dirs / "real_projects_dir").is_dir()


def test_v02_get_project_avec_traversee_est_rejete(isolated_dirs):
    with pytest.raises(HTTPException) as exc_info:
        projects.get_project("../../etc")
    assert exc_info.value.status_code == 400


def test_v02_update_project_avec_traversee_est_rejete(isolated_dirs):
    with pytest.raises(HTTPException) as exc_info:
        projects.update_project("..", {"name": "x"})
    assert exc_info.value.status_code == 400


def test_delete_project_legitime_fonctionne_toujours(legit_project):
    result = projects.delete_project(legit_project)
    assert result["status"] == "ok"
    assert not (projects.PROJECTS_DIR / "legit").exists()


# --- update_project : validation Pydantic (audit du 31/07/2026, corrigé le 06/08/2026) --

def test_update_project_avec_corps_vide_est_rejete(legit_project):
    # Un corps sans "id"/"name" ne doit plus pouvoir écraser silencieusement
    # project.json avec un état vide.
    with pytest.raises(HTTPException) as exc_info:
        projects.update_project(legit_project, {})
    assert exc_info.value.status_code == 400


def test_update_project_avec_id_ne_correspondant_pas_a_l_url_est_rejete(legit_project):
    with pytest.raises(HTTPException) as exc_info:
        projects.update_project(legit_project, {"id": "une-autre-mission", "name": "Legit"})
    assert exc_info.value.status_code == 400
    # project.json n'a pas été modifié.
    sur_disque = projects._read_state(projects.PROJECTS_DIR / legit_project / "project.json")
    assert sur_disque["id"] == "legit"


def test_update_project_legitime_fonctionne_toujours(legit_project):
    result = projects.update_project(legit_project, {
        "id": legit_project, "name": "Legit", "client": "Legit Corp", "steps": {"cadrage": {"scope": "SI"}},
    })
    assert result["steps"]["cadrage"]["scope"] == "SI"


# --- V-03 : upload_file -------------------------------------------------

def test_v03_upload_avec_nom_de_fichier_traverse_reste_confine_dans_targets(legit_project):
    malicious_upload = UploadFile(io.BytesIO(b"PWNED"), filename="../../sentinel/pwned.txt")
    result = asyncio.run(projects.upload_file(legit_project, malicious_upload))
    # Le fichier est écrit avec son seul nom de base, dans targets/ — jamais
    # en dehors. Aucun "sentinel/" ne doit apparaître nulle part.
    written = list((projects.PROJECTS_DIR / legit_project / "targets").iterdir())
    assert [f.name for f in written] == ["pwned.txt"]
    assert result["steps"]["collecte"]["files"] == ["pwned.txt"]
    assert not (projects.PROJECTS_DIR.parent / "sentinel").exists()


def test_upload_avec_p_id_traverse_est_rejete(isolated_dirs):
    malicious_upload = UploadFile(io.BytesIO(b"x"), filename="ok.txt")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(projects.upload_file("..", malicious_upload))
    assert exc_info.value.status_code == 400


def test_upload_legitime_fonctionne_bien_toujours(legit_project):
    upload = UploadFile(io.BytesIO(b"Port 22\n"), filename="sshd_config")
    result = asyncio.run(projects.upload_file(legit_project, upload))
    assert result["steps"]["collecte"]["files"] == ["sshd_config"]
    assert (projects.PROJECTS_DIR / legit_project / "targets" / "sshd_config").read_text() == "Port 22\n"


# --- V-02 (audit combiné du 06/08/2026) : plafond de taille sur l'upload ---
# `shutil.copyfileobj` écrivait le flux brut sans aucune limite : un client
# pouvait saturer le disque avec un seul upload de fichier cible.

def test_upload_trop_volumineux_est_rejete(legit_project, monkeypatch):
    monkeypatch.setattr(projects.crud, "TAILLE_MAX_UPLOAD_FICHIER", 1024)
    upload = UploadFile(io.BytesIO(b"A" * 5000), filename="trop_gros.bin")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(projects.upload_file(legit_project, upload))
    assert exc_info.value.status_code == 413
    # Rien n'a été écrit sur disque : ni le fichier, ni une trace dans l'état.
    assert not (projects.PROJECTS_DIR / legit_project / "targets" / "trop_gros.bin").exists()


# --- V-04 : import_framework -------------------------------------------

def test_v04_import_framework_avec_traversee_est_rejete(isolated_dirs):
    (isolated_dirs / "frameworks" / "iso27001.yaml").write_text(
        "id: iso27001\nname: ORIGINAL\n", encoding="utf-8"
    )
    with pytest.raises(HTTPException) as exc_info:
        projects.import_framework({"id": "../iso27001", "name": "Malicious"})
    assert exc_info.value.status_code == 400
    # Le référentiel officiel n'a pas été écrasé.
    original = (isolated_dirs / "frameworks" / "iso27001.yaml").read_text(encoding="utf-8")
    assert "ORIGINAL" in original


def test_import_framework_legitime_fonctionne_toujours(isolated_dirs):
    result = projects.import_framework({"id": "mon_referentiel", "name": "Mon référentiel"})
    assert result["status"] == "ok"
    assert (isolated_dirs / "frameworks" / "custom" / "mon_referentiel.yaml").is_file()


def test_import_framework_avec_exigence_mal_formee_est_rejete(isolated_dirs):
    # Chaque exigence doit porter "id" et "title" (ExigenceImport) — un corps
    # dict brut n'importe quoi n'atterrit plus tel quel dans le YAML.
    with pytest.raises(HTTPException) as exc_info:
        projects.import_framework({
            "id": "mon_referentiel_2", "name": "Mon référentiel",
            "requirements": [{"titre_sans_accent": "manque id et title"}],
        })
    assert exc_info.value.status_code == 400
    assert not (isolated_dirs / "frameworks" / "custom" / "mon_referentiel_2.yaml").exists()


def test_import_framework_avec_exigences_valides_les_conserve(isolated_dirs):
    result = projects.import_framework({
        "id": "mon_referentiel_3", "name": "Mon référentiel",
        "requirements": [{"id": "REQ-01", "title": "Politique documentée"}],
    })
    assert result["status"] == "ok"
    contenu = (isolated_dirs / "frameworks" / "custom" / "mon_referentiel_3.yaml").read_text(encoding="utf-8")
    assert "REQ-01" in contenu
    assert "Politique documentée" in contenu


# --- V-05 : signature du NDA / rapport d'audit --------------------------

def test_v05_la_signature_est_un_vrai_sha256_reproductible(legit_project):
    doc = projects.export_project_document(legit_project, "nda")
    state = projects._read_state(projects.PROJECTS_DIR / legit_project / "project.json")
    expected = docx_export.data_fingerprint(state)
    assert expected in doc["markdown"]
    assert len(expected) == 64  # hexdigest SHA256
    # Recalculée à partir du même état, la signature doit être identique
    # (contrairement à hash(), qui varie par process).
    assert docx_export.data_fingerprint(state) == expected


def test_v05_signature_change_si_les_donnees_changent(legit_project):
    doc1 = projects.export_project_document(legit_project, "nda")
    state_file = projects.PROJECTS_DIR / legit_project / "project.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["client"] = "Client modifié"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    doc2 = projects.export_project_document(legit_project, "nda")
    assert doc1["markdown"] != doc2["markdown"]


# --- V-06 : export_project_document — filename dérivé de p_id, pas de client ---

def test_v06_export_ignore_les_caracteres_dangereux_du_champ_client(isolated_dirs):
    p_dir = projects.PROJECTS_DIR / "victime"
    p_dir.mkdir()
    (p_dir / "reports").mkdir()
    malicious_client = "../../../sentinel/exfil"
    (p_dir / "project.json").write_text(
        json.dumps({"id": "victime", "name": "V", "client": malicious_client, "steps": {}}),
        encoding="utf-8",
    )
    doc = projects.export_project_document("victime", "audit_report")
    # Le nom de fichier dérive de p_id (sûr), jamais du champ libre "client".
    # Le volet figure dans le nom : cette mission n'a pas de type, donc « Conseil ».
    assert doc["title"] == "Rapport_Audit_Conseil_victime.md"
    report_file = p_dir / "reports" / doc["title"]
    assert report_file.is_file()
    # Rien n'a été écrit hors de reports/.
    assert not (isolated_dirs / "real_projects_dir" / "sentinel").exists()


def test_export_project_document_avec_p_id_traverse_est_rejete(isolated_dirs):
    with pytest.raises(HTTPException) as exc_info:
        projects.export_project_document("..", "nda")
    assert exc_info.value.status_code == 400


# --- Routes .docx : passées en POST le 30/07/2026 --------------------------
#
# Le logo personnalisé (base64) transite désormais dans le corps de la
# requête plutôt qu'en paramètre de requête GET, qui ne le supporterait pas
# de façon fiable au-delà de quelques ko. Ces tests vérifient le branchement
# route -> report_docx.py : l'identité et le logo transmis dans `data`
# atteignent bien le document généré.

def test_export_project_nda_docx_transmet_l_identite_et_le_logo(legit_project):
    from docx import Document
    import io as io_module
    logo_perso = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY"
                  "42YAAAAASUVORK5CYII=")
    res = projects.export_project_nda_docx(
        legit_project, data={"auditeur": "Camille Martin", "cabinet": "Martin Cyber Audit", "logo": logo_perso})
    assert res.media_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    doc = Document(io_module.BytesIO(res.body))
    texte = "\n".join(" | ".join(c.text for c in r.cells) for t in doc.tables for r in t.rows)
    assert "Martin Cyber Audit" in texte
    assert "Camille Martin" in texte


def test_export_project_nda_docx_fonctionne_sans_identite_fournie(legit_project):
    """`data` par défaut : un consommateur qui n'envoie aucun corps ne doit
    pas faire planter la route."""
    res = projects.export_project_nda_docx(legit_project)
    assert res.status_code == 200


# --- Route SoA : 404 plutôt qu'un document vide et trompeur -----------------

def test_export_soa_docx_repond_404_sans_declaration_d_applicabilite(legit_project):
    """La mission `legit_project` n'a pas de référentiel ISO 27001 : générer
    un .docx quand même produirait un document trompeur (93 lignes vides)."""
    with pytest.raises(HTTPException) as exc_info:
        projects.export_project_soa_docx(legit_project)
    assert exc_info.value.status_code == 404


def test_export_soa_docx_fonctionne_quand_la_soa_existe(legit_project):
    from modules import soa as soa_module
    state_file = projects.PROJECTS_DIR / legit_project / "project.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["steps"]["evaluation"] = {"soa": soa_module.entrees_par_defaut()}
    state_file.write_text(json.dumps(state), encoding="utf-8")

    res = projects.export_project_soa_docx(legit_project)
    assert res.status_code == 200
    assert res.media_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
