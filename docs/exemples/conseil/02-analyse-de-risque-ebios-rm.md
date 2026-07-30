**GREEN SHIELD** · Cabinet non renseigné — Audit & Conseil Cybersécurité

> **ANALYSE DE RISQUES EBIOS RM** — Vernier Composites SAS
> Édité le 30/07/2026 21:45 · Réf. `audit_de_securite_et_analyse_de_risque_ebios_rm`
> **Document confidentiel — diffusion restreinte**

# RAPPORT D'ANALYSE DE RISQUES CYBER (ORIENTATION EBIOS RM)

**Projet :** Audit de sécurité & analyse de risque EBIOS RM  
**Client :** Vernier Composites SAS  
**Date d'édition :** 30/07/2026 21:45  
**Consultant :** Consultant, Cabinet non renseigné  
**Classification :** CONFIDENTIEL  

---

## 1. Cadrage et Identification du Patrimoine (Périmètre)
Ce chapitre identifie le périmètre d'évaluation, les missions fondamentales de l'entreprise et cartographie le patrimoine d'actifs.

### 1.1 Valeurs Métier (Patrimoine à forte valeur ajoutée)
| ID | Valeur Métier | Description | Données Perso (RGPD) |
| :--- | :--- | :--- | :--- |
| VM-01 | Formulations et procédés composites (R&D) | Recettes matières, courbes de cuisson, résultats d'essais destructifs. Actif le plus sensible de l'entreprise, non brevetable en l'état. | Non |
| VM-02 | Dossiers de qualification client | Preuves de conformité aéronautique par lot, exigées lors des audits clients. | Non |
| VM-03 | Données RH et paie | Contrats, bulletins, données de santé au travail des 204 salariés. | OUI (Registre actif) |
| VM-04 | Continuité de la ligne de production | Disponibilité des automates et du MES pilotant les 4 fours de cuisson. | Non |


### 1.2 Biens Supports (Actifs de l'infrastructure)
| ID | Bien Support | Type | Description | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| BS-01 | Active Directory (2 contrôleurs de domaine) | Logiciel | Annuaire unique, forêt à domaine unique, niveau fonctionnel 2016. | Responsable Infrastructure |
| BS-02 | Serveur de fichiers R&D (NAS) | Matériel | Stocke les formulations. Partage SMB, pas de chiffrement au repos. | Responsable R&D |
| BS-03 | MES et automates de cuisson | Matériel | Réseau OT à plat, non segmenté du réseau bureautique. | Responsable Production |
| BS-04 | Postes de travail (168 postes Windows 11) | Matériel | Parc géré par GPO, sans EDR à ce jour. | Support IT |
| BS-05 | Messagerie Microsoft 365 | Logiciel | Tenant unique, MFA activé pour les seuls administrateurs. | Responsable Infrastructure |
| BS-06 | Sauvegardes Veeam sur NAS secondaire | Matériel | Sauvegarde quotidienne, même VLAN que la production, pas de copie hors site. | Responsable Infrastructure |


---

## 2. Cartographie des Menaces & Scénarios EBIOS RM

### 2.1 Événements Redoutés
| ID | Événement Redouté | Gravité | Impacts (Financier, Juridique, Image) |
| :--- | :--- | :--- | :--- |
| ER-01 | Chiffrement du SI de production par rançongiciel | 4/4 | Arrêt des 4 fours de cuisson, 38 k€/jour ouvré, pénalités de retard contractuelles au-delà de 5 jours. |
| ER-02 | Exfiltration des formulations composites | 4/4 | Perte définitive de l'avantage concurrentiel : les formulations ne sont pas brevetées et leur valeur repose entièrement sur le secret. |
| ER-03 | Falsification d'un dossier de qualification client | 3/4 | Perte de la qualification aéronautique, exclusion de la chaîne d'approvisionnement du donneur d'ordre. |
| ER-04 | Divulgation des données de santé au travail | 3/4 | Atteinte grave à la vie privée de salariés identifiables, sanction CNIL, conflit social. |


### 2.2 Sources de Risque et Objectifs Visés
| ID | Source de risque | Objectif visé |
| :--- | :--- | :--- |
| SR-01 | Groupe cybercriminel opérant en rançongiciel-as-a-service | Extorsion par double peine : chiffrement puis menace de publication. |
| SR-02 | Concurrent étranger via prestataire de maintenance | Captation des formulations pour combler un retard technologique. |
| SR-03 | Salarié en partance vers un concurrent | Emport de dossiers R&D à des fins d'embauche. |


