"""Tests du module Collecte technique : détection/empreinte de configuration
(inventaire factuel, sans jugement de conformité) et import dans le registre
des Biens Supports d'une mission."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import collecte_technique as ct  # noqa: E402
from modules import projects  # noqa: E402


# --- Détection & empreinte ---------------------------------------------

def test_detecte_un_sshd_config_par_son_contenu_meme_avec_un_nom_quelconque():
    content = "Port 22\nPermitRootLogin yes\nPasswordAuthentication yes\nSubsystem sftp /usr/lib/openssh/sftp-server\n"
    fp = ct.fingerprint("fichier_client_42.txt", content)
    assert fp.detected_type == "sshd_config"
    assert fp.service == "Service SSH (OpenSSH)"
    assert fp.directive_count == 4
    assert "PermitRootLogin yes" in fp.flags
    assert fp.suggested_asset.type == "Réseau"


def test_detecte_un_nginx_par_son_contenu():
    content = "server {\n  listen 80;\n  server_name example.com;\n  location / { proxy_pass http://127.0.0.1:8000; }\n}\n"
    fp = ct.fingerprint("conf.d/default", content)
    assert fp.detected_type == "nginx"
    assert any(f.startswith("server_name") for f in fp.flags)


def test_detecte_apache_et_compte_les_modules_charges():
    content = (
        "ServerRoot \"/etc/apache2\"\n"
        "LoadModule ssl_module modules/mod_ssl.so\n"
        "LoadModule rewrite_module modules/mod_rewrite.so\n"
        "<VirtualHost *:80>\n  DocumentRoot /var/www/html\n</VirtualHost>\n"
    )
    fp = ct.fingerprint("apache2.conf", content)
    assert fp.detected_type == "apache"
    assert any("2 module(s)" in f for f in fp.flags)


def test_detecte_mysql_par_la_section_mysqld():
    content = "[mysqld]\nport = 3306\nbind-address = 0.0.0.0\ndatadir = /var/lib/mysql\n"
    fp = ct.fingerprint("my.cnf", content)
    assert fp.detected_type == "mysql"
    assert "bind-address = 0.0.0.0" in fp.flags


def test_detecte_postgresql_par_ses_reglages_caracteristiques():
    content = "listen_addresses = '*'\nmax_connections = 100\nshared_buffers = 128MB\n"
    fp = ct.fingerprint("postgresql.conf", content)
    assert fp.detected_type == "postgresql"


def test_docker_compose_extrait_les_images_et_la_version_du_premier_service():
    content = (
        "version: \"3.8\"\n"
        "services:\n"
        "  web:\n"
        "    image: nginx:1.21\n"
        "  db:\n"
        "    image: postgres:15\n"
    )
    fp = ct.fingerprint("docker-compose.yml", content)
    assert fp.detected_type == "docker_compose"
    assert fp.version == "1.21"
    assert fp.directive_count == 2
    assert "web: nginx:1.21" in fp.flags
    assert "db: postgres:15" in fp.flags


def test_os_release_extrait_le_nom_et_la_version():
    content = 'NAME="Ubuntu"\nVERSION_ID="22.04"\nPRETTY_NAME="Ubuntu 22.04.3 LTS"\nID=ubuntu\n'
    fp = ct.fingerprint("os-release", content)
    assert fp.detected_type == "os_release"
    assert fp.version == "22.04"
    assert fp.suggested_asset.name == "Ubuntu 22.04.3 LTS"


def test_contenu_non_reconnu_retombe_sur_le_type_inconnu_sans_planter():
    fp = ct.fingerprint("mystere.bin", "texte quelconque\nsans signature connue\n")
    assert fp.detected_type == "inconnu"
    assert fp.suggested_asset.description.startswith("Format non reconnu")


def test_contenu_vide_ne_plante_pas():
    fp = ct.fingerprint("vide.conf", "")
    assert fp.detected_type == "inconnu"
    assert fp.directive_count == 0


def test_yaml_docker_compose_malforme_ne_plante_pas():
    fp = ct.fingerprint("docker-compose.yml", "services:\n  web:\n    image: [unclosed\n")
    # Repli silencieux : pas d'exception, on obtient une empreinte (docker_compose vide ou inconnu)
    assert fp.filename == "docker-compose.yml"


# --- Endpoint /api/collecte/fingerprint ---------------------------------

def test_endpoint_fingerprint_retourne_le_dict_serialisable():
    result = ct.run_fingerprint({"filename": "sshd_config", "content": "Port 22\nPermitRootLogin yes\n"})
    assert result["detected_type"] == "sshd_config"
    assert isinstance(result["flags"], list)


def test_endpoint_fingerprint_rejette_un_contenu_vide():
    with pytest.raises(HTTPException) as exc_info:
        ct.run_fingerprint({"filename": "x", "content": "   "})
    assert exc_info.value.status_code == 400


# --- Import dans le registre (Biens Supports, Phase 1) ------------------

@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    p_dir = tmp_path / "acme"
    p_dir.mkdir()
    (p_dir / "project.json").write_text(
        json.dumps({
            "id": "acme", "name": "Acme", "client": "Acme Corp", "type": "grc",
            "steps": {"cadrage": {"assets_support": [{"id": "BS-01", "name": "Existant", "type": "Logiciel", "description": "", "owner": ""}]}},
        }),
        encoding="utf-8",
    )
    return "acme"


def test_import_ajoute_l_actif_au_registre_avec_un_id_unique(project_dir):
    result = ct.import_asset_into_registry(project_dir, {
        "name": "Serveur SSH (OpenSSH)", "type": "Réseau", "description": "Relevé via collecte", "owner": "RSSI",
    })
    assets = result["steps"]["cadrage"]["assets_support"]
    assert len(assets) == 2
    nouveau = assets[-1]
    assert nouveau["id"] == "BS-02"  # BS-01 déjà pris, prochain numéro libre
    assert nouveau["name"] == "Serveur SSH (OpenSSH)"
    assert nouveau["owner"] == "RSSI"


def test_import_persiste_sur_disque(project_dir, tmp_path):
    ct.import_asset_into_registry(project_dir, {"name": "Nginx", "type": "Logiciel", "description": "", "owner": ""})
    saved = json.loads((tmp_path / project_dir / "project.json").read_text(encoding="utf-8"))
    assert len(saved["steps"]["cadrage"]["assets_support"]) == 2


def test_import_sans_nom_est_rejete(project_dir):
    with pytest.raises(HTTPException) as exc_info:
        ct.import_asset_into_registry(project_dir, {"name": "  ", "type": "Logiciel"})
    assert exc_info.value.status_code == 400


def test_import_sur_projet_introuvable_renvoie_404(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    with pytest.raises(HTTPException) as exc_info:
        ct.import_asset_into_registry("does_not_exist", {"name": "X"})
    assert exc_info.value.status_code == 404


def test_import_avec_p_id_traverse_est_rejete(tmp_path, monkeypatch):
    """Non-régression : audit du 28/07/2026 — p_id non assaini permettait de
    remonter hors de PROJECTS_DIR (même défaut que V-02 dans projects.py)."""
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    with pytest.raises(HTTPException) as exc_info:
        ct.import_asset_into_registry("..", {"name": "X"})
    assert exc_info.value.status_code == 400


def test_next_bs_id_ignore_les_ids_non_numeriques_et_evite_les_collisions():
    assets = [{"id": "BS-AD"}, {"id": "BS-01"}, {"id": "BS-03"}]
    assert ct.ids.next_id("BS", assets) == "BS-04"


def test_next_bs_id_sur_registre_vide():
    assert ct.ids.next_id("BS", []) == "BS-01"
