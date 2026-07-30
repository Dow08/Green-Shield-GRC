**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **RAPPORT D'AUDIT DE SÉCURITÉ & D'ANALYSE DE RISQUE** — Vernier Composites SAS
> Édité le 30/07/2026 22:05 · Réf. `audit_de_securite_et_analyse_de_risque_ebios_rm`
> **Document confidentiel — diffusion restreinte**

# RAPPORT D'AUDIT DE SÉCURITÉ & D'ANALYSE DE RISQUE

|   |   |
| :--- | :--- |
| **Projet** | Audit de sécurité & analyse de risque EBIOS RM |
| **Client** | Vernier Composites SAS |
| **Périmètre de l'audit** | SI de production et de R&D du site de Saint-Étienne (2 ateliers, 1 laboratoire), hors filiale allemande et hors SI commercial hébergé chez l'éditeur. |
| **Date d'édition** | 30/07/2026 22:05 |
| **Auditeur** | Consultant, Cabinet non renseigné |


---

## 1. Synthèse à destination de la direction
Vernier Composites présente une exposition élevée sur deux actifs non substituables : la ligne de production (38 k€/jour ouvré) et les formulations R&D, non brevetées. Trois écarts expliquent l'essentiel du risque : le réseau industriel n'est pas séparé du réseau bureautique, les sauvegardes résident sur le même VLAN que la production et n'ont jamais été restaurées en test, et le prestataire de maintenance dispose d'un accès VPN permanent sans authentification forte. Aucun ne demande d'investissement lourd : les trois relèvent de configuration et de procédure. Le MFA et la sortie d'une copie de sauvegarde du VLAN de production sont réalisables sous quinze jours.

---

