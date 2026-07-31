**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **RAPPORT D'AUDIT DE CONFORMITÉ & GRC** — Banque Aurore SA
> Édité le 31/07/2026 11:10 · Réf. `audit_de_conformite_iso_27001_et_dora`
> **Document confidentiel — diffusion restreinte**

# RAPPORT D'AUDIT DE CONFORMITÉ & GRC

|   |   |
| :--- | :--- |
| **Projet** | Audit de conformité ISO 27001 & DORA |
| **Client** | Banque Aurore SA |
| **Référentiel principal** | ISO/IEC 27001:2022 |
| **Périmètre de l'audit** | Système d'information de la banque de détail et des services de paiement, incluant les fonctions critiques ou importantes au sens DORA. Hors périmètre : salle de marché (entité juridique distincte) et réseau d'agences physiques. |
| **Date d'édition** | 31/07/2026 11:10 |
| **Auditeur** | Consultant, Cabinet non renseigné |


---

## 1. Synthèse à destination de la direction
La banque présente une maturité de sécurité supérieure à la moyenne de son segment : gouvernance établie, journalisation centralisée, résilience testée. Deux écarts majeurs subsistent et exposent directement à un constat ACPR : la gestion des départs (14 comptes actifs de sortants) et l'inventaire des actifs (37 serveurs inconnus). Le registre DORA des prestataires est incomplet sur 3 des 4 prestataires critiques. Aucun de ces écarts n'est structurel : ils relèvent de processus à formaliser, pas d'investissements lourds.

---

## 2. Cadrage de la mission
| Élément de cadrage | Contenu |
| :--- | :--- |
| Déclencheur de la mission | Entrée en application de DORA et notification d'entité essentielle NIS2, doublées d'une revue ACPR annoncée pour le premier trimestre 2027. |
| Sponsor exécutif | Directeur des Risques (rattachement direct au Directoire) |
| Budget vendu | 34 jours |
| Maturité constatée à l'entrée | Élevée sur la gouvernance et la résilience, hétérogène sur la gestion des accès et des actifs. |
| Échéance cible | 2027-01-31 (revue ACPR) |
| Périmètre inclus | Banque de détail, services de paiement, fonctions critiques DORA, conformité ISO 27001 sur les 4 domaines audités. |
| Périmètre explicitement exclu | Salle de marché, agences physiques, test d'intrusion applicatif (couvert par un marché distinct). |
| Modalités d'intervention | Mission en 6 phases sur 14 semaines, 8 jours sur site, comité de suivi mensuel avec le Directeur des Risques. |
| Accès au SI consentis | Comptes nominatifs en lecture seule sur le SIEM et l'annuaire, extraction des configurations fournie par la DSI, accès aux contrats prestataires via le service juridique. |
| Date de réunion de lancement | 2026-05-11 |
| Gouvernance de la mission | Comité de suivi mensuel présidé par le Directeur des Risques, remontée immédiate au Directoire de tout écart susceptible d'entraîner un constat ACPR. |
| Livrables contractuels | Rapport d'audit ISO 27001 avec écarts et preuves · Cartographie DORA des prestataires critiques · Plan de remédiation priorisé et daté · AIPD du scoring de crédit · Restitution au comité des risques |
| Participants au lancement | Directeur des Risques (sponsor) · RSSI · DSI · DPO · Directeur des Paiements · Responsable Conformité |


### 2.1 Entretiens conduits
| Rôle rencontré | Date | Ce qui a été déclaré |
| :--- | :--- | :--- |
| Directeur des Risques | 2026-05-11 | Objectif : aucun constat majeur à la revue ACPR de 2027. Priorité donnée à ce qui est opposable devant le régulateur. |
| RSSI | 2026-05-18 | Signale lui-même la faiblesse du processus de départ et l'écart d'inventaire. SIEM opérationnel mais aveugle sur les journaux applicatifs du core banking. |
| Directeur des Paiements | 2026-05-26 | RTO de 2 h imposé par les règles STET, pas par un arbitrage interne. Bascule testée trimestriellement avec procès-verbal. |
| DPO | 2026-06-02 | Avis réservé sur le scoring de crédit ; consultation CNIL déposée, mise en production suspendue jusqu'à réponse. |
| Responsable Conformité | 2026-06-09 | Registre d'information DORA renseigné pour 1 prestataire critique sur 4. Stratégies de sortie non documentées. |


