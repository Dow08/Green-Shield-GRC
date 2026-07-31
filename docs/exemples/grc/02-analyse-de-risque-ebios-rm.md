**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **ANALYSE DE RISQUES EBIOS RM** — Banque Aurore SA
> Édité le 31/07/2026 10:38 · Réf. `audit_de_conformite_iso_27001_et_dora`
> **Document confidentiel — diffusion restreinte**

# RAPPORT D'ANALYSE DE RISQUES CYBER (ORIENTATION EBIOS RM)

**Projet :** Audit de conformité ISO 27001 & DORA  
**Client :** Banque Aurore SA  
**Date d'édition :** 31/07/2026 10:38  
**Consultant :** Consultant, Cabinet non renseigné  
**Classification :** CONFIDENTIEL  

---

## 1. Cadrage et Identification du Patrimoine (Périmètre)
Ce chapitre identifie le périmètre d'évaluation, les missions fondamentales de l'entreprise et cartographie le patrimoine d'actifs.

### 1.1 Valeurs Métier (Patrimoine à forte valeur ajoutée)
| ID | Valeur Métier | Description | Données Perso (RGPD) |
| :--- | :--- | :--- | :--- |
| VM-01 | Comptes et soldes clients | Registre des positions clients, cœur du système bancaire. | OUI (Registre actif) |
| VM-02 | Service de paiement instantané (SCT Inst) | Fonction critique au sens DORA — indisponibilité immédiatement visible du client. | OUI (Registre actif) |
| VM-03 | Dossiers de crédit et scoring | Décisions automatisées avec effet juridique (RGPD Art. 22). | OUI (Registre actif) |
| VM-04 | Piste d'audit réglementaire | Traçabilité exigée par l'ACPR, intégrité opposable. | OUI (Registre actif) |


### 1.2 Biens Supports (Actifs de l'infrastructure)
| ID | Bien Support | Type | Description | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| BS-01 | Core banking system (éditeur externe) | Logiciel | Progiciel hébergé chez l'éditeur, version N-1. | DSI |
| BS-02 | Plateforme de paiement SCT Inst | Logiciel | Interconnexion STET, disponibilité 24/7 exigée. | Directeur des Paiements |
| BS-03 | Datacenter principal et site de repli | Matériel | Deux sites actifs/passifs distants de 40 km. | Responsable Production |
| BS-04 | SIEM et collecte de journaux | Logiciel | Collecte 380 sources, rétention 12 mois. | RSSI |
| BS-05 | Poste de travail et messagerie (M365) | Logiciel | 640 postes, MFA généralisé, EDR déployé. | DSI |


---

## 2. Cartographie des Menaces & Scénarios EBIOS RM

### 2.1 Événements Redoutés
| ID | Événement Redouté | Gravité | Impacts (Financier, Juridique, Image) |
| :--- | :--- | :--- | :--- |
| ER-01 | Indisponibilité prolongée du paiement instantané | 4/4 | Fonction critique DORA interrompue, notification ACPR sous 4 h, atteinte de réputation immédiate. |
| ER-02 | Altération de l'intégrité des soldes clients | 4/4 | Perte de confiance systémique, reconstitution manuelle, risque prudentiel. |
| ER-03 | Fuite du fichier clients (210 000 personnes) | 4/4 | Notification CNIL sous 72 h et information individuelle, sanction possible, action de groupe. |


### 2.2 Sources de Risque et Objectifs Visés
| ID | Source de risque | Objectif visé |
| :--- | :--- | :--- |
| SR-01 | Groupe criminel spécialisé secteur financier | Fraude au virement et extorsion. |
| SR-02 | Compromission de la chaîne d'approvisionnement (éditeur core banking) | Accès indirect au SI bancaire via une mise à jour piégée. |


### 2.3 Scénarios Opérationnels d'Attaque (Analyse Factuelle)
| ID | Scénario Opérationnel (Connaître -> Intrusion -> Pivot -> Exploiter) | Gravité | Vraisemblance | Mesure d'Atténuation |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | Mise à jour piégée du core banking (BS-01) livrée par l'éditeur → exécution en production → accès aux comptes clients (VM-01) et altération des soldes. | 4/4 | 2/5 | Vérification d'intégrité des livraisons éditeur, environnement de pré-production isolé, revue de code des correctifs critiques. |
| SO-02 | Saturation volumétrique de la plateforme SCT Inst (BS-02) via l'interconnexion STET → indisponibilité de la fonction critique DORA. | 4/4 | 3/5 | Limitation de débit en amont, bascule sur le site de repli testée trimestriellement, procédure de dégradation maîtrisée. |


