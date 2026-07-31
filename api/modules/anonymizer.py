import re
import uuid
from typing import Tuple, Dict, Any

class DataAnonymizer:
    def __init__(self):
        # Pour stocker les correspondances pendant une session/requête
        self.mapping: Dict[str, str] = {}
        self.counters: Dict[str, int] = {
            "IP": 1,
            "EMAIL": 1,
            "DOMAIN": 1,
            "ORG": 1
        }
        
    def _replace_and_store(self, match: re.Match, entity_type: str) -> str:
        original = match.group(0)
        # Si déjà mappé
        for placeholder, orig in self.mapping.items():
            if orig == original:
                return placeholder
                
        # Nouveau mapping
        placeholder = f"[{entity_type}_{self.counters[entity_type]}]"
        self.counters[entity_type] += 1
        self.mapping[placeholder] = original
        return placeholder

    def anonymize(self, text: str) -> str:
        """
        Anonymise le texte en remplaçant les entités sensibles par des placeholders.
        """
        result = text
        
        # 1. IPs
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        result = re.sub(ip_pattern, lambda m: self._replace_and_store(m, "IP"), result)
        
        # 2. Emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        result = re.sub(email_pattern, lambda m: self._replace_and_store(m, "EMAIL"), result)
        
        # 3. Domaines
        domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b'
        result = re.sub(domain_pattern, lambda m: self._replace_and_store(m, "DOMAIN"), result)
        
        # 4. Noms d'organisations (très basique pour l'exemple sans modèle NLP lourd)
        # On cherche des suites de mots commençant par une majuscule (sauf début de phrase)
        # Pour faire simple on se contentera des regex au-dessus, et d'un dict personnalisé
        # dans une vraie implémentation Presidio serait utilisé.
        
        return result
        
    def deanonymize(self, text: str) -> str:
        """
        Rétablit les données originales à partir des placeholders.
        """
        result = text
        for placeholder, original in self.mapping.items():
            result = result.replace(placeholder, original)
        return result

# Instance singleton pour tester, ou à instancier par requête
