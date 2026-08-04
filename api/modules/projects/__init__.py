from __future__ import annotations
import os
import json
import shutil
from pathlib import Path
from cryptography.fernet import Fernet

import yaml
from .. import data_paths
from .. import ressources
from .. import schema_migration
from .. import audit_log
from .. import tprm

PROJECTS_DIR = data_paths.resolve_projects_dir()
FRAMEWORKS_DIR = ressources.frameworks_dir()
_LEGACY_PROJECTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "projects"

_STORAGE_KEY = os.environ.get("GREENSHIELD_STORAGE_KEY")
_fernet = Fernet(_STORAGE_KEY) if _STORAGE_KEY else None

def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    if _fernet:
        content = _fernet.encrypt(json_str.encode("utf-8"))
    else:
        content = json_str.encode("utf-8")
        
    tmp.write_bytes(content)
    os.replace(tmp, path)

def _read_state(path: Path) -> dict:
    content = path.read_bytes()
    if _fernet:
        try:
            content = _fernet.decrypt(content)
        except Exception:
            # Fallback for unencrypted files read with a key
            pass
            
    state = json.loads(content.decode("utf-8"))
    state = schema_migration.migrate(state)
    if "progress" not in state:
        state["progress"] = calculate_progress(state)
    return state

def _migrate_legacy_projects() -> None:
    if not _LEGACY_PROJECTS_DIR.is_dir() or _LEGACY_PROJECTS_DIR == PROJECTS_DIR:
        return

    marqueur = PROJECTS_DIR / ".legacy-migre"
    if marqueur.exists():
        return

    for legacy in _LEGACY_PROJECTS_DIR.iterdir():
        if not (legacy / "project.json").is_file():
            continue
        target = PROJECTS_DIR / legacy.name
        if target.exists():
            continue
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(legacy, target)
        audit_log.record("legacy.migrate", target=legacy.name)

    try:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        marqueur.write_text(
            "Migration depuis l'ancien emplacement effectuée.\n",
            encoding="utf-8",
        )
    except OSError:
        pass

PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
_migrate_legacy_projects()

def _tprm_rate(dependence: int, penetration: int, maturity: int, trust: int) -> dict:
    return tprm.ratio_anssi(dependence, penetration, maturity, trust)

def get_framework_by_id(fw_id: str) -> dict | None:
    fw_path = FRAMEWORKS_DIR / f"{fw_id}.yaml"
    if not fw_path.exists():
        fw_path = FRAMEWORKS_DIR / "custom" / f"{fw_id}.yaml"
        if not fw_path.exists():
            return None
    try:
        return yaml.safe_load(fw_path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _rempli(valeur) -> bool:
    if isinstance(valeur, str):
        return bool(valeur.strip())
    if isinstance(valeur, (list, dict)):
        return len(valeur) > 0
    return valeur is not None

def calculate_progress(state: dict) -> int:
    steps = state.get("steps", {}) or {}
    def phase(cle: str) -> dict:
        return steps.get(cle) or {}

    jalons = (
        (5, _rempli(phase("cadrage").get("scope"))),
        (5, phase("cadrage").get("nda_signed")),
        (5, _rempli(phase("cadrage").get("assets_metier"))),
        (5, _rempli(phase("cadrage").get("assets_support"))),
        (5, _rempli(phase("diagnostic").get("rgpd_register"))),
        (5, phase("diagnostic").get("aipd_required") is not None),
        (5, (not phase("diagnostic").get("aipd_required")) or _rempli((phase("diagnostic").get("aipd") or {}).get("risks_eval"))),
        (15, _rempli(phase("tprm").get("tiers"))),
        (10, _rempli(phase("ebios").get("redoute_events"))),
        (10, _rempli(phase("ebios").get("operational_scenarios"))),
        (5, _rempli((phase("resilience").get("bcp_strategy") or {}).get("rto"))),
        (10, _rempli((phase("resilience").get("e3r") or {}).get("endiguement"))),
        (10, _rempli(phase("traitement").get("remediations"))),
        (5, _rempli((phase("restitution") or {}).get("exec_summary"))),
    )
    return min(sum(points for points, atteint in jalons if atteint), 100)

from .crud import *
from .exports import *
from .snapshots_routes import *
from .exports import _call_gemini_copilot