## 2. Cadrage de la mission
| Élément de cadrage | Contenu |
| :--- | :--- |
| Déclencheur de la mission | Exigence de sécurité du donneur d'ordre aéronautique inscrite au renouvellement de contrat 2027, doublée d'une tentative de rançongiciel évitée en mars 2026. |
| Sponsor exécutif | Directeur Général (mandat direct, arbitrage budgétaire sans passage COMEX) |
| Budget vendu | 18 jours |
| Maturité constatée à l'entrée | Faible à moyenne : sauvegardes existantes mais non testées, aucune PSSI, aucun référent sécurité, réseau OT non segmenté. |
| Échéance cible | 2026-11-30 (revue de sécurité du donneur d'ordre) |
| Périmètre inclus | SI bureautique et industriel du site de Saint-Étienne, incluant AD, MES, automates de cuisson, NAS R&D, messagerie M365 et sauvegardes. |
| Périmètre explicitement exclu | Filiale allemande (SI distinct), SI commercial en SaaS, tests d'intrusion sur les automates en production (risque matière), audit du code embarqué. |
| Modalités d'intervention | Mission en 4 phases sur 10 semaines, 3 déplacements sur site, points d'avancement hebdomadaires en visioconférence de 30 minutes. |
| Accès au SI consentis | Compte nominatif en lecture seule sur l'AD, accès physique aux ateliers accompagné, export des configurations pare-feu fourni par le client. Aucun accès administrateur. |
| Date de réunion de lancement | 2026-06-03 |
| Gouvernance de la mission | Comité de pilotage bimensuel présidé par le DG, arbitrages tracés en compte rendu, escalade directe au DG en cas de découverte critique en cours de mission. |
| Livrables contractuels | Rapport d'audit de sécurité avec constats sourcés · Analyse de risque EBIOS RM (ateliers 1 à 5) · Plan de traitement priorisé et chiffré · AIPD vidéoprotection · Restitution en comité de direction (2 h) |
| Participants au lancement | Directeur Général (sponsor) · Responsable Infrastructure · Responsable R&D · Responsable Production · Responsable RH (volet RGPD) |


### 2.1 Entretiens conduits
| Rôle rencontré | Date | Ce qui a été déclaré |
| :--- | :--- | :--- |
| Directeur Général | 2026-06-03 | Attente principale : conserver la qualification du donneur d'ordre. Budget disponible mais arbitré à l'euro près ; demande un plan chiffré et priorisé. |
| Responsable Infrastructure | 2026-06-05 | Confirme l'absence de segmentation OT/IT, l'absence d'EDR et le fait que les sauvegardes n'ont jamais été restaurées en test. Signale 12 comptes à privilèges dont 4 sans propriétaire identifié. |
| Responsable R&D | 2026-06-11 | Les formulations sont sur un partage SMB accessible à 31 comptes, dont 9 hors R&D. Aucune traçabilité des consultations. Aucun brevet ne protège ces actifs. |
| Responsable Production | 2026-06-11 | Un arrêt de plus de 24 h impose de purger les fours et de rebuter les pièces en cours : le RTO de 24 h est un plafond technique, pas une préférence. |
| Responsable RH | 2026-06-17 | Confirme la présence de données de santé au travail conservées 40 ans et le recours à un DPO externe mutualisé. CSE consulté sur la vidéoprotection. |


---

## 3. Patrimoine évalué
### 3.1 Valeurs métier
| ID | Valeur métier | Description | Données personnelles |
| :--- | :--- | :--- | :--- |
| VM-01 | Formulations et procédés composites (R&D) | Recettes matières, courbes de cuisson, résultats d'essais destructifs. Actif le plus sensible de l'entreprise, non brevetable en l'état. | Non |
| VM-02 | Dossiers de qualification client | Preuves de conformité aéronautique par lot, exigées lors des audits clients. | Non |
| VM-03 | Données RH et paie | Contrats, bulletins, données de santé au travail des 204 salariés. | Oui |
| VM-04 | Continuité de la ligne de production | Disponibilité des automates et du MES pilotant les 4 fours de cuisson. | Non |


### 3.2 Biens supports
| ID | Bien support | Type | Description | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| BS-01 | Active Directory (2 contrôleurs de domaine) | Logiciel | Annuaire unique, forêt à domaine unique, niveau fonctionnel 2016. | Responsable Infrastructure |
| BS-02 | Serveur de fichiers R&D (NAS) | Matériel | Stocke les formulations. Partage SMB, pas de chiffrement au repos. | Responsable R&D |
| BS-03 | MES et automates de cuisson | Matériel | Réseau OT à plat, non segmenté du réseau bureautique. | Responsable Production |
| BS-04 | Postes de travail (168 postes Windows 11) | Matériel | Parc géré par GPO, sans EDR à ce jour. | Support IT |
| BS-05 | Messagerie Microsoft 365 | Logiciel | Tenant unique, MFA activé pour les seuls administrateurs. | Responsable Infrastructure |
| BS-06 | Sauvegardes Veeam sur NAS secondaire | Matériel | Sauvegarde quotidienne, même VLAN que la production, pas de copie hors site. | Responsable Infrastructure |


---

## 4. Évaluation organisationnelle
_Aucune check-list de conformité n'est rattachée à cette mission : l'évaluation organisationnelle relève ici de l'analyse de risque du chapitre 2._

---

## 5. Analyse de risque
### 5.1 Événements redoutés
| ID | Événement redouté | Gravité | Impacts |
| :--- | :--- | :--- | :--- |
| ER-01 | Chiffrement du SI de production par rançongiciel | 4/4 | Arrêt des 4 fours de cuisson, 38 k€/jour ouvré, pénalités de retard contractuelles au-delà de 5 jours. |
| ER-02 | Exfiltration des formulations composites | 4/4 | Perte définitive de l'avantage concurrentiel : les formulations ne sont pas brevetées et leur valeur repose entièrement sur le secret. |
| ER-03 | Falsification d'un dossier de qualification client | 3/4 | Perte de la qualification aéronautique, exclusion de la chaîne d'approvisionnement du donneur d'ordre. |
| ER-04 | Divulgation des données de santé au travail | 3/4 | Atteinte grave à la vie privée de salariés identifiables, sanction CNIL, conflit social. |


### 5.2 Scénarios opérationnels
| ID | Scénario opérationnel | Gravité | Vraisemblance | Mesure d'atténuation |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | Hameçonnage d'un poste bureautique (BS-04, sans EDR) → récupération d'identifiants → élévation de privilèges sur l'AD (BS-01) → propagation vers le MES (BS-03) faute de segmentation OT/IT → chiffrement, y compris des sauvegardes (BS-06) placées sur le même VLAN. | 4/4 | 3/5 | Déploiement EDR, MFA généralisé, segmentation OT/IT, sauvegarde immuable hors site. |
| SO-02 | Compromission du compte VPN du prestataire de maintenance des fours → rebond vers le NAS R&D (BS-02) dont le partage SMB est accessible sans cloisonnement → copie des formulations. | 4/4 | 2/5 | VPN nominatif par prestataire, MFA obligatoire, restriction d'accès au NAS R&D par groupe AD, journalisation des accès. |
| SO-03 | Salarié R&D copiant les formulations sur un support amovible avant son départ, aucun contrôle des périphériques USB n'étant en place. | 3/4 | 3/5 | Blocage USB par GPO sauf dérogation, journalisation des copies volumineuses, clause de confidentialité renforcée. |
| SO-04 | Accès illégitime au NVR de vidéoprotection depuis le VLAN bureautique, faute de segmentation. | 3/4 | 2/5 | VLAN dédié au NVR, authentification nominative, journalisation des consultations. |


### 5.2bis Traitement des risques (propriétaire, résiduel, décision)
| ID | Propriétaire | Résiduel (G/V) | Stratégie | Statut |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | RSSI | 3/2 | Réduire | En traitement |
| SO-02 | DSI | 3/1 | Réduire | Ouvert |
| SO-03 | Direction R&D | 4/2 | Réduire | Ouvert |
| SO-04 | Responsable Sûreté | 1/1 | Accepter | Traité |


---

## 6. Écosystème et risques tiers
| Tiers | Criticité | Ratio | Dép. / Pén. / Mat. / Conf. |
| :--- | :--- | :--- | :--- |
| Prestataire maintenance automates (accès VPN permanent) | Critique | 4.17 | 5 / 5 / 2 / 3 |
| Infogéreur poste de travail | Moyen | 1.33 | 4 / 4 / 3 / 4 |
| Hébergeur Microsoft 365 | Faible | 0.8 | 5 / 4 / 5 / 5 |
| Fournisseur de résines (portail EDI) | Faible | 0.67 | 3 / 2 / 3 / 3 |
| Cabinet d'expertise comptable | Faible | 0.17 | 2 / 1 / 3 / 4 |


---

## 7. Résilience et continuité
| Cible de continuité | Valeur retenue |
| :--- | :--- |
| RTO — durée maximale d'interruption admissible | 24 heures pour la ligne de production, 72 heures pour la bureautique |
| RPO — perte de données maximale admissible | 4 heures pour le MES, 24 heures pour les serveurs de fichiers |
| Politique de sauvegarde | Objectif cible : règle 3-2-1 avec une copie immuable hors site et un test de restauration semestriel documenté. État constaté : sauvegarde quotidienne unique sur NAS secondaire du même VLAN, jamais restaurée en test. |


### 7.1 Séquence de remédiation E3R
| Étape E3R | Procédure retenue |
| :--- | :--- |
| Endiguement | Isolement immédiat du VLAN production par coupure des liens inter-VLAN sur le cœur de réseau, arrêt contrôlé des fours selon la procédure de sécurité matière, déconnexion du VPN prestataires. |
| Éviction | Réinitialisation du compte krbtgt à deux reprises, révocation de tous les accès prestataires, réinitialisation des mots de passe des 12 comptes à privilèges, blocage des règles de transfert de messagerie créées durant l'incident. |
| Éradication | Analyse hors ligne des deux contrôleurs de domaine, reconstruction plutôt que nettoyage en cas de doute, recherche des tâches planifiées et services persistants sur l'ensemble du parc, suppression des comptes dormants. |
| Reconstruction | Remontée de l'AD depuis une sauvegarde antérieure à la compromission, reconstruction des postes depuis un master durci, remise en service par vagues avec surveillance renforcée pendant 30 jours, retour d'expérience formalisé sous 15 jours. |


### 7.2 Volet stratégique — arbitrage Direction
_Le volet stratégique (arbitrage Direction) n'a pas été documenté._

---

## 8. Évaluation technique des configurations

> **Couverture technique de cet audit.** Aucun scan technique n'a été exécuté : à ce stade, l'ensemble des constats repose sur du déclaratif.

_Aucun scan technique d'audit de configuration n'a été exécuté pour ce projet._

---

## 9. Rattachement aux référentiels de contrôles (CIS v8 / NIST CSF 2.0)
| Pratique | Contrôles rattachés | État | Constaté en |
| :--- | :--- | :--- | :--- |
| Inventaire des biens supports tenu sur tout le cycle de vie | NIST CSF 2.0 ID.AM, CIS v8 CIS 1, CIS v8 CIS 2 | Couverte — 6 bien(s) support inventorié(s) en phase 1. | Phase 1 (Cadrage & Patrimoine) |
| Gestion continue des vulnérabilités | CIS v8 CIS 7, NIST CSF 2.0 ID.RA-01 | **Non couverte** — Non déclaré en phase 2. | Phase 2 (Diagnostic & RGPD) |
| Journalisation collectée, conservée et exploitable | CIS v8 CIS 8 | **Non couverte** — Non déclarée en phase 5. | Phase 5 (Résilience & E3R) |
| Fournisseurs évalués avant acquisition | NIST CSF 2.0 ID.RA-10 | **Non couverte** — Non tracé : exigence propre au volet GRC. | Phase 3 (Risques Tiers (TPRM)) |

1 pratique(s) couverte(s) sur 4 (25 %).


---

## 10. Plan de traitement
### 10.1 Mesures priorisées
| ID | Priorité | Axe | Mesure de traitement |
| :--- | :--- | :--- | :--- |
| REM-01 | Critique | Protection | Segmenter le réseau OT du réseau bureautique (pare-feu industriel, flux autorisés en liste blanche) — traite SO-01 et SO-02. |
| REM-02 | Critique | Résilience | Mettre en place une sauvegarde immuable hors site et tester la restauration complète du MES — traite ER-01. |
| REM-03 | Critique | Protection | Généraliser le MFA à tous les comptes M365 et VPN, y compris prestataires — traite SO-01 et SO-02. |
| REM-04 | Élevé | Défense | Déployer un EDR sur les 168 postes et les serveurs, avec supervision — traite SO-01. |
| REM-05 | Élevé | Protection | Restreindre l'accès au NAS R&D par groupe AD et bloquer les périphériques USB par GPO — traite SO-03. |
| REM-06 | Élevé | Gouvernance | Faire adopter la PSSI par la direction et nommer un référent sécurité à temps partiel — aucune gouvernance formalisée à ce jour. |
| REM-07 | Moyen | Défense | Centraliser les journaux (AD, pare-feu, M365, NVR) avec une rétention de 12 mois — traite SO-04 et conditionne toute investigation. |
| REM-08 | Moyen | Gouvernance | Mettre en place une revue trimestrielle des accès et un processus de départ salarié — traite SO-03. |


### 10.1bis Pilotage (responsable, échéance, statut)
| ID | Responsable | Échéance | Statut | Coût estimé |
| :--- | :--- | :--- | :--- | :--- |
| REM-01 | DSI | 2026-09-30 | En cours | Moyen |
| REM-02 | DSI | 2026-09-15 | Fait | Léger |
| REM-03 | DSI | 2026-09-01 | En cours | Léger |
| REM-04 | DSI | 2026-11-30 | À faire | Élevé |
| REM-05 | DSI | 2026-09-30 | À faire | Négligeable |
| REM-06 | Direction Générale | 2026-10-15 | À faire | Négligeable |
| REM-07 | RSSI | 2026-12-15 | À faire | Moyen |
| REM-08 | RSSI | 2026-10-01 | À faire | Négligeable |


### 10.2 Actions immédiates
1. Activer le MFA sur la messagerie et le VPN
2. Changer les mots de passe d'administration par défaut des automates
3. Sortir une copie de sauvegarde du VLAN de production
4. Sensibiliser les 204 salariés à l'hameçonnage
5. Appliquer les correctifs critiques en attente sur les 2 contrôleurs de domaine
6. Retirer les droits d'administrateur local aux utilisateurs standards

---

## 11. Charges consommées
| Phase | Temps consommé |
| :--- | ---: |
| Cadrage & Patrimoine | 13 h |
| Diagnostic & RGPD | 16 h |
| Risques Tiers (TPRM) | 7 h |
| Analyse des Menaces (EBIOS RM) | 19 h |
| Résilience & E3R | 10 h |
| Traitement & Livrables | 12 h |
| Coordination, déplacements, rédaction | 8 h |
| **Total** | **85 h** |

*   **Budget vendu :** 18 jours

---

## 12. Réserves et limites
Les constats figurant dans le présent rapport reposent exclusivement sur les éléments communiqués par Vernier Composites SAS et sur les preuves collectées à la date du 30/07/2026 22:05, dans le périmètre défini au chapitre 2. Les déclarations recueillies auprès des interlocuteurs n'ont fait l'objet d'une vérification technique que lorsque la colonne « Preuve » le mentionne explicitement. Le présent rapport constitue une évaluation à un instant donné et ne saurait valoir garantie d'absence de vulnérabilité ni de conformité future, le niveau de sécurité évoluant avec le système d'information et l'état de la menace.

---

## 13. Certifications et signatures d'audit
L'auditeur certifie l'exactitude des constats factuels mentionnés ci-dessus.

| Signature de l'Auditeur Cyber | Signature du Client Audité |
| :--- | :--- |
| **Consultant** | **DSI / Responsable de la sécurité** |
| Signature cryptographique locale : `SHA256:143dfce57d167905bbe2b6cf363f1f64f3ee118732de9c36683e1622a5bb2e87` | Signature : |

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `143dfce57d167905bbe2b6cf363f1f64f3ee118732de9c36683e1622a5bb2e87`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