### 2.3bis Traitement des risques (propriétaire, résiduel, décision)
| ID | Propriétaire | Résiduel (G/V) | Stratégie | Statut |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | RSSI | 3/1 | Réduire | En traitement |
| SO-02 | Directeur des Paiements | 3/2 | Réduire | Ouvert |


### 2.4 Cas Réels Versés au Dossier
| Cas réel | Enseignement retenu pour ce client |
| :--- | :--- |
| Incident SolarWinds (2020) | La chaîne d'approvisionnement logicielle est un vecteur d'entrée légitime et signé — d'où l'exigence DORA de registre des prestataires. |
| Panne TSB (2018) — migration bancaire | Une bascule mal testée coûte plus cher qu'une attaque : le test de bascule est une exigence, pas une bonne pratique. |


---

## 3. Écosystème et Risques Tiers
| Prestataire | Exigences satisfaites | Écarts restants |
| :--- | :--- | :--- |
| Éditeur core banking (prestataire critique) | 2/4 (50 %) | Clauses contractuelles obligatoires signées (DORA Art. 30) ; Stratégie de sortie documentée et testable |
| Opérateur d'interconnexion STET | 4/4 (100 %) | Conforme |
| Hébergeur du site de repli | 0/4 (0 %) | Inscrit au registre d'information (DORA Art. 28.3) ; Clauses contractuelles obligatoires signées (DORA Art. 30) ; Stratégie de sortie documentée et testable ; Évaluation réalisée avant acquisition (NIST ID.RA-10) |
| Prestataire d'infogérance poste de travail | 0/4 (0 %) | Inscrit au registre d'information (DORA Art. 28.3) ; Clauses contractuelles obligatoires signées (DORA Art. 30) ; Stratégie de sortie documentée et testable ; Évaluation réalisée avant acquisition (NIST ID.RA-10) |


---

## 4. Plan d'Action & Traitement
Chaque mesure ci-dessous répond à un scénario ou à un écart constaté au chapitre 2.

### 4.1 Mesures de Traitement Priorisées
| ID | Priorité | Axe | Mesure de traitement |
| :--- | :--- | :--- | :--- |
| REM-01 | Critique | Gouvernance | Formaliser la procédure de retrait des accès au départ et clôturer les 14 comptes actifs de sortants — écart ISO A.7. |
| REM-02 | Critique | Gouvernance | Compléter le registre d'information DORA (Art. 28.3) pour les 3 prestataires critiques manquants avant l'échéance ACPR. |
| REM-03 | Élevé | Protection | Rapprocher l'inventaire des actifs du parc réel et intégrer les 37 serveurs découverts — écart ISO A.8. |
| REM-04 | Élevé | Gouvernance | Documenter et tester une stratégie de sortie pour le prestataire core banking — exigence DORA. |
| REM-05 | Moyen | Défense | Étendre la collecte SIEM aux journaux applicatifs du core banking, aujourd'hui absents des 380 sources. |


### 4.1bis Pilotage (responsable, échéance, statut)
| ID | Responsable | Échéance | Statut | Coût estimé |
| :--- | :--- | :--- | :--- | :--- |
| REM-01 | DSI | 2026-09-15 | En cours | Négligeable |
| REM-02 | RSSI | 2026-09-30 | À faire | Négligeable |
| REM-03 | DSI | 2026-11-15 | À faire | Moyen |
| REM-04 | RSSI | 2026-12-01 | À faire | Négligeable |
| REM-05 | RSSI | 2026-10-15 | À faire | Moyen |


### 4.2 Actions Immédiates
1. Clôturer les 3 comptes à privilèges de personnes sorties
2. Publier la liste des prestataires critiques au registre DORA
3. Activer l'alerte SIEM sur création de compte à privilèges
4. Vérifier la couverture EDR des 37 serveurs découverts
5. Planifier le prochain test de bascule avec procès-verbal
6. Confirmer la clause de sortie du contrat core banking

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `870d095ccce86180b4371c414e51921b436ce7160191eb6b8b033d69f8406603`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
