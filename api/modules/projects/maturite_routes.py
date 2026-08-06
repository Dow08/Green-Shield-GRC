"""maturite_routes.py — routes du radar de maturité NIST CSF (auto-évaluation
déclarative du consultant), distinctes de la roue de rattachement servie
depuis crud.py (`get_nist_csf`).
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..database.models import User
from ..auth import get_current_user
from .. import maturite_nist
from .. import audit_log
from .. import path_safety
from ..schemas import coerce, UpdateMaturiteNistRequest
from .crud import _resolve_test_deps, _get_project_db_or_disk, update_project_db

router = APIRouter(prefix="/api")

CodeFonctionNist = Literal["GV", "ID", "PR", "DE", "RS", "RC"]


@router.get("/projects/{p_id}/maturite-nist")
def get_maturite_nist(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Radar de maturité NIST CSF déclaré : six fonctions, Tier 1-4 ou non évalué."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return maturite_nist.radar(state)


@router.put("/projects/{p_id}/maturite-nist/{code}")
def definir_maturite_nist(
    p_id: str, code: CodeFonctionNist, data: UpdateMaturiteNistRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
) -> dict:
    """Enregistre (ou réinitialise si tier=null) le Tier auto-déclaré d'une fonction."""
    data = coerce(UpdateMaturiteNistRequest, data)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    registre = state.setdefault("grc", {}).setdefault("maturite_nist", {})
    registre[code] = {"tier": data.tier, "justification": (data.justification or "").strip()}
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_project_db(p_id, state, db)
    audit_log.record("maturite_nist.definir", target=p_id, detail=f"{code} tier={data.tier}")
    return state
