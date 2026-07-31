import re

def next_id(prefix: str, existing_items: list[dict], id_field: str = "id") -> str:
    """Génère un identifiant séquentiel sans collision.
    
    Args:
        prefix: Le préfixe (ex: 'BS', 'T'). L'ID généré sera 'BS-01', 'T-001', etc.
        existing_items: La liste des dictionnaires existants.
        id_field: La clé contenant l'ID dans le dictionnaire.
    """
    existants = {e.get(id_field, "") for e in existing_items}
    
    # Trouver la longueur du padding selon le préfixe
    # Par historique, BS-XX a 2 chiffres, T-XXX a 3 chiffres
    padding = 3 if prefix == "T" else 2
    
    numeros = []
    pattern = re.compile(rf"^{prefix}-(\d+)$")
    for e in existants:
        m = pattern.fullmatch(e)
        if m:
            numeros.append(int(m.group(1)))
            
    suivant = (max(numeros) + 1) if numeros else 1
    
    candidat = f"{prefix}-{suivant:0{padding}d}"
    while candidat in existants:
        suivant += 1
        candidat = f"{prefix}-{suivant:0{padding}d}"
        
    return candidat
