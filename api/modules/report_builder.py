"""report_builder.py — génération des livrables Markdown d'une mission.

Extrait de `projects.py` le 29/07/2026 : la route HTTP mélangeait le routage,
la lecture du dossier de mission et près de 300 lignes de gabarits documentaires.
Ce module ne connaît ni HTTP ni système de fichiers — il prend l'état d'une
mission et rend un couple (titre de fichier, contenu Markdown), ce qui le rend
testable directement et prépare l'habillage graphique des livrables.
"""
from __future__ import annotations

from datetime import datetime

from . import charte
from . import docx_export


class TypeDocumentInconnu(ValueError):
    """Type de livrable non pris en charge."""

    def __init__(self, doc_type: str):
        super().__init__(f"Type de document inconnu : {doc_type}")
        self.doc_type = doc_type


# Types de livrables proposés par l'interface.
TYPES_DOCUMENTS = ("nda", "ebios", "pssi_pri", "aipd", "audit_report")


def build_document(state: dict, p_id: str, doc_type: str) -> tuple[str, str]:
    """Rend (nom de fichier, contenu Markdown) pour un livrable de mission."""
    client = state.get("client", "Client")
    name = state.get("name", "Projet")
    steps = state.get("steps", {})
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    title = ""
    markdown_content = ""
    
    empreinte = docx_export.data_fingerprint(state)


    if doc_type == "nda":
        title = f"Accord_Confidentialite_{p_id}.md"
        nda_text = steps.get("cadrage", {}).get("nda_text") or "NDA non rédigé."
        markdown_content = f"""{charte.entete("ACCORD DE CONFIDENTIALITÉ", client, now, p_id)}
# ACCORD DE CONFIDENTIALITÉ & PROTECTION DES DONNÉES (NDA)

**Projet :** {name}  
**Client :** {client}  
**Date d'édition :** {now}  
**Classification :** <span style="color:#ff6f91;font-weight:bold;">CONFIDENTIEL AFFAIRES</span>  

---

{nda_text}

---

### SIGNATURES

En foi de quoi, les parties s'engagent et signent électroniquement ou de manière manuscrite :

| Pour DP Cyber Consulting | Pour {client} |
| :--- | :--- |
| **Dorian, Consultant Cyber** | **Mandataire habilité** |
| Signature cryptographique locale : `SHA256:{docx_export.data_fingerprint(state)}` | Signature : |
| Date : {now} | Date : |
"""
    elif doc_type == "ebios":
        title = f"Analyse_Risques_EBIOS_{p_id}.md"
        redoutes = steps.get("ebios", {}).get("redoute_events", [])
        scenarios = steps.get("ebios", {}).get("operational_scenarios", [])
        assets_metier = steps.get("cadrage", {}).get("assets_metier", [])
        assets_support = steps.get("cadrage", {}).get("assets_support", [])
        
        metier_md = "| ID | Valeur Métier | Description | Données Perso (RGPD) |\n| :--- | :--- | :--- | :--- |\n"
        for m in assets_metier:
            rgpd_status = "OUI (Registre actif)" if m.get("is_personal_data") else "Non"
            metier_md += f"| {m.get('id')} | {m.get('name')} | {m.get('description')} | {rgpd_status} |\n"
            
        support_md = "| ID | Bien Support | Type | Description | Responsable |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for s in assets_support:
            support_md += f"| {s.get('id')} | {s.get('name')} | {s.get('type')} | {s.get('description')} | {s.get('owner')} |\n"
            
        redoutes_md = "| ID | Événement Redouté | Gravité | Impacts (Financier, Juridique, Image) |\n| :--- | :--- | :--- | :--- |\n"
        for r in redoutes:
            redoutes_md += f"| {r.get('id')} | {r.get('event')} | {r.get('gravity')}/4 | {r.get('impact')} |\n"
            
        scenarios_md = "| ID | Scénario Opérationnel (Connaître -> Intrusion -> Pivot -> Exploiter) | Gravité | Vraisemblance | Mesure d'Atténuation |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for s in scenarios:
            scenarios_md += f"| {s.get('id')} | {s.get('event')} | {s.get('gravity')}/4 | {s.get('likelihood')}/5 | {s.get('mitigation')} |\n"
            
        markdown_content = f"""{charte.entete("ANALYSE DE RISQUES EBIOS RM", client, now, p_id)}
# RAPPORT D'ANALYSE DE RISQUES CYBER (ORIENTATION EBIOS RM)

**Projet :** {name}  
**Client :** {client}  
**Date d'édition :** {now}  
**Consultant :** Dorian, DP Cyber Consulting  
**Classification :** CONFIDENTIEL  

---

## 1. Cadrage et Identification du Patrimoine (Périmètre)
Ce chapitre identifie le périmètre d'évaluation, les missions fondamentales de l'entreprise et cartographie le patrimoine d'actifs.

### 1.1 Valeurs Métier (Patrimoine à forte valeur ajoutée)
{metier_md}

### 1.2 Biens Supports (Actifs de l'infrastructure)
{support_md}

---

## 2. Cartographie des Menaces & Scénarios EBIOS RM

### 2.1 Événements Redoutés
{redoutes_md}

### 2.2 Scénarios Opérationnels d'Attaque (Analyse Factuelle)
{scenarios_md}

---

## 3. Plan d'Action & Traitement
Chaque risque identifié ci-dessus doit être mitigé par l'application des contrôles techniques correspondants.
"""
    elif doc_type == "pssi_pri":
        title = f"PSSI_PRI_{p_id}.md"
        pssi_sects = steps.get("pssi_pri", {}).get("pssi_sections", [])
        sections_md = ""
        for s in pssi_sects:
            sections_md += f"### {s.get('title')}\n\n{s.get('content')}\n\n"
            
        rto = steps.get("resilience", {}).get("bcp_strategy", {}).get("rto", "N/A")
        rpo = steps.get("resilience", {}).get("bcp_strategy", {}).get("rpo", "N/A")
        bcp = steps.get("resilience", {}).get("bcp_strategy", {}).get("backup_policy", "N/A")
        e3r = steps.get("resilience", {}).get("e3r", {})
        
        markdown_content = f"""{charte.entete("PSSI & PLAN DE REPRISE", client, now, p_id)}
# POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI) & PLAN DE REPRISE (PRI)

**Client :** {client}  
**Projet :** {name}  
**Date :** {now}  
**Auteur :** Dorian, DP Cyber Consulting  

---

## I. POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI)

{sections_md}

---

## II. PLAN DE REPRISE INFORMATIQUE & RÉSILIENCE (PRI)

### 2.1 Indicateurs Temporels de Continuité
*   **RTO (Recovery Time Objective / Temps de reprise max) :** `{rto}`
*   **RPO (Recovery Point Objective / Perte de données max) :** `{rpo}`

### 2.2 Politique de Sauvegarde et d'Immuabilité
{bcp}

### 2.3 Séquence de Remédiation en Gestion de Crise (E3R de l'ANSSI)
En cas de compromission majeure de l'Active Directory ou de l'infrastructure Cloud :

1.  **Endiguement (Contenir l'attaquant) :**  
    {e3r.get('endiguement', 'N/A')}
2.  **Éviction (Reprendre le contrôle du cœur de confiance) :**  
    {e3r.get('eviction', 'N/A')}
3.  **Éradication (Nettoyage en profondeur des emprises) :**  
    {e3r.get('eradication', 'N/A')}
4.  **Reconstruction (Rebâtir de façon durcie dès la conception) :**  
    {e3r.get('reconstruction', 'N/A')}

---

### SIGNATURES POUR HOMOLOGATION DE SÉCURITÉ

| Pour DP Cyber Consulting | Pour la Direction de {client} |
| :--- | :--- |
| **Dorian** | **Directeur Général / RSSI** |
| Signature : | Signature : |
"""
    elif doc_type == "aipd":
        title = f"AIPD_RGPD_{p_id}.md"
        diagnostic = steps.get("diagnostic", {})
        rgpd_reg = diagnostic.get("rgpd_register", [])
        aipd = diagnostic.get("aipd", {})
        
        register_md = "| ID | Activité de Traitement | Finalité | Catégories de Données | Durée de conservation |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for r in rgpd_reg:
            register_md += f"| {r.get('id')} | {r.get('name')} | {r.get('purpose')} | {r.get('data_categories')} | {r.get('retention')} |\n"
            
        markdown_content = f"""{charte.entete("AIPD / PIA (RGPD)", client, now, p_id)}
# ANALYSE D'IMPACT RELATIVE À LA PROTECTION DES DONNÉES (AIPD / PIA)

**Client :** {client}  
**Projet :** {name}  
**Date :** {now}  
**Délégué à la Protection des Données (DPO) :** Enregistré au registre  

---

## 1. Registre des Activités de Traitement (Inventaire)
{register_md}

---

## 2. Analyse d'Impact Systématique (PIA)

### 2.1 Description Systématique du Traitement
{aipd.get('treatment_description', 'N/A')}

### 2.2 Évaluation de la Nécessité et de la Proportionnalité
{aipd.get('necessity_eval', 'N/A')}

### 2.3 Évaluation des Risques sur les Droits et Libertés des Personnes
{aipd.get('risks_eval', 'N/A')}

### 2.4 Mesures de Traitement & de Sécurité envisagées (Atténuation)
{aipd.get('mitigation_measures', 'N/A')}

---

### SIGNATURE DE VALIDATION CONFORMITÉ CNIL

| Avis du Délégué à la Protection des Données (DPO) | Validation du Responsable du Traitement |
| :--- | :--- |
| **Avis Favorable / Non Favorable** | **Validé pour mise en œuvre** |
| Signature : | Signature : |
"""
    elif doc_type == "audit_report":
        title = f"Rapport_Audit_GRC_{p_id}.md"
        cadrage = steps.get("cadrage", {})
        fw_name = cadrage.get("framework_name", "Standard GRC")
        scope = cadrage.get("scope", "N/A")
        
        controls = steps.get("evaluation", {}).get("manual_controls", [])
        manual_md = "| ID | Exigence Organisationnelle | Statut de Conformité | Notes du Consultant |\n| :--- | :--- | :--- | :--- |\n"
        for c in controls:
            manual_md += f"| {c.get('id')} | {c.get('title')} | {c.get('status')} | {c.get('notes', 'N/A')} |\n"
            
        tech_results = steps.get("evaluation", {}).get("technical_results", {})
        tech_md = ""
        if tech_results:
            tech_md = f"### Résultats Scan Technique (AuditCraft-GRC)\n\n*   **Score technique :** {tech_results.get('score')}% ({tech_results.get('band')})\n*   **Failles critiques :** {tech_results.get('critical_count')}\n\n{tech_results.get('report_markdown', '_Pas de rapport généré_')}"
        else:
            tech_md = "_Aucun scan technique d'audit de configuration n'a été exécuté pour ce projet._"
            
        markdown_content = f"""{charte.entete("RAPPORT D'AUDIT GRC", client, now, p_id)}
# RAPPORT D'AUDIT DE CONFORMITÉ & GRC

**Projet :** {name}  
**Client :** {client}  
**Référentiel principal :** {fw_name}  
**Périmètre de l'audit :** {scope}  
**Date d'édition :** {now}  
**Auditeur :** Dorian, DP Cyber Consulting  

---

## 1. Synthèse de l'Évaluation Organisationnelle (Manuelle)
{manual_md}

---

## 2. Évaluation Technique des Configurations (Automatique)
{tech_md}

---

## 3. Certifications et signatures d'audit
L'auditeur certifie l'exactitude des constats factuels mentionnés ci-dessus.

| Signature de l'Auditeur Cyber | Signature du Client Audité |
| :--- | :--- |
| **Dorian** | **DSI / Responsable de la sécurité** |
| Signature cryptographique locale : `SHA256:{docx_export.data_fingerprint(state)}` | Signature : |
"""
    else:
        raise TypeDocumentInconnu(doc_type)
        

    markdown_content += charte.pied(empreinte)
    return title, markdown_content
