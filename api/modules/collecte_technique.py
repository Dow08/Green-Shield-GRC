"""Module Collecte technique — Recon & empreinte de configuration.

Rôle strictement distinct d'AuditCraft-GRC : ce module ne rend AUCUN verdict de
conformité, il se contente d'identifier factuellement un fichier de
configuration (type de service, réglages présents, version si détectable) pour
alimenter le registre des Biens Supports (Phase 1) d'une mission. Le jugement
de conformité reste le rôle d'AuditCraft-GRC ; l'analyse de risque reste le
rôle d'EBIOS RM. Ici : inventaire, rien d'autre.

Parsing 100 % hors-ligne et tolérant, dans le même esprit que
`auditcraft_grc/parser.py` : une ligne malformée ou un format non reconnu ne
lève jamais d'exception, il retombe simplement sur un résultat générique.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml
from fastapi import APIRouter, HTTPException

from . import projects
from . import audit_log
from . import path_safety
from .auditcraft_grc import parser as sshd_nginx_parser

router = APIRouter(prefix="/api")

MODULE = {
    "id": "collecte_technique",
    "name": "Collecte technique",
    "icon": "collect",
    "category": "Reconnaissance",
    "description": "Recon & empreinte de configuration alimentant le registre.",
    "status": "active",
    "endpoint": "/api/collecte/fingerprint",
}


@dataclass(frozen=True)
class SuggestedAsset:
    name: str
    type: str
    description: str
    owner: str = ""


@dataclass(frozen=True)
class Fingerprint:
    filename: str
    detected_type: str
    service: str
    version: str | None
    directive_count: int
    flags: list[str] = field(default_factory=list)
    suggested_asset: SuggestedAsset = field(default_factory=lambda: SuggestedAsset("", "", ""))

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "detected_type": self.detected_type,
            "service": self.service,
            "version": self.version,
            "directive_count": self.directive_count,
            "flags": self.flags,
            "suggested_asset": {
                "name": self.suggested_asset.name,
                "type": self.suggested_asset.type,
                "description": self.suggested_asset.description,
                "owner": self.suggested_asset.owner,
            },
        }


# --- Détection du type de fichier (par contenu, pas seulement par nom) -----

_SIGNATURES: dict[str, list[re.Pattern]] = {
    "sshd_config": [re.compile(p, re.MULTILINE) for p in (
        r"^\s*PermitRootLogin\b", r"^\s*PasswordAuthentication\b", r"^\s*ChallengeResponseAuthentication\b",
        r"^\s*Subsystem\s+sftp\b",
    )],
    "nginx": [re.compile(p, re.MULTILINE) for p in (
        r"\bserver\s*\{", r"\blocation\s+[^\{]*\{", r"\bserver_name\s+", r"\bproxy_pass\s+",
    )],
    "apache": [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in (
        r"<VirtualHost\b", r"^\s*LoadModule\b", r"^\s*DocumentRoot\b", r"^\s*ServerRoot\b",
    )],
    "mysql": [re.compile(p, re.MULTILINE) for p in (
        r"^\[mysqld\]", r"^\[mariadb\]", r"^\s*innodb_buffer_pool_size\b",
    )],
    "postgresql": [re.compile(p, re.MULTILINE) for p in (
        r"^\s*listen_addresses\s*=", r"^\s*max_connections\s*=", r"^\s*shared_buffers\s*=",
    )],
    "docker_compose": [re.compile(p, re.MULTILINE) for p in (
        r"^\s*services\s*:", r"^\s*image\s*:", r"^\s*version\s*:\s*[\"']?\d",
    )],
    "os_release": [re.compile(p, re.MULTILINE) for p in (
        r"^PRETTY_NAME=", r"^VERSION_ID=", r"^ID=",
    )],
}


def detect_type(filename: str, content: str) -> str:
    """Détecte le type de configuration par signatures de contenu (robuste au
    renommage de fichier), avec repli sur l'extension/le nom si aucune
    signature ne matche assez fort."""
    scores = {kind: sum(1 for sig in sigs if sig.search(content)) for kind, sigs in _SIGNATURES.items()}
    best_kind, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score >= 2:
        return best_kind

    lower_name = filename.lower()
    if "sshd" in lower_name:
        return "sshd_config"
    if "nginx" in lower_name:
        return "nginx"
    if "apache" in lower_name or "httpd" in lower_name:
        return "apache"
    if "my.cnf" in lower_name or "mysql" in lower_name or "mariadb" in lower_name:
        return "mysql"
    if "postgresql.conf" in lower_name or "postgres" in lower_name:
        return "postgresql"
    if "docker-compose" in lower_name or "compose.y" in lower_name:
        return "docker_compose"
    if "os-release" in lower_name:
        return "os_release"
    return "inconnu"


# --- Extraction factuelle par type ------------------------------------------

def _fingerprint_sshd(filename: str, content: str) -> Fingerprint:
    directives = sshd_nginx_parser.parse_sshd(content)
    watched = ["Port", "PermitRootLogin", "PasswordAuthentication", "X11Forwarding", "PermitEmptyPasswords"]
    flags = []
    for key in watched:
        d = sshd_nginx_parser.effective(directives, key)
        if d is not None:
            flags.append(f"{d.key} {d.value}")
    return Fingerprint(
        filename=filename,
        detected_type="sshd_config",
        service="Service SSH (OpenSSH)",
        version=None,
        directive_count=len(directives),
        flags=flags,
        suggested_asset=SuggestedAsset(
            name="Serveur SSH (OpenSSH)",
            type="Réseau",
            description=f"Accès distant administrateur — {len(directives)} directive(s) relevée(s) dans {filename}.",
        ),
    )


def _fingerprint_nginx(filename: str, content: str) -> Fingerprint:
    directives = sshd_nginx_parser.parse_nginx(content)
    watched = ["server_name", "listen", "ssl_protocols", "add_header", "proxy_pass"]
    flags = []
    for key in watched:
        d = sshd_nginx_parser.effective(directives, key)
        if d is not None:
            flags.append(f"{d.key} {d.value}")
    return Fingerprint(
        filename=filename,
        detected_type="nginx",
        service="Serveur web (Nginx)",
        version=None,
        directive_count=len(directives),
        flags=flags,
        suggested_asset=SuggestedAsset(
            name="Serveur web (Nginx)",
            type="Logiciel",
            description=f"Reverse-proxy / serveur web — {len(directives)} directive(s) relevée(s) dans {filename}.",
        ),
    )


_KV_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.]*)\s+([^\r\n#]+)", re.MULTILINE)


def _fingerprint_apache(filename: str, content: str) -> Fingerprint:
    watched = ["ServerRoot", "DocumentRoot", "ServerName", "Listen"]
    flags = []
    for key in watched:
        m = re.search(rf"^\s*{key}\s+(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if m:
            flags.append(f"{key} {m.group(1).strip()}")
    module_count = len(re.findall(r"^\s*LoadModule\b", content, re.MULTILINE | re.IGNORECASE))
    return Fingerprint(
        filename=filename,
        detected_type="apache",
        service="Serveur web (Apache HTTPD)",
        version=None,
        directive_count=len(_KV_LINE.findall(content)),
        flags=flags + ([f"{module_count} module(s) chargé(s) (LoadModule)"] if module_count else []),
        suggested_asset=SuggestedAsset(
            name="Serveur web (Apache HTTPD)",
            type="Logiciel",
            description=f"Serveur HTTP Apache — relevé dans {filename}.",
        ),
    )


def _fingerprint_mysql(filename: str, content: str) -> Fingerprint:
    watched = ["port", "bind-address", "datadir", "innodb_buffer_pool_size"]
    flags = []
    for key in watched:
        m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if m:
            flags.append(f"{key} = {m.group(1).strip()}")
    return Fingerprint(
        filename=filename,
        detected_type="mysql",
        service="Base de données (MySQL / MariaDB)",
        version=None,
        directive_count=len(_KV_LINE.findall(content)),
        flags=flags,
        suggested_asset=SuggestedAsset(
            name="Base de données (MySQL / MariaDB)",
            type="Logiciel",
            description=f"SGBD relationnel — relevé dans {filename}.",
        ),
    )


def _fingerprint_postgresql(filename: str, content: str) -> Fingerprint:
    watched = ["listen_addresses", "port", "max_connections", "ssl"]
    flags = []
    for key in watched:
        m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if m:
            flags.append(f"{key} = {m.group(1).strip()}")
    return Fingerprint(
        filename=filename,
        detected_type="postgresql",
        service="Base de données (PostgreSQL)",
        version=None,
        directive_count=len(_KV_LINE.findall(content)),
        flags=flags,
        suggested_asset=SuggestedAsset(
            name="Base de données (PostgreSQL)",
            type="Logiciel",
            description=f"SGBD relationnel — relevé dans {filename}.",
        ),
    )


def _fingerprint_docker_compose(filename: str, content: str) -> Fingerprint:
    try:
        parsed = yaml.safe_load(content) or {}
    except yaml.YAMLError:
        parsed = {}
    services = parsed.get("services", {}) if isinstance(parsed, dict) else {}
    images = []
    if isinstance(services, dict):
        for svc_name, svc_def in services.items():
            if isinstance(svc_def, dict) and svc_def.get("image"):
                images.append(f"{svc_name}: {svc_def['image']}")
    version = None
    if images:
        first_image_ref = images[0].split(": ", 1)[-1]  # ex: "nginx:1.21"
        if ":" in first_image_ref:
            version = first_image_ref.split(":", 1)[1]
    return Fingerprint(
        filename=filename,
        detected_type="docker_compose",
        service="Orchestration conteneurs (Docker Compose)",
        version=version,
        directive_count=len(services) if isinstance(services, dict) else 0,
        flags=images,
        suggested_asset=SuggestedAsset(
            name=f"Stack Docker Compose ({len(images)} service(s))",
            type="Logiciel",
            description=f"Services conteneurisés relevés dans {filename} : " + (", ".join(images) if images else "aucune image identifiée."),
        ),
    )


_OS_RELEASE_LINE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)="?([^"\r\n]*)"?$', re.MULTILINE)


def _fingerprint_os_release(filename: str, content: str) -> Fingerprint:
    fields = dict(_OS_RELEASE_LINE.findall(content))
    pretty_name = fields.get("PRETTY_NAME") or fields.get("NAME") or "Système non identifié"
    version = fields.get("VERSION_ID") or fields.get("VERSION")
    return Fingerprint(
        filename=filename,
        detected_type="os_release",
        service=f"Système d'exploitation ({pretty_name})",
        version=version,
        directive_count=len(fields),
        flags=[f"{k}={v}" for k, v in fields.items() if k in ("ID", "VERSION_ID", "PRETTY_NAME")],
        suggested_asset=SuggestedAsset(
            name=pretty_name,
            type="Logiciel",
            description=f"Empreinte système relevée dans {filename}" + (f" (version {version})." if version else "."),
        ),
    )


def _fingerprint_inconnu(filename: str, content: str) -> Fingerprint:
    non_empty_lines = [l for l in content.splitlines() if l.strip()]
    return Fingerprint(
        filename=filename,
        detected_type="inconnu",
        service="Format non reconnu automatiquement",
        version=None,
        directive_count=len(non_empty_lines),
        flags=[],
        suggested_asset=SuggestedAsset(
            name=filename or "Actif non qualifié",
            type="Logiciel",
            description="Format non reconnu automatiquement — à qualifier manuellement par le consultant.",
        ),
    )


_FINGERPRINTERS = {
    "sshd_config": _fingerprint_sshd,
    "nginx": _fingerprint_nginx,
    "apache": _fingerprint_apache,
    "mysql": _fingerprint_mysql,
    "postgresql": _fingerprint_postgresql,
    "docker_compose": _fingerprint_docker_compose,
    "os_release": _fingerprint_os_release,
}


def fingerprint(filename: str, content: str) -> Fingerprint:
    """Point d'entrée unique : détecte le type puis extrait une empreinte
    factuelle. Ne lève jamais d'exception — un contenu imprévu retombe sur le
    résultat générique 'inconnu'."""
    kind = detect_type(filename, content)
    fingerprinter = _FINGERPRINTERS.get(kind, _fingerprint_inconnu)
    try:
        return fingerprinter(filename, content)
    except Exception:
        return _fingerprint_inconnu(filename, content)


# --- Routes API ---------------------------------------------------------

@router.post("/collecte/fingerprint")
def run_fingerprint(data: dict) -> dict:
    filename = data.get("filename", "config")
    content = data.get("content", "")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Aucun contenu à analyser")
    return fingerprint(filename, content).to_dict()


def _next_bs_id(assets_support: list[dict]) -> str:
    existing = {a.get("id", "") for a in assets_support}
    numeric = [int(m.group(1)) for a in existing if (m := re.fullmatch(r"BS-(\d+)", a))]
    next_n = (max(numeric) + 1) if numeric else 1
    candidate = f"BS-{next_n:02d}"
    while candidate in existing:
        next_n += 1
        candidate = f"BS-{next_n:02d}"
    return candidate


@router.post("/projects/{p_id}/collecte/import")
def import_asset_into_registry(p_id: str, data: dict) -> dict:
    """Ajoute un actif (issu d'une empreinte, validée/éditée par le consultant)
    au registre des Biens Supports (Phase 1) de la mission choisie."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = projects.PROJECTS_DIR / p_id
    state_file = p_dir / "project.json"
    if not state_file.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Le nom de l'actif est obligatoire")

    try:
        state = projects._read_state(state_file)
        cadrage = state.setdefault("steps", {}).setdefault("cadrage", {})
        assets_support = cadrage.setdefault("assets_support", [])
        bs_id = _next_bs_id(assets_support)
        assets_support.append({
            "id": bs_id,
            "name": name,
            "type": data.get("type") or "Logiciel",
            "description": data.get("description", ""),
            "owner": data.get("owner", ""),
        })
        state["progress"] = projects.calculate_progress(state)
        projects._write_json_atomic(state_file, state)
        audit_log.record("collecte.import", target=p_id, detail=f"asset={bs_id}")
        return state
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
