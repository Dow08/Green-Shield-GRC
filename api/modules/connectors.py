import time
import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from .projects.crud import get_project_db, update_project_db

router = APIRouter(prefix="/api/connectors", tags=["connectors"])
logger = logging.getLogger(__name__)

class ConnectorScanResult(BaseModel):
    connector_id: str
    status: str
    updates_count: int
    details: str

class ConnectorScanRequest(BaseModel):
    connector_id: str

@router.post("/{project_id}/scan", response_model=ConnectorScanResult)
def scan_connectors(project_id: str, req: ConnectorScanRequest):
    """
    Simule le lancement d'un scan via un connecteur API.
    Met à jour automatiquement certaines étapes du référentiel ISO 27001
    avec des preuves remontées par l'API.
    """
    project = get_project_db(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    # On simule un délai réseau pour l'appel API
    time.sleep(1.5)

    grc = project.get("grc", {})
    parcours = grc.get("parcours", {})
    iso27001 = parcours.get("iso27001", {})

    updates = 0
    details = ""

    if req.connector_id == "microsoft_365":
        # Mock: M365 valide l'étape de contrôle d'accès
        # On va créer/mettre à jour l'étape "etape_a_9_4" (Contrôle d'accès)
        etape_id = "etape_a_9_4"
        existant = iso27001.get(etape_id, {"valeurs": {}})
        
        iso27001[etape_id] = {
            **existant,
            "statut": "fait",
            "valeurs": {
                **existant.get("valeurs", {}),
                "commentaire": "Validé automatiquement par l'API Microsoft 365. Le MFA est forcé sur 100% des comptes administrateurs.",
                "source": "api:microsoft_365"
            }
        }
        updates += 1
        details = "Contrôle d'accès (A.9.4) validé via Entra ID."

    elif req.connector_id == "aws":
        # Mock: AWS valide la cryptographie
        etape_id = "etape_a_10_1"
        existant = iso27001.get(etape_id, {"valeurs": {}})
        
        iso27001[etape_id] = {
            **existant,
            "statut": "fait",
            "valeurs": {
                **existant.get("valeurs", {}),
                "commentaire": "Validé automatiquement par l'API AWS. Chiffrement SSE-S3 actif sur tous les buckets.",
                "source": "api:aws"
            }
        }
        updates += 1
        details = "Mesures cryptographiques (A.10.1) validées via AWS KMS/S3."
    
    else:
        raise HTTPException(status_code=400, detail="Connecteur inconnu")

    # Sauvegarde
    parcours["iso27001"] = iso27001
    grc["parcours"] = parcours
    project["grc"] = grc
    
    update_project_db(project_id, project)

    return ConnectorScanResult(
        connector_id=req.connector_id,
        status="success",
        updates_count=updates,
        details=details
    )
