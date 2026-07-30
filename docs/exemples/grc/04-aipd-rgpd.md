**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **AIPD / PIA (RGPD)** — Banque Aurore SA
> Édité le 30/07/2026 22:05 · Réf. `audit_de_conformite_iso_27001_et_dora`
> **Document confidentiel — diffusion restreinte**

# ANALYSE D'IMPACT RELATIVE À LA PROTECTION DES DONNÉES (AIPD / PIA)

**Client :** Banque Aurore SA  
**Projet :** Audit de conformité ISO 27001 & DORA  
**Date :** 30/07/2026 22:05  
**Délégué à la Protection des Données (DPO) :** Enregistré au registre  

---

## 1. Registre des Activités de Traitement (Inventaire)
| ID | Activité de Traitement | Finalité | Catégories de Données | Durée de conservation |
| :--- | :--- | :--- | :--- | :--- |
| RGPD-01 | Gestion des comptes et opérations | Exécution du contrat de services bancaires. | Identité, coordonnées, données financières, historiques d'opérations | Durée de la relation + 5 ans (Code monétaire et financier) |
| RGPD-02 | Lutte contre le blanchiment (LCB-FT) | Obligation légale de vigilance et de déclaration TRACFIN. | Identité, origine des fonds, alertes de profilage | 5 ans après la fin de la relation d'affaires |
| RGPD-03 | Scoring d'octroi de crédit | Évaluation de la solvabilité — décision partiellement automatisée. | Revenus, charges, historique d'incidents, score calculé | Durée du crédit + 5 ans |


---

## 2. Analyse d'Impact Systématique (PIA)

### 2.1 Description Systématique du Traitement
Scoring automatisé d'octroi de crédit appliqué à l'ensemble des demandes particuliers, combinant données déclaratives, historique interne et fichiers d'incidents Banque de France. Une décision de refus peut être prononcée sans intervention humaine en deçà d'un seuil de score, avec réexamen humain sur réclamation.

### 2.2 Évaluation de la Nécessité et de la Proportionnalité
L'évaluation de solvabilité est une obligation prudentielle. L'automatisation est proportionnée au volume (2 800 demandes/mois), mais le refus automatique sans intervention humaine relève de l'Art. 22 RGPD : un droit d'obtenir une intervention humaine a été mis en place, et les variables du modèle ont été réduites de 47 à 31 après revue de pertinence.

### 2.3 Évaluation des Risques sur les Droits et Libertés des Personnes
Risque principal : discrimination indirecte par des variables corrélées à l'origine géographique (code postal). Gravité Élevée (effet juridique et économique durable sur la personne), vraisemblance Moyenne. Risque secondaire : opacité de la décision, la personne ne pouvant contester ce qu'elle ne comprend pas.

### 2.4 Mesures de Traitement & de Sécurité envisagées (Atténuation)
Retrait de la variable code postal et des 4 variables les plus corrélées, test de disparité annuel sur cohortes, motivation systématique du refus en langage clair, droit à l'intervention humaine sous 15 jours, journalisation des décisions pendant 5 ans.

---

## 3. Obligations Organisationnelles (Conduite de l'AIPD)
| Obligation | Référence | État | Commentaire |
| :--- | :--- | :--- | :--- |
| Avis du délégué à la protection des données recueilli | RGPD Art. 35 §2 | Fait | DPO interne — avis réservé du 22/06/2026 : maintient une alerte sur le risque de discrimination indirecte résiduelle. |
| Avis des personnes concernées recueilli (ou motif de non-consultation) | RGPD Art. 35 §9 | Fait | Panel de 12 clients consulté en juin 2026 ; incompréhension majoritaire des motifs de refus, à l'origine de la mesure de motivation en langage clair. |
| Confrontation aux listes CNIL des traitements soumis / exemptés | RGPD Art. 35 §4-5 | Fait | Traitement figurant sur la liste CNIL (décision automatisée avec effet juridique) — AIPD obligatoire. |
| Réexamen prévu à chaque évolution du niveau de risque | RGPD Art. 35 §11 | Fait | Réexamen à chaque réentraînement du modèle et au minimum annuellement. |
| Consultation préalable de la CNIL avant mise en œuvre | RGPD Art. 36 §1 | Fait | Consultation préalable CNIL déposée le 08/07/2026 (accusé AR-2026-4471), réponse attendue sous 8 semaines. Mise en production suspendue dans l'intervalle. |


---

### SIGNATURE DE VALIDATION CONFORMITÉ CNIL

| Avis du Délégué à la Protection des Données (DPO) | Validation du Responsable du Traitement |
| :--- | :--- |
| **Avis Favorable / Non Favorable** | **Validé pour mise en œuvre** |
| Signature : | Signature : |

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `c6c4d45e568cff57cfe0161d28b9ae8c7b73842f56e0660190548ad3e4992b08`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