---

## 3. Patrimoine évalué
### 3.1 Valeurs métier
| ID | Valeur métier | Description | Données personnelles |
| :--- | :--- | :--- | :--- |
| VM-01 | Comptes et soldes clients | Registre des positions clients, cœur du système bancaire. | Oui |
| VM-02 | Service de paiement instantané (SCT Inst) | Fonction critique au sens DORA — indisponibilité immédiatement visible du client. | Oui |
| VM-03 | Dossiers de crédit et scoring | Décisions automatisées avec effet juridique (RGPD Art. 22). | Oui |
| VM-04 | Piste d'audit réglementaire | Traçabilité exigée par l'ACPR, intégrité opposable. | Oui |


### 3.2 Biens supports
| ID | Bien support | Type | Description | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| BS-01 | Core banking system (éditeur externe) | Logiciel | Progiciel hébergé chez l'éditeur, version N-1. | DSI |
| BS-02 | Plateforme de paiement SCT Inst | Logiciel | Interconnexion STET, disponibilité 24/7 exigée. | Directeur des Paiements |
| BS-03 | Datacenter principal et site de repli | Matériel | Deux sites actifs/passifs distants de 40 km. | Responsable Production |
| BS-04 | SIEM et collecte de journaux | Logiciel | Collecte 380 sources, rétention 12 mois. | RSSI |
| BS-05 | Poste de travail et messagerie (M365) | Logiciel | 640 postes, MFA généralisé, EDR déployé. | DSI |


---

## 4. Protection des données personnelles
### 4.1 Registre des traitements (RGPD Art. 30)
| ID | Traitement | Finalité | Catégories de données | Conservation |
| :--- | :--- | :--- | :--- | :--- |
| RGPD-01 | Gestion des comptes et opérations | Exécution du contrat de services bancaires. | Identité, coordonnées, données financières, historiques d'opérations | Durée de la relation + 5 ans (Code monétaire et financier) |
| RGPD-02 | Lutte contre le blanchiment (LCB-FT) | Obligation légale de vigilance et de déclaration TRACFIN. | Identité, origine des fonds, alertes de profilage | 5 ans après la fin de la relation d'affaires |
| RGPD-03 | Scoring d'octroi de crédit | Évaluation de la solvabilité — décision partiellement automatisée. | Revenus, charges, historique d'incidents, score calculé | Durée du crédit + 5 ans |

### 4.1bis Registre des violations de données (RGPD Art. 33-34)
_Aucune violation de données n'a été constatée sur cette mission._


### 4.2 Analyse d'impact — les quatre volets
| Volet d'analyse | Contenu |
| :--- | :--- |
| Description systématique du traitement | Scoring automatisé d'octroi de crédit appliqué à l'ensemble des demandes particuliers, combinant données déclaratives, historique interne et fichiers d'incidents Banque de France. Une décision de refus peut être prononcée sans intervention humaine en deçà d'un seuil de score, avec réexamen humain sur réclamation. |
| Nécessité et proportionnalité | L'évaluation de solvabilité est une obligation prudentielle. L'automatisation est proportionnée au volume (2 800 demandes/mois), mais le refus automatique sans intervention humaine relève de l'Art. 22 RGPD : un droit d'obtenir une intervention humaine a été mis en place, et les variables du modèle ont été réduites de 47 à 31 après revue de pertinence. |
| Risques pour les droits et libertés | Risque principal : discrimination indirecte par des variables corrélées à l'origine géographique (code postal). Gravité Élevée (effet juridique et économique durable sur la personne), vraisemblance Moyenne. Risque secondaire : opacité de la décision, la personne ne pouvant contester ce qu'elle ne comprend pas. |
| Mesures d'atténuation | Retrait de la variable code postal et des 4 variables les plus corrélées, test de disparité annuel sur cohortes, motivation systématique du refus en langage clair, droit à l'intervention humaine sous 15 jours, journalisation des décisions pendant 5 ans. |


