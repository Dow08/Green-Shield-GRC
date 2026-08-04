import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from .projects.crud import get_project_db, update_project_db
from .database.models import User
from .auth import get_current_user
from . import path_safety

router = APIRouter(prefix="/api/connectors", tags=["connectors"])
logger = logging.getLogger(__name__)

class ConnectorScanResult(BaseModel):
    connector_id: str
    status: str
    updates_count: int
    details: str

# `scan_connectors` (POST /{project_id}/scan) supprimée le 31/07/2026 : sous
# couvert de « connecteur M365/AWS/GitHub », la route ne faisait jamais
# aucun appel réel (juste un `time.sleep`) et écrivait un texte de preuve
# entièrement fabriqué directement dans les contrôles ISO 27001 de la
# mission, marqués « fait » — contraire à la philosophie « zéro invention »
# du projet, sur une route qui n'était même pas cantonnée à la mission de
# démonstration. Décision utilisateur : supprimer plutôt que corriger.

from .red_shield_parser import RedShieldExport
from .audit_log import record

@router.post("/{project_id}/redshield", response_model=ConnectorScanResult)
def import_red_shield(project_id: str, payload: RedShieldExport, current_user: User = Depends(get_current_user)):
    project_id = path_safety.safe_path_component(project_id, "identifiant de mission")
    project = get_project_db(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    # In Green Shield, the project data is often managed via read_state / write_state on project.json directly
    # Let's see how the project handles technical_findings
    # project dict usually has "steps" etc., but let's just use the state file.
    
    # Wait, the read_state expects a Path. Connectors currently use get_project_db which returns a dict.
    # Let's stick to update_project_db
    
    technical_findings = {
        "assets": [a.model_dump() for a in payload.assets],
        "vulnerabilities": [v.model_dump() for v in payload.vulnerabilities],
        "security_controls": payload.security_controls.model_dump() if payload.security_controls else {}
    }
    
    project["technical_findings"] = technical_findings
    
    update_project_db(project_id, project)
    
    record("project.connector.redshield", target=project_id, detail=f"Imported {len(payload.assets)} assets and {len(payload.vulnerabilities)} vulnerabilities")
    
    return ConnectorScanResult(
        connector_id="red_shield",
        status="success",
        updates_count=len(payload.assets) + len(payload.vulnerabilities),
        details=f"Importé {len(payload.assets)} biens supports et {len(payload.vulnerabilities)} vulnérabilités factuelles depuis Red Shield."
    )
