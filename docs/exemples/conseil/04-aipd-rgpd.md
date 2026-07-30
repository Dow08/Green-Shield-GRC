**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **AIPD / PIA (RGPD)** — Vernier Composites SAS
> Édité le 30/07/2026 22:05 · Réf. `audit_de_securite_et_analyse_de_risque_ebios_rm`
> **Document confidentiel — diffusion restreinte**

# ANALYSE D'IMPACT RELATIVE À LA PROTECTION DES DONNÉES (AIPD / PIA)

**Client :** Vernier Composites SAS  
**Projet :** Audit de sécurité & analyse de risque EBIOS RM  
**Date :** 30/07/2026 22:05  
**Délégué à la Protection des Données (DPO) :** Enregistré au registre  

---

## 1. Registre des Activités de Traitement (Inventaire)
| ID | Activité de Traitement | Finalité | Catégories de Données | Durée de conservation |
| :--- | :--- | :--- | :--- | :--- |
| RGPD-01 | Gestion administrative du personnel | Exécution du contrat de travail, paie, obligations sociales. | Identité, coordonnées, RIB, situation familiale, arrêts de travail | Durée du contrat + 5 ans (prescription prud'homale) |
| RGPD-02 | Vidéoprotection des accès ateliers | Sécurité des personnes et protection du secret industriel. | Images des salariés et visiteurs aux 6 points d'accès | 30 jours |
| RGPD-03 | Suivi de la santé au travail | Suivi des expositions aux résines époxy (obligation employeur). | Données de santé, résultats d'examens médicaux | 40 ans après la fin d'exposition (Code du travail) |


---

## 2. Analyse d'Impact Systématique (PIA)

### 2.1 Description Systématique du Traitement
Vidéoprotection continue des 6 accès aux ateliers et au laboratoire R&D, avec conservation 30 jours et consultation restreinte à deux personnes habilitées. Finalité double : sécurité des personnes (machines dangereuses) et protection du secret industriel.

### 2.2 Évaluation de la Nécessité et de la Proportionnalité
La protection du secret industriel justifie un contrôle des accès au laboratoire, mais la vidéoprotection continue des postes de travail en atelier excède ce qui est nécessaire : le champ des caméras 3 et 4 a été réduit aux seules zones de passage, et l'enregistrement audio désactivé.

### 2.3 Évaluation des Risques sur les Droits et Libertés des Personnes
Origine : accès illégitime d'un tiers au NVR, exposé sur le même VLAN que la bureautique. Risque : surveillance permanente de salariés identifiables (gravité Élevée, vraisemblance Moyenne au vu de l'absence de segmentation). Impact sur les personnes : sentiment de surveillance constante, détournement possible à des fins disciplinaires.

### 2.4 Mesures de Traitement & de Sécurité envisagées (Atténuation)
Segmentation du NVR sur un VLAN dédié, authentification nominative des deux habilités avec journalisation des consultations, réduction du champ des caméras 3 et 4, affichage et information des salariés, consultation du CSE actée en séance du 12/06/2026.

---

## 3. Obligations Organisationnelles (Conduite de l'AIPD)
| Obligation | Référence | État | Commentaire |
| :--- | :--- | :--- | :--- |
| Avis du délégué à la protection des données recueilli | RGPD Art. 35 §2 | Fait | DPO externe mutualisé — avis favorable rendu le 18/06/2026 sous réserve de la réduction du champ des caméras. |
| Avis des personnes concernées recueilli (ou motif de non-consultation) | RGPD Art. 35 §9 | Fait | CSE consulté le 12/06/2026, avis favorable ; note d'information remise aux 204 salariés. |
| Confrontation aux listes CNIL des traitements soumis / exemptés | RGPD Art. 35 §4-5 | Fait | Traitement figurant sur la liste CNIL des traitements soumis à AIPD (surveillance systématique de personnes sur un lieu de travail). |
| Réexamen prévu à chaque évolution du niveau de risque | RGPD Art. 35 §11 | Fait | Réexamen déclenché par tout ajout de caméra, toute extension de durée de conservation, ou au plus tard le 30/06/2028. |
| Consultation préalable de la CNIL avant mise en œuvre | RGPD Art. 36 §1 | Non applicable (risque résiduel non élevé) | |


---

### SIGNATURE DE VALIDATION CONFORMITÉ CNIL

| Avis du Délégué à la Protection des Données (DPO) | Validation du Responsable du Traitement |
| :--- | :--- |
| **Avis Favorable / Non Favorable** | **Validé pour mise en œuvre** |
| Signature : | Signature : |

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `143dfce57d167905bbe2b6cf363f1f64f3ee118732de9c36683e1622a5bb2e87`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