### 4.3 Obligations organisationnelles
| Obligation | Référence | État | Commentaire |
| :--- | :--- | :--- | :--- |
| Avis du délégué à la protection des données recueilli | RGPD Art. 35 §2 | Fait | DPO interne — avis réservé du 22/06/2026 : maintient une alerte sur le risque de discrimination indirecte résiduelle. |
| Avis des personnes concernées recueilli (ou motif de non-consultation) | RGPD Art. 35 §9 | Fait | Panel de 12 clients consulté en juin 2026 ; incompréhension majoritaire des motifs de refus, à l'origine de la mesure de motivation en langage clair. |
| Confrontation aux listes CNIL des traitements soumis / exemptés | RGPD Art. 35 §4-5 | Fait | Traitement figurant sur la liste CNIL (décision automatisée avec effet juridique) — AIPD obligatoire. |
| Réexamen prévu à chaque évolution du niveau de risque | RGPD Art. 35 §11 | Fait | Réexamen à chaque réentraînement du modèle et au minimum annuellement. |
| Consultation préalable de la CNIL avant mise en œuvre | RGPD Art. 36 §1 | Fait | Consultation préalable CNIL déposée le 08/07/2026 (accusé AR-2026-4471), réponse attendue sous 8 semaines. Mise en production suspendue dans l'intervalle. |


---

## 5. Analyse de risque
### 5.1 Événements redoutés
| ID | Événement redouté | Gravité | Impacts |
| :--- | :--- | :--- | :--- |
| ER-01 | Indisponibilité prolongée du paiement instantané | 4/4 | Fonction critique DORA interrompue, notification ACPR sous 4 h, atteinte de réputation immédiate. |
| ER-02 | Altération de l'intégrité des soldes clients | 4/4 | Perte de confiance systémique, reconstitution manuelle, risque prudentiel. |
| ER-03 | Fuite du fichier clients (210 000 personnes) | 4/4 | Notification CNIL sous 72 h et information individuelle, sanction possible, action de groupe. |


### 5.2 Scénarios opérationnels
| ID | Scénario opérationnel | Gravité | Vraisemblance | Mesure d'atténuation |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | Mise à jour piégée du core banking (BS-01) livrée par l'éditeur → exécution en production → accès aux comptes clients (VM-01) et altération des soldes. | 4/4 | 2/5 | Vérification d'intégrité des livraisons éditeur, environnement de pré-production isolé, revue de code des correctifs critiques. |
| SO-02 | Saturation volumétrique de la plateforme SCT Inst (BS-02) via l'interconnexion STET → indisponibilité de la fonction critique DORA. | 4/4 | 3/5 | Limitation de débit en amont, bascule sur le site de repli testée trimestriellement, procédure de dégradation maîtrisée. |


### 5.2bis Traitement des risques (propriétaire, résiduel, décision)
| ID | Propriétaire | Résiduel (G/V) | Stratégie | Statut |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | RSSI | 3/1 | Réduire | En traitement |
| SO-02 | Directeur des Paiements | 3/2 | Réduire | Ouvert |


---

## 6. Écosystème et risques tiers
| Prestataire | Exigences satisfaites | Écarts restants |
| :--- | :--- | :--- |
| Éditeur core banking (prestataire critique) | 2/4 (50 %) | Clauses contractuelles obligatoires signées (DORA Art. 30) ; Stratégie de sortie documentée et testable |
| Opérateur d'interconnexion STET | 4/4 (100 %) | Conforme |
| Hébergeur du site de repli | 0/4 (0 %) | Inscrit au registre d'information (DORA Art. 28.3) ; Clauses contractuelles obligatoires signées (DORA Art. 30) ; Stratégie de sortie documentée et testable ; Évaluation réalisée avant acquisition (NIST ID.RA-10) |
| Prestataire d'infogérance poste de travail | 0/4 (0 %) | Inscrit au registre d'information (DORA Art. 28.3) ; Clauses contractuelles obligatoires signées (DORA Art. 30) ; Stratégie de sortie documentée et testable ; Évaluation réalisée avant acquisition (NIST ID.RA-10) |


---

## 7. Résilience et continuité
| Cible de continuité | Valeur retenue |
| :--- | :--- |
| RTO — durée maximale d'interruption admissible | 2 heures pour le paiement instantané (fonction critique DORA), 8 heures pour la banque en ligne |
| RPO — perte de données maximale admissible | 15 minutes pour les opérations de paiement, 1 heure pour les référentiels clients |
| Politique de sauvegarde | Réplication synchrone entre les deux datacenters, sauvegarde immuable quotidienne conservée 35 jours hors site, test de bascule complet trimestriel avec procès-verbal transmis à l'ACPR. |