### 2.3 Scénarios Opérationnels d'Attaque (Analyse Factuelle)
| ID | Scénario Opérationnel (Connaître -> Intrusion -> Pivot -> Exploiter) | Gravité | Vraisemblance | Mesure d'Atténuation |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | Hameçonnage d'un poste bureautique (BS-04, sans EDR) → récupération d'identifiants → élévation de privilèges sur l'AD (BS-01) → propagation vers le MES (BS-03) faute de segmentation OT/IT → chiffrement, y compris des sauvegardes (BS-06) placées sur le même VLAN. | 4/4 | 3/5 | Déploiement EDR, MFA généralisé, segmentation OT/IT, sauvegarde immuable hors site. |
| SO-02 | Compromission du compte VPN du prestataire de maintenance des fours → rebond vers le NAS R&D (BS-02) dont le partage SMB est accessible sans cloisonnement → copie des formulations. | 4/4 | 2/5 | VPN nominatif par prestataire, MFA obligatoire, restriction d'accès au NAS R&D par groupe AD, journalisation des accès. |
| SO-03 | Salarié R&D copiant les formulations sur un support amovible avant son départ, aucun contrôle des périphériques USB n'étant en place. | 3/4 | 3/5 | Blocage USB par GPO sauf dérogation, journalisation des copies volumineuses, clause de confidentialité renforcée. |
| SO-04 | Accès illégitime au NVR de vidéoprotection depuis le VLAN bureautique, faute de segmentation. | 3/4 | 2/5 | VLAN dédié au NVR, authentification nominative, journalisation des consultations. |


### 2.3bis Traitement des risques (propriétaire, résiduel, décision)
| ID | Propriétaire | Résiduel (G/V) | Stratégie | Statut |
| :--- | :--- | :--- | :--- | :--- |
| SO-01 | RSSI | 3/2 | Réduire | En traitement |
| SO-02 | DSI | 3/1 | Réduire | Ouvert |
| SO-03 | Direction R&D | 4/2 | Réduire | Ouvert |
| SO-04 | Responsable Sûreté | 1/1 | Accepter | Traité |


### 2.4 Cas Réels Versés au Dossier
| Cas réel | Enseignement retenu pour ce client |
| :--- | :--- |
| Norsk Hydro (2019) — rançongiciel LockerGoga | Industriel comparable : la propagation IT vers OT a arrêté la production faute de segmentation. La transparence publique a limité l'atteinte réputationnelle. |
| ASML / employé exfiltrant des données (2023) | La menace interne sur la propriété intellectuelle industrielle est réelle et ne se traite pas par des mesures périmétriques. |
| Fuite de données de santé — laboratoires français (2021) | Les données de santé mal cloisonnées finissent en accès ouvert ; la sanction porte sur le défaut de mesures, pas sur l'attaque. |


---

## 3. Écosystème et Risques Tiers
| Tiers | Criticité | Ratio | Dép. / Pén. / Mat. / Conf. |
| :--- | :--- | :--- | :--- |
| Prestataire maintenance automates (accès VPN permanent) | Critique | 4.17 | 5 / 5 / 2 / 3 |
| Infogéreur poste de travail | Moyen | 1.33 | 4 / 4 / 3 / 4 |
| Hébergeur Microsoft 365 | Faible | 0.8 | 5 / 4 / 5 / 5 |
| Fournisseur de résines (portail EDI) | Faible | 0.67 | 3 / 2 / 3 / 3 |
| Cabinet d'expertise comptable | Faible | 0.17 | 2 / 1 / 3 / 4 |


---

## 4. Plan d'Action & Traitement
Chaque mesure ci-dessous répond à un scénario ou à un écart constaté au chapitre 2.

### 4.1 Mesures de Traitement Priorisées
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


### 4.1bis Pilotage (responsable, échéance, statut)
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


### 4.2 Actions Immédiates
1. Activer le MFA sur la messagerie et le VPN
2. Changer les mots de passe d'administration par défaut des automates
3. Sortir une copie de sauvegarde du VLAN de production
4. Sensibiliser les 204 salariés à l'hameçonnage
5. Appliquer les correctifs critiques en attente sur les 2 contrôleurs de domaine
6. Retirer les droits d'administrateur local aux utilisateurs standards

---

GREEN SHIELD — Cabinet non renseigné · Document confidentiel, ne pas diffuser sans autorisation écrite.

Empreinte SHA-256 de l'état de la mission à l'édition : `b74a86b53875b57c1a939c4a3399b4add2a26263c49b95e3f621b4069c7ebd63`

*Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.*
