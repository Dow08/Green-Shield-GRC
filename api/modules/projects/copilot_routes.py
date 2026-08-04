from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from modules.anonymizer import DataAnonymizer
from modules.auth import get_current_user
from modules.database.models import User
import logging

router = APIRouter(prefix="/api/projects/copilot", tags=["copilot"])
logger = logging.getLogger(__name__)

class CopilotRequest(BaseModel):
    prompt: str

class CopilotResponse(BaseModel):
    name: str
    client: str
    type: str
    framework_ids: Optional[List[str]] = None
    original_prompt: str
    masked_prompt: str

@router.post("/generate", response_model=CopilotResponse)
def generate_project(request: CopilotRequest, current_user: User = Depends(get_current_user)):
    """Pré-remplit le formulaire de création à partir d'une description libre.

    **Ce n'est pas un appel à une IA.** Le type de mission est déduit par
    quelques mots-clés (voir plus bas) et le reste est une valeur par défaut
    que le consultant corrige. L'interface décrit désormais ce comportement
    tel qu'il est — elle annonçait auparavant une génération par IA et un
    masquage « avant envoi » alors que rien n'est envoyé nulle part.

    Le jour où un vrai LLM sera branché ici (via `ai_gateway.call_gemini`,
    point de passage unique du projet), `anonymizer.py` devra d'abord couvrir
    les **noms d'organisation** : il ne masque aujourd'hui que les adresses IP,
    les courriels et les domaines. Le nom du client — la donnée la plus
    sensible d'un audit — sortirait en clair.
    """
    # 1. Instanciation de l'anonymiseur pour cette session
    anonymizer = DataAnonymizer()

    # 2. Masquage des données sensibles
    masked_prompt = anonymizer.anonymize(request.prompt)
    # Le prompt décrit une mission cliente : sa longueur suffit au diagnostic,
    # son contenu n'est jamais journalisé (même règle que le Copilote de
    # mission, `crud.py::run_project_copilot`). Il l'était auparavant, alors
    # que le masquage ne couvre pas les noms d'organisation.
    logger.info("Copilote création — prompt reçu (%d caractères)", len(request.prompt))

    # 3. Aucune IA n'est appelée ici : valeur par défaut, à corriger par le
    # consultant dans le formulaire de création.
    client_par_defaut = "Client à renseigner"

    # 4. Les placeholders éventuels sont rétablis avant affichage.
    final_client_name = anonymizer.deanonymize(client_par_defaut)

    # 5. Déduction du volet par mots-clés — pas une inférence d'IA.
    project_type = "grc" if "audit" in request.prompt.lower() or "iso" in request.prompt.lower() else "consulting"
    frameworks = ["iso27001"] if project_type == "grc" else None

    return CopilotResponse(
        name="Mission à nommer",
        client=final_client_name,
        type=project_type,
        framework_ids=frameworks,
        original_prompt=request.prompt,
        masked_prompt=masked_prompt
    )