### 7.1 Séquence de remédiation E3R
| Étape E3R | Procédure retenue |
| :--- | :--- |
| Endiguement | Isolement de la zone compromise par bascule sur le site de repli, gel des livraisons éditeur, activation de la cellule de crise avec astreinte RSSI sous 30 minutes. |
| Éviction | Révocation des certificats et jetons d'interconnexion, réinitialisation des comptes à privilèges et des comptes de service, rupture temporaire du lien avec l'éditeur. |
| Éradication | Analyse forensique des binaires livrés, comparaison aux empreintes de référence, reconstruction des serveurs concernés depuis un socle durci vérifié. |
| Reconstruction | Remise en service progressive avec vérification d'intégrité comptable poste par poste, réconciliation des opérations sur la période suspecte, notification ACPR de clôture d'incident et retour d'expérience sous 30 jours. |


### 7.2 Volet stratégique — arbitrage Direction
_Le volet stratégique (arbitrage Direction) n'a pas été documenté._

---

## 8. Évaluation organisationnelle
| ID | Référentiel | Exigence Organisationnelle | Statut de Conformité | Notes du Consultant |
| :--- | :--- | :--- | :--- | :--- |
| ISO-A.5 | ISO/IEC 27001:2022 | Politiques de sécurité de l'information | Conforme | PSSI validée par le comité exécutif le 14/02/2026, revue annuelle planifiée. |
| ISO-A.6 | ISO/IEC 27001:2022 | Organisation et rôles de sécurité | Conforme | RSSI rattaché au Directeur des Risques, séparation effective d'avec la DSI. |
| ISO-A.7 | ISO/IEC 27001:2022 | Sécurité des ressources humaines | Non conforme | Aucune procédure formalisée de retrait des accès au départ : 14 comptes actifs de personnes sorties des effectifs, dont 3 à privilèges. Écart majeur. |
| ISO-A.8 | ISO/IEC 27001:2022 | Gestion des actifs | Non conforme | Inventaire des actifs tenu mais non rapproché du parc réel depuis 19 mois ; 37 serveurs découverts au scan ne figurent pas à l'inventaire. |
| DORA-ICT | Reglement DORA | Cadre de gestion des risques TIC | Conforme | Cadre formalisé, revu annuellement par le comité des risques TIC. |
| DORA-INC | Reglement DORA | Notification des incidents majeurs | Non conforme | Processus de classification existant, mais délai de notification à l'ACPR non testé en conditions réelles. |
| DORA-TEST | Reglement DORA | Tests de resilience operationnelle | À vérifier | Dernier test de pénétration remonte à 14 mois — cadence annuelle à confirmer pour 2027. |
| DORA-3P | Reglement DORA | Gestion du risque tiers | Conforme | Registre des prestataires critiques tenu à jour (cf. Phase 3, Risques Tiers). |


### Déclaration d'Applicabilité (SoA) — synthèse par thème
_Détail des 93 contrôles de l'Annexe A dans le livrable dédié « Déclaration d'Applicabilité »._

| Thème | Total | Applicables | Exclus | Non statués |
| :--- | :--- | :--- | :--- | :--- |
| Organisationnel | 37 | 3 | 0 | 34 |
| Personnel | 8 | 0 | 0 | 8 |
| Physique | 14 | 0 | 1 | 13 |
| Technologique | 34 | 1 | 0 | 33 |

---

## 9. Évaluation technique des configurations

> **Couverture technique de cet audit.** Aucun scan technique n'a été exécuté : à ce stade, l'ensemble des constats repose sur du déclaratif.

_Aucun scan technique d'audit de configuration n'a été exécuté pour ce projet._

---

## 10. Rattachement aux référentiels de contrôles (CIS v8 / NIST CSF 2.0)
| Pratique | Contrôles rattachés | État | Constaté en |
| :--- | :--- | :--- | :--- |
| Inventaire des biens supports tenu sur tout le cycle de vie | NIST CSF 2.0 ID.AM, CIS v8 CIS 1, CIS v8 CIS 2 | Couverte — 5 bien(s) support inventorié(s) en phase 1. | Phase 1 (Cadrage & Patrimoine) |
| Gestion continue des vulnérabilités | CIS v8 CIS 7, NIST CSF 2.0 ID.RA-01 | Couverte — Déclaré actif en phase 2. | Phase 2 (Diagnostic & RGPD) |
| Journalisation collectée, conservée et exploitable | CIS v8 CIS 8 | Couverte — Déclarée active en phase 5. | Phase 5 (Résilience & E3R) |
| Fournisseurs évalués avant acquisition | NIST CSF 2.0 ID.RA-10 | **Non couverte** — 2 tiers évalué(s) avant acquisition sur 4. | Phase 3 (Risques Tiers (TPRM)) |

