# Journal de bord - GREEN SHIELD

Ce document retrace l'ensemble des actions menées sur le projet afin d'assurer une traçabilité complète des évolutions techniques et fonctionnelles.

---

## [28/07/2026] - Évolutions Majeures : Hardening, Tests et Plateforme de Conseil Stateful (6 Phases)

### 1. Sécurité et Durcissement (Hardening)
- **Frontend Nginx :**
  - Ajout des en-têtes HTTP de sécurité essentiels pour contrer le clickjacking (`X-Frame-Options: DENY`), le reniflage MIME (`X-Content-Type-Options: nosniff`), la fuite de référents (`Referrer-Policy: no-referrer`) et les attaques par injection (`Content-Security-Policy`).
  - Basculement du conteneur `greenshield_web` sur une image non-privilégiée (`nginxinc/nginx-unprivileged:alpine`) écoutant sur le port non-privilégié `8080`.
  - Mise à jour du mappage des ports dans `docker-compose.yml` (`8080:8080`) pour s'adapter à la configuration non-privilégiée.
  - Remplacement de `npm install` par `npm ci` dans `web/Dockerfile` pour garantir la reproductibilité absolue des builds de production.
- **Backend FastAPI :**
  - Restriction du middleware CORS de l'API à la seule origine locale autorisée (`http://localhost:8080`), renforçant l'étanchéité locale de l'application hors environnement de développement.

### 2. Automatisation et Tests Unitaires (Qualité logicielle)
- **Dépendances :** Ajout de `pytest==8.3.3` dans `api/requirements.txt`.
- **Tests unitaires de l'API :**
  - `api/tests/test_parser.py` : Valide la robustesse et la tolérance aux fautes des parsers SSHD (`sshd_config`) et Nginx (`nginx.conf`).
  - `api/tests/test_engine.py` : Couvre l'exactitude de l'évaluation des règles GRC (Must Equal, Must Not Contain) et le traitement des cibles manquantes.

### 3. Base de données des Référentiels GRC (Extensible)
- Création du dossier `api/frameworks/` et de sa sous-arborescence `custom/`.
- Implémentation des fichiers de référentiels réglementaires au format Policy-as-Code YAML :
  - `iso27001.yaml` : Norme internationale de management de la sécurité (SMSI).
  - `nis2.yaml` : Directive européenne de sécurité des SI.
  - `dora.yaml` : Résilience opérationnelle pour le secteur financier.
  - `aiact.yaml` : Réglementation européenne sur les systèmes d'IA.

### 4. Moteur de Projets Backend et Intégration de la Méthodologie Complète (`projects.py`)
- **Structure dynamique :** Les missions sont cloisonnées dans le répertoire local de fichiers `projects/<project_id>/` :
  - `project.json` : Contient l'état complet de la Kanban, la progression calculée dynamiquement, et les données de formulaires.
  - `targets/` : Contient les fichiers de configuration techniques importés par client.
  - `reports/` : Contient les documents finaux générés par l'application.
- **Formulaire de Cadrage &amp; Patrimoine (Phase 1) :**
  - Cadrage du périmètre technique de l'audit et définition des missions/finalités de l'organisation.
  - Saisie et édition de l'Accord de Confidentialité (NDA) avec gestion des signatures locales et manuscrites.
  - Cartographie des **Valeurs Métier** avec typage RGPD automatique (synchro registre de traitements) et Inventaire des **Biens Supports** (Matériels, Logiciels, Réseaux, Locaux, RH) aligné NIST.
