# RÉFÉRENTIEL CYBER & TECHNIQUE — GREEN SHIELD

Ce document sert de **spécification technique, de journal de bord d'implémentation et de guide de transfert (Handoff)**. Il est conçu pour donner à tout développeur ou modèle de langage (LLM) futur une vision claire et structurée de ce qui a été demandé, de ce qui a été réalisé en conséquence, et de la façon dont l'application est structurée pour de futurs développements.

---

## 📌 1. VISION & OBJECTIFS DU PROJET

**GREEN SHIELD** est une plateforme locale, modulaire et souveraine (100 % hors-ligne) d'audit de sécurité et d'accompagnement GRC (Gouvernance, Risques et Conformité). Elle est conçue spécifiquement pour assister un consultant en cybersécurité senior (Dorian, chez DP Cyber Consulting) dans ses missions quotidiennes de A à Z.

---

## 🎯 2. EXIGENCES DU CONSULTANT & RÉPONSES APPORTÉES

Voici la correspondance exacte entre vos demandes fonctionnelles et les implémentations techniques réalisées :

| Thématique / Demande | Expression du besoin | Implémentation technique réalisée |
| :--- | :--- | :--- |
| **Audit Technique Réel (Bouclier)** | Expliquer clairement ce qu'est l'audit technique (AuditCraft-GRC) et s'éloigner du fictif. | Intégration du scan statique réel des fichiers `sshd_config` et `nginx.conf` du client (dans `/targets`), affichage des lignes fautives exactes et des règles de durcissement violées avec score d'évaluation factuel. |
| **Manuel Autoguidé (6 Phases)** | Étre guidé pas-à-pas dans la réalisation d'un audit complet sans rien oublier. | Mise en place d'un Stepper Kanban dynamique à 6 phases synchronisé, sauvegardant l'avancement en continu. |
| **Données &amp; Modèles Pré-remplis** | Ne pas partir de zéro, avoir des champs pré-remplis éditables pour chaque client. | Le backend injecte un jeu complet de données par défaut réalistes de cybersécurité (EBIOS RM, PSSI, PRI, TPRM, NDA) dès la création d'un projet, que ce soit en GRC ou en Conseil. |
| **Sélecteur de Modèles (Suggestions)** | Choisir parmi un catalogue d'actifs standards éditables sans tout retaper de zéro. | Implémentation de **menus déroulants extensibles (Dropdowns)** sous l'inventaire de la Phase 1 (Sélecteurs de modèles d'actifs). Sélectionner une option (ex: Active Directory, BDD Clients, VPN) remplit instantanément et de façon cohérente tous les champs du formulaire. L'auditeur peut alors les modifier, puis cliquer sur `+` pour ajouter l'actif de manière explicite. |
| **Progression Réaliste (Progression à la validation)** | Ne pas avoir un projet déjà complété à 85% par défaut à cause des templates. | Calcul de la jauge de progression basé uniquement sur la **validation explicite** de chacune des 6 étapes via une case à cocher en bas de page (`validated: boolean`). Le projet commence à 0 % et progresse par paliers de 16,6 %. |
| **Diagnostic Assisté (Aide PSSI)** | Expliquer à quoi correspond chaque case à cocher (ex: "PSSI active") de manière pédagogique. | Implémentation d'un module d'aide interactif (panneaux d'explications SecOps &amp; ANSSI) s'ouvrant d'un clic sur la check-list pour guider le consultant. |
| **Indicateurs Numériques** | Voir la valeur exacte des réglettes (curseurs) sur l'interface. | Affichage textuel réactif en temps réel des valeurs numériques de sliders (ex : `Dépendance : 3/5`, `Gravité : 4/4`). |
| **Tableau de Bord &amp; Diagrammes** | Visualiser l'avancement global et la répartition des missions sous forme de graphiques. | Intégration de diagrammes SVG interactifs sur le Dashboard d'accueil (Progress Rings d'avancement moyen, barres empilées de répartition GRC/Conseil). |
| **Gestion des Projets (CRUD)** | Pouvoir supprimer un projet ou rapport d'audit directement depuis l'interface. | Implémentation de la route `DELETE /api/projects/{p_id}` côté API et d'un bouton de suppression (corbeille rouge) avec invite de confirmation sur le Dashboard. |
| **Menu Réglages / Paramètres** | Configurer l'identité du consultant et la clé d'API AI. | Ajout d'un menu **Paramètres** fonctionnel en bas à gauche de la barre latérale permettant de configurer son identité d'auditeur et sa clé d'API Copilote stockée localement de manière souveraine (`localStorage`). |
| **Exportation multi-formats** | Extraire les rapports d'audit en Markdown, Word (DocX) et PDF. | Intégration d'un moteur d'export compilant des documents Markdown/HTML pré-configurés avec des feuilles de style CSS d'impression professionnelles (NDA, EBIOS RM, PSSI/PRI, AIPD, Rapport GRC). Ouvrables nativement sous MS Word et imprimables directement en PDF depuis le navigateur. |
| **Solidité &amp; Stabilité** | Éviter les écrans noirs de crash au clic sur les onglets. | Résolution complète d'un bug d'optional-chaining sur les fiches de REX EBIOS RM. Sécurisation complète de tous les objets via des gardes TypeScript. |

---

## 🧱 3. ARCHITECTURE LOGICIELLE ET FLUX DE DONNÉES

L'application est structurée en microservices étanches orchestrés par Docker Compose :

```
[web] (React 19 / Vite 6)  <--- Proxy /api --->  [api] (FastAPI / Python 3.12)
       Port 8080                                        Port 8000
                                                           |
                                                    (Lecture seule :ro)
                                                           v
                                                  [target_lab] (SI Client)
```

### 3.1 Structure de Stockage des Données (100% Fichiers locaux)
Pour garantir la confidentialité des données des clients de DP Cyber Consulting et éliminer la complexité d'une base de données réseau, toutes les données sont stockées à plat sous forme de fichiers :

*   **Référentiels Réglementaires (`api/frameworks/`) :** Fichiers YAML éditables décrivant les exigences de conformité (`iso27001.yaml`, `nis2.yaml`, `dora.yaml`, `aiact.yaml`).
*   **Données des Projets d'Audit (`projects/<project_id>/`) :**
    *   `project.json` : Fichier maître stockant l'intégralité des métadonnées, de l'état de la Kanban, des checklists, du flag d'étapes validées, et des réponses aux formulaires.
    *   `targets/` : Répertoire contenant les fichiers de configuration techniques réels importés du SI client pour le scan technique.
    *   `reports/` : Répertoire d'archivage des rapports générés (Markdown, livrables).

---

## 🛠️ 4. ÉTAPES D'AUDIT CYBER (MÉTHODOLOGIE DÉTAILLÉE)

### Étape 1 : Cadrage &amp; Patrimoine (Périmètre NIST/EBIOS RM)
*   **Missions :** Définir les finalités d'affaires de l'entreprise.
*   **Valeurs Métier (Patrimoine immatériel) :** Processus clés, secrets industriels, fichiers clients.
*   **Biens Supports (Patrimoine matériel &amp; réseau) :** Serveurs, annuaires Active Directory, pare-feu, postes de travail.
*   **Sélecteurs de Modèles (Extensibles) :** Menus déroulants éditables dans le code (gabarits standard de l'industrie) pour accélérer le cadrage et l'onboarding.
*   **Sécurisation :** Génération de l'Accord de Confidentialité (NDA) dès l'onboarding pour sceller les échanges techniques.

### Étape 2 : Diagnostic &amp; RGPD (État des lieux)
*   **Diagnostic d'hygiène ANSSI :** Évaluation des politiques fondamentales (PSSI, gouvernance cyber, processus de patch management).
*   **Registre RGPD (Article 30) :** Répertorier les activités traitant des données personnelles de manière souveraine.
*   **Analyse d'Impact relative à la Protection des Données (AIPD / PIA) :** Évaluation obligatoire CNIL pour les traitements à haut risque (Évaluation de la nécessité, proportionnalité, gravité d'impact et mesures barrières de chiffrement).

### Étape 3 : Risques Tiers (TPRM / Third-Party Risk Management)
*   **Formule d'évaluation de la criticité fournisseurs :**  
    $$\text{Score de Risque} = \frac{\text{Dépendance} + \text{Pénétration SI} + (6 - \text{Maturité cyber}) + (6 - \text{Confiance})}{4}$$
    *   Si $\text{Score} \ge 4.0$ ➔ **Tiers Critique (Rouge)**
    *   Si $\text{Score} \ge 3.0$ ➔ **Tiers Élevé (Orange)**
    *   Si $\text{Score} \ge 2.0$ ➔ **Tiers Moyen (Bleu)**
    *   Sinon ➔ **Tiers Faible (Gris)**

### Étape 4 : Analyse des Menaces EBIOS RM Ateliers 2 à 4
*   **Événements redoutés :** Ransomwares, espionnage de brevet Biotech, arnaque au président (Pathé), fuite massive de données (Marriott).
*   **Séquence d'attaque opérationnelle :** Modélisation de chemin d'intrusion :  
    `Connaître (Reconnaissance) ➔ Rentrer (Intrusion) ➔ Trouver (Mouvement latéral) ➔ Exploiter (Vol/Chiffrement)`.
*   **Matrice de Risques SVG :** Placement visuel réactif sur la matrice de chaleur Gratité (1-4) × Vraisemblance (1-5).

### Étape 5 : Résilience, Continuité &amp; E3R ANSSI
*   **Cibles temporelles :** RTO (temps de reprise max), RPO (perte de données max autorisée).
*   **Séquence de remédiation d'incident majeur E3R (ANSSI) :**
    *   *Endiguement :* Isoler et figer l'attaque active (confinement VLAN/EDR).
    *   *Éviction :* Purger les accès administratifs et reprendre le contrôle des identités (krbtgt).
    *   *Éradication :* Nettoyer en profondeur les emprises malveillantes.
    *   *Reconstruction :* Rebâtir de façon durcie dès la conception (Security-by-design / IaC).

### Étape 6 : Plan de Traitement &amp; Livrables
*   **Plan d'Action :** Répartition des mesures d'experts dans 4 axes (*Gouvernance, Protection, Défense, Résilience*).
*   **Le Cyberdépart :** Sélection automatique de 6 recommandations vitales (Quick Wins) à impact immédiat.
*   **Exports multi-formats :** Compilation HTML bilingue prête à être ouverte sous Microsoft Word ou imprimée directement en PDF de haute qualité.

---

## 🛠️ 5. EXÉCUTION & COMMANDES UTILES (Pour le repreneur)

Pour faire tourner l'application localement sur la machine hôte :

1.  **Démarrer l'API FastAPI (Port 8000) :**
    ```bash
    cd api
    python -m uvicorn main:app --reload --port 8000
    ```
2.  **Démarrer le Frontend React (Port 5173) :**
    ```bash
    cd web
    npm ci           # Installe proprement les dépendances de façon déterministe
    npm run dev      # Lance le serveur de dev Vite
    ```
3.  **Lancer les tests unitaires du moteur d'audit :**
    ```bash
    cd api
    pytest
    ```

---
*Ce document sert de contrat technique immuable pour assurer la pérennité et la souveraineté technologique de GREEN SHIELD. Rédigé et mis à jour le 28 juillet 2026 par l'agent expert de Dorian.*