3 pratique(s) couverte(s) sur 4 (75 %).


---

## 11. Plan de traitement
### 11.1 Mesures priorisées
| ID | Priorité | Axe | Mesure de traitement |
| :--- | :--- | :--- | :--- |
| REM-01 | Critique | Gouvernance | Formaliser la procédure de retrait des accès au départ et clôturer les 14 comptes actifs de sortants — écart ISO A.7. |
| REM-02 | Critique | Gouvernance | Compléter le registre d'information DORA (Art. 28.3) pour les 3 prestataires critiques manquants avant l'échéance ACPR. |
| REM-03 | Élevé | Protection | Rapprocher l'inventaire des actifs du parc réel et intégrer les 37 serveurs découverts — écart ISO A.8. |
| REM-04 | Élevé | Gouvernance | Documenter et tester une stratégie de sortie pour le prestataire core banking — exigence DORA. |
| REM-05 | Moyen | Défense | Étendre la collecte SIEM aux journaux applicatifs du core banking, aujourd'hui absents des 380 sources. |


### 11.1bis Pilotage (responsable, échéance, statut)
| ID | Responsable | Échéance | Statut | Coût estimé |
| :--- | :--- | :--- | :--- | :--- |
| REM-01 | DSI | 2026-09-15 | En cours | Négligeable |
| REM-02 | RSSI | 2026-09-30 | À faire | Négligeable |
| REM-03 | DSI | 2026-11-15 | À faire | Moyen |
| REM-04 | RSSI | 2026-12-01 | À faire | Négligeable |
| REM-05 | RSSI | 2026-10-15 | À faire | Moyen |


### 11.2 Actions immédiates
1. Clôturer les 3 comptes à privilèges de personnes sorties
2. Publier la liste des prestataires critiques au registre DORA
3. Activer l'alerte SIEM sur création de compte à privilèges
4. Vérifier la couverture EDR des 37 serveurs découverts
5. Planifier le prochain test de bascule avec procès-verbal
6. Confirmer la clause de sortie du contrat core banking

---

## 12. Charges consommées
| Phase | Temps consommé |
| :--- | ---: |
| Cadrage & Patrimoine | 20 h |
| Diagnostic & RGPD | 24 h |
| Risques Tiers (TPRM) | 16 h |
| Analyse des Menaces (EBIOS RM) | 12 h |
| Résilience & E3R | 15 h |
| Traitement & Livrables | 14 h |
| Coordination, déplacements, rédaction | 10 h |
| **Total** | **111 h** |

*   **Budget vendu :** 34 jours

---

## 13. Réserves et limites
Les constats figurant dans le présent rapport reposent exclusivement sur les éléments communiqués par Banque Aurore SA et sur les preuves collectées à la date du 31/07/2026 11:10, dans le périmètre défini au chapitre 2. Les déclarations recueillies auprès des interlocuteurs n'ont fait l'objet d'une vérification technique que lorsque la colonne « Preuve » le mentionne explicitement. Le présent rapport constitue une évaluation à un instant donné et ne saurait valoir garantie d'absence de vulnérabilité ni de conformité future, le niveau de sécurité évoluant avec le système d'information et l'état de la menace.

---

## 14. Certifications et signatures d'audit
L'auditeur certifie l'exactitude des constats factuels mentionnés ci-dessus.

| Signature de l'Auditeur Cyber | Signature du Client Audité |
| :--- | :--- |
| **Consultant** | **DSI / Responsable de la sécurité** |
| Signature cryptographique locale : `SHA256:87bdb9f2e3587ab6a25c45da3d56f8f35ba86205e49b6718241a85d4c4bee970` | Signature : |

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `87bdb9f2e3587ab6a25c45da3d56f8f35ba86205e49b6718241a85d4c4bee970`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