- **Diagnostic, État des lieux &amp; RGPD (Phase 2) :**
  - Évaluation de l'hygiène (PSSI en place, Gouvernance active, CIS 7).
  - Registre des activités de traitement RGPD (Article 30) dynamique avec synchronisation des valeurs métiers sensibles.
  - Module complet d'**Analyse d'Impact relative à la Protection des Données (AIPD / PIA)** selon les critères de la CNIL (Cadrage, Nécessité, Évaluation des risques vie privée, et Mesures d'atténuation).
- **Gestion des Risques Tiers (Phase 3 - TPRM / NIST ID.RA-10) :**
  - Cartographie de l'écosystème de sous-traitance et évaluation automatisée de la criticité cyber via 4 critères de pondération (*Dépendance, Pénétration, Maturité cyber, Confiance*).
- **Analyse des Menaces &amp; Scénarios EBIOS RM (Phase 4) :**
  - Cartographie des Événements Redoutés, identification des Sources de Risques (SR) / Objectifs Visés (OV), et modélisation des Scénarios Opérationnels d'intrusion (`Connaître -> Rentrer -> Trouver -> Exploiter`).
  - Intégration de fiches réflexes interactives basées sur des cas réels éprouvés (**Marriott** pour le chiffrement, **Pathé** pour la fraude président, et la **Biotech** pour le sabotage R&D).
- **Résilience &amp; Gestion de Crise E3R (Phase 5) :**
  - Centralisation des logs (CIS 8), politique de sauvegarde immuable avec cibles temporelles RTO/RPO.
  - Séquence de remédiation cyber séquentielle de l'ANSSI : **Endiguement ➔ Éviction ➔ Éradication ➔ Reconstruction**.
- **Plan de Traitement &amp; Copilote AI (Phase 6) :**
  - Feuille de route classée par Axes (*Gouvernance, Protection, Défense, Résilience*), sélection automatique de **6 mesures prioritaires "Cyberdépart"** NIS 2.
  - **Copilote Cyber AI Générative :** Intégration d'un module d'IA d'analyse de risques et de rédaction de recommandations d'expert cyber (Offline-ready).
- **Génération de documents Multi-formats (Word &amp; PDF) :**
  - Moteur d'export de rapports finaux formatés en Markdown/HTML de haute qualité pré-configurés avec des feuilles de style CSS d'impression professionnelles (NDA, Analyse EBIOS RM, PSSI/PRI, AIPD/RGPD, Rapport de conformité GRC complet). Ces documents s'ouvrent nativement sous Microsoft Word et s'impriment directement en PDF depuis le navigateur avec une mise en page d'édition soignée.

### 5. Interface Utilisateur &amp; Dashboards KPI SVG (`Projects.tsx`)
- **Stepper 6 phases :** Un stepper visuel et dynamique gérant l'auto-sauvegarde automatique.
- **Grille Heatmap SVG :** Rendu visuel interactif en temps réel de la matrice de chaleur Gravité × Vraisemblance (EBIOS RM).
- **TPRM Chart SVG :** Visualisation graphique de la répartition de criticité de la chaîne d'approvisionnement.
- **Modèles pré-remplis :** Pré-population systématique de tous les formulaires d'audit avec des gabarits cyber haut de gamme modifiables en un clic.
- **Validation TypeScript :** Compilation complète validée à 100 % sans erreur (`npx tsc --noEmit`).

### 6. Copilote IA — Bascule en ligne (Gemini) / hors-ligne réelle
- **Constat :** Les Réglages promettaient une bascule vers un LLM en ligne (Gemini/OpenAI) dès qu'une clé API était saisie, mais `Projects.tsx` envoyait toujours `key: ""` et le backend (`run_project_copilot`) ignorait le champ `key` — le Copilote restait figé sur les réponses locales pré-écrites quelle que soit la configuration.
- **Backend (`api/modules/projects.py`) :** Ajout de `_call_gemini_copilot()` (stdlib `urllib`, sans nouvelle dépendance) qui appelle `generativelanguage.googleapis.com` (Gemini 2.0 Flash) avec le contexte du projet quand une clé est fournie ; toute erreur (réseau, clé invalide, quota, format de réponse) retourne `None` pour un repli silencieux vers l'intelligence experte locale. La réponse expose désormais `source`: `online` / `offline` / `offline_fallback`.
- **Frontend (`Projects.tsx`) :** Lecture de `copilot_api_key` (`localStorage`, configurée dans Réglages) à l'appel du Copilote ; badge visuel affichant la provenance réelle de la réponse (En ligne — Gemini / Hors-ligne — intelligence locale / Hors-ligne, repli local).
- **Tests :** `api/tests/test_projects_copilot.py` (5 tests : sans clé, avec clé valide mockée, clé invalide → repli, projet introuvable → 404, erreur réseau → `None`). Suite complète : 49 tests backend (pytest) + 16 tests frontend (vitest), tous verts. Vérifié en conditions réelles via le navigateur (dev server + API relancée avec `--reload`).

### 7. Activation des deux derniers modules "À venir" : Copilote GRC & Collecte technique
- **Copilote GRC autonome** (`api/modules/copilot_grc.py`) — distinct du Copilote embarqué en Phase 6 (scopé à UNE mission) : agrège les constats RÉELS de **toutes** les missions du registre (tiers TPRM Critique/Élevé, événements redoutés EBIOS RM de gravité ≥3, non-conformités techniques AuditCraft-GRC, Cyberdéparts en attente). Aucune donnée inventée — chaque chiffre vient d'une lecture directe des `project.json`. Même bascule en ligne (Gemini)/hors-ligne que le Copilote de mission, via la passerelle partagée. `GET /api/copilot/context` (agrégat brut) + `POST /api/copilot/ask` (synthèse/priorisation).
- **`api/modules/ai_gateway.py`** (nouveau, extrait par refactor) — passerelle sortante unique vers Gemini, partagée par `projects.py` (Copilote de mission) et `copilot_grc.py` (Copilote transverse). Élimine la duplication de l'appel réseau.
- **Collecte technique** (`api/modules/collecte_technique.py`) — empreinte factuelle (pas de verdict de conformité, rôle strictement distinct d'AuditCraft-GRC) d'un fichier de configuration collé/déposé : détection par signatures de **contenu** (pas seulement le nom de fichier) pour OpenSSH, Nginx, Apache, MySQL/MariaDB, PostgreSQL, Docker Compose, `/etc/os-release`, avec repli tolérant sur type « inconnu » sans jamais lever d'exception. `POST /api/collecte/fingerprint` (analyse standalone) + `POST /api/projects/{id}/collecte/import` (ajoute l'actif détecté au registre des Biens Supports, Phase 1, avec génération d'un `BS-XX` sans collision).
- **Frontend :** `web/src/pages/CopilotGRC.tsx` (KPI de portefeuille + 3 colonnes de priorités + chat) et `web/src/pages/CollecteTechnique.tsx` (saisie config → empreinte → formulaire d'import pré-rempli vers une mission choisie). Composant `CopilotSourceBadge.tsx` extrait pour éliminer la duplication du badge de source entre les deux copilotes (mission + transverse). Les 3 modules du registre (`missions`, `copilot`, `collect`) sont désormais tous `status: "active"` dans `App.tsx`.
- **Tests :** `test_ai_gateway.py` (5), `test_copilot_grc.py` (12), `test_collecte_technique.py` (18) côté backend ; `CopilotGRC.test.tsx` (6) et `CollecteTechnique.test.tsx` (4) côté frontend. Suite complète : **84 tests backend + 26 tests frontend**, tous verts. `tsc --noEmit` propre. Vérifié en conditions réelles dans le navigateur : synthèse du Copilote GRC sur les 2 missions réelles du registre, empreinte Nginx réelle, import effectif d'un nouveau Bien Support (`BS-29`) dans la mission « test » sans collision d'identifiant.

### 8. Audit combiné Qualité Logicielle + SecOps/Pentest — 5 vulnérabilités CRITIQUES corrigées
- **Audit :** revue adversariale des 19 routes de l'API (validation, gestion d'erreurs, OWASP Top 10, IAM, secrets, durcissement Docker/nginx). Chaque hypothèse de vulnérabilité confirmée par un PoC isolé (répertoire jetable) avant d'être retenue. Verdict initial : `NO-GO LIVE` (5 CRITIQUES, 6 MAJEURS, 3 MINEURS).
- **V-02/V-03/V-04/V-06/V-07 — Path traversal (plusieurs endpoints)** : `p_id`, `fw_id`, `client` (nom de fichier exporté) et `file.filename` (upload) n'étaient jamais validés avant de construire un chemin disque. `DELETE /api/projects/..` permettait de faire résoudre `PROJECTS_DIR / ".."` vers le **parent** de `PROJECTS_DIR` et de le supprimer intégralement via `shutil.rmtree()`. Corrigé par un point de passage unique, `api/modules/path_safety.py` (`safe_path_component` : allowlist Unicode alnum + `_`/`-`, compatible avec les identifiants réels déjà en usage comme « cassiopé » ; `safe_filename` : réduction au nom de base + rejet des cas dégénérés), appliqué aux 10 points d'entrée concernés dans `projects.py`, `workflow_loader.py` et `collecte_technique.py`. Les 5 exports Markdown dérivent désormais leur nom de fichier de `p_id` (déjà sûr) plutôt que du champ libre `client`.
- **V-05 — Fausse signature cryptographique** : `SHA256:{hash(p_id)}` sur le NDA et le rapport d'audit utilisait `hash()` Python natif — ni SHA256, ni reproductible d'un redémarrage à l'autre (vérifié : deux process différents donnent deux valeurs différentes pour le même `p_id`). Remplacé par `docx_export.data_fingerprint(state)` (vrai `hashlib.sha256`, déjà correct côté export DOCX, désormais réutilisé côté export Markdown).
- **V-01 — Absence totale d'authentification** : par conception (outil mono-consultant), mais aggravée par la publication Docker du port `web` sur `0.0.0.0`. `docker-compose.yml` restreint désormais la publication à `127.0.0.1:8080:8080`, avec commentaire explicite sur la condition de retrait (authentification en place).
- **Tests de non-régression :** `test_path_safety.py` (14, le validateur isolément), `test_projects_security.py` (nouveau, 15 tests reproduisant exactement chaque vecteur du PoC de l'audit), + 1 test dans `test_workflow_loader.py` (V-07), + 1 dans `test_collecte_technique.py` (traversal sur l'import registre). Suite complète : **113 tests backend + 26 tests frontend**, tous verts.
- **Vérification réseau réelle (pas seulement unitaire) :** re-testé via `curl --path-as-is` (contourne la normalisation client-side de `..` que curl applique par défaut) contre un serveur relancé avec le correctif — `DELETE /api/projects/..` renvoie bien `400` au lieu de s'exécuter.
- **⚠️ Incident survenu pendant cette vérification :** la même commande `curl --path-as-is -X DELETE .../api/projects/..`, envoyée par erreur contre un processus serveur resté actif sur le port 8000 depuis *avant* le correctif (code non corrigé), a réellement supprimé `%APPDATA%\GreenShield\` — **perte définitive de la mission « test »** (aucune copie ailleurs). La mission « Cassiopé » a survécu car une copie existait encore dans `GREEN SHIELD/projects/cassiopé/` (ancien emplacement pré-F13, toujours dans le dépôt) et a été ré-importée automatiquement par `_migrate_legacy_projects()` au redémarrage. Leçon retenue : tout test d'exploitation, même après correctif supposé, doit s'exécuter dans un environnement isolé (répertoire jetable) — jamais contre un serveur dont l'état du code n'est pas confirmé à l'instant T.
