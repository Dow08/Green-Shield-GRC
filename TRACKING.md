# Journal de bord - GREEN SHIELD

Ce document retrace l'ensemble des actions menées sur le projet afin d'assurer une traçabilité complète des évolutions techniques et fonctionnelles.

---

## [29/07/2026] — Sprints 2 et 3 du plan d'amélioration

### Sprint 2

**Export/import de mission en archive chiffrée (F14 + reste de F15).** Aucune sauvegarde ni portabilité n'existait : point unique de défaillance incohérent pour un outil qui vend du PCA/PRA. `api/modules/archive.py` produit une archive ZIP chiffrée **AES-256** — elle quitte le disque chiffré du poste (clé USB, pièce jointe, remise au client), c'est le vecteur le plus exposé. L'import traite l'archive comme une **entrée non fiable** : traversée de chemin (Zip Slip) refusée à la lecture *et* à l'écriture, taille décompressée plafonnée, structure validée, identifiant repassant par `path_safety`.

**Coquille applicative responsive.** `App.tsx` et `Sidebar.tsx` n'avaient aucune classe responsive alors que l'usage tablette est avéré. Barre latérale en tiroir sous `md`, fermeture au clic extérieur et à Échap. **Piège Tailwind v4 documenté dans CLAUDE.md** : `translate-x-0` ne reprenait pas la main sur `-translate-x-full` (ces utilitaires écrivent la propriété CSS `translate` en v4, et le style calculé restait à `-100%` malgré la bonne classe dans le DOM) ; les décalages arbitraires négatifs ne sont pas générés non plus. Bascule sur `hidden`/`flex`.

**Découpage de `Projects.tsx` : 2044 → 652 lignes.** Un test de caractérisation (10 parcours couvrant les 6 phases) a été écrit **avant** le refactor — le fichier n'avait aucun test. Chaque phase devient un composant possédant son propre état d'interface ; le corps JSX est repris tel quel pour minimiser le risque. La réinitialisation au changement de mission passe par la `key` des composants plutôt qu'une cascade de setters.

**Revue de complétude avant export.** Les exports remplaçaient silencieusement toute donnée absente par « N/A » : un rapport pouvait partir chez un client criblé de trous. `revue_export.py` énumère les manques avec la phase où les compléter, en deux niveaux (bloquant / recommandé). Il ne remplit rien — c'est exactement la promesse « zéro invention ».

### Sprint 3

**Identité visuelle des livrables** (demande explicite du consultant). `api/modules/charte.py` : logo embarqué en base64 — un livrable doit rester lisible hors ligne, sans dépendre d'un fichier joint qui se perdrait —, en-tête marque/cabinet/client/référence, bandeau de confidentialité, pied portant l'empreinte SHA-256. Appliquée aux 5 livrables Markdown et au gabarit Word, depuis la même source d'image.

**Extraction de `report_builder.py`** (prérequis du point précédent) : la génération des livrables quitte `projects.py` (1233 → 970 lignes). Le module ne connaît ni HTTP ni disque, ce qui a permis d'écrire 21 tests sur le contenu réel — dont deux non-régressions de l'audit sécurité (V-05 empreinte, V-06 nom de fichier).

**Historique versionné (F9).** Instantané automatique à chaque validation de phase, restauration depuis l'interface, état courant sauvegardé avant tout écrasement, historique embarqué dans l'archive. Le nom d'instantané venant du client, il est validé par motif strict avec vérification d'appartenance en défense en profondeur.

**Jeu de démonstration (F16).** Démontrer l'outil exigeait d'ouvrir une mission cliente réelle. Le bouton « Mission de démo » crée une mission fictive marquée `is_demo`, avec du temps consommé et une configuration SSH volontairement vulnérable — le scan y trouve 5 écarts dont 2 critiques.

**Nettoyage.** Le projet de test « cassiopé » supprimé à la demande du consultant, et la migration depuis l'ancien emplacement rendue **unique** (marqueur `.legacy-migre`) : elle s'exécutait à chaque import du module et recopiait les missions dans tout `GREENSHIELD_DATA_DIR` — une mission volontairement supprimée réapparaissait au redémarrage suivant.

### Faille multiplateforme trouvée par la CI
Une entrée d'archive nommée `..\..\windows\evil.txt` est un **simple nom de fichier sous Linux** (l'antislash y est un caractère valide) : elle n'y traverse pas. Mais la même archive extraite **sous Windows** traverserait réellement. La validation ne pouvait donc pas dépendre du système qui extrait. L'antislash est désormais refusé explicitement — la spécification ZIP impose `/`.

Le test de cette règle attaque `_nom_sur` directement plutôt que de passer par un aller-retour ZIP : `zipfile` normalise les antislashs sous Windows mais pas sous Linux, ce qui rendait le test dépendant du système — exactement le piège qui masquait l'écart.

### Bilan
**294 tests backend + 96 tests frontend**, tous verts. Chaque fonctionnalité vérifiée en conditions réelles (HTTP ou navigateur) sur des missions **fictives**, jamais sur des données clientes.

---

## [29/07/2026] — Identité visuelle + Sprint 1 du plan d'amélioration

### 0. Logo officiel intégré
- Le logo (bouclier + arbre de vie) attendait à la racine du dépôt sans être branché. Version 256 px optimisée (2,1 Mo → 104 ko) déposée en `web/public/logo.png`, utilisée dans la pastille de la barre latérale (`Sidebar.tsx`, remplace l'icône lucide générique) et en favicon (`index.html`). Vérifié en navigateur (chargement 200 OK).
- **Rappel posé** dans [todo.md](todo.md) : maquettes stylisées des rapports (NDA, EBIOS RM, PSSI/PRI, AIPD, rapport GRC, DOCX) restant à réaliser — aujourd'hui feuille de style d'impression générique, sans charte ni logo.

### 1. Journal d'audit des actions sensibles (P0)
- **Constat de l'audit :** aucune trace n'existait de qui avait créé, modifié, exporté ou **supprimé** une mission (`grep logging` → 0 résultat dans `api/`). Angle mort pour un outil qui vend de la traçabilité GRC.
- `api/modules/audit_log.py` — logging stdlib, `RotatingFileHandler` (5 × 1 Mo), `propagate=False` pour ne pas polluer la sortie uvicorn. **Ne lève jamais** : disque plein ou droits insuffisants n'empêchent pas l'opération métier d'aboutir.
- `api/modules/data_paths.py` — résolution des emplacements de données extraite de `projects.py` et partagée (missions + journal), sans duplication de la logique `GREENSHIELD_DATA_DIR`.
- **Actions tracées :** création / modification / suppression de mission, upload, scan technique, import de référentiel, export (Markdown et DOCX), appels Copilote (mission et portefeuille, avec la **source réelle** — c'est la seule circonstance où des données quittent le poste), import Collecte technique, et **tentatives de traversée de chemin rejetées** (signal de sécurité).
- **Confidentialité :** le journal enregistre l'action et l'identifiant de mission, **jamais** le contenu — constats, vulnérabilités, données personnelles des personnes interrogées, ni le texte des prompts. Un test dédié le vérifie explicitement.
- **Tests :** `test_audit_log.py` (8) + `test_audit_log_integration.py` (9). Vérifié de bout en bout contre un vrai serveur sur un répertoire de données jetable.

### 2. Chiffrement au repos documenté (F15, P0)
- Section « ⚠️ Prérequis d'exploitation (non négociables) » en tête de [README.md](README.md) : chiffrement de disque (avec les commandes de vérification `manage-bde -status` / `lsblk -f`), restriction réseau au loopback, aucune donnée client dans git. Tableau « où vivent les données » ajouté.
- README également remis à jour : les 4 modules sont désormais listés comme actifs (la table annonçait encore 3 modules « 🔜 »), section Tests et index de documentation ajoutés.

### 3. Intégration continue (P1)
- `.github/workflows/ci.yml` — sur push et pull request vers `main` : job backend (pytest) et job frontend (typecheck, lint, tests, build), avec cache pip/npm. `GREENSHIELD_DATA_DIR` pointé vers un répertoire jetable du runner pour qu'aucun test n'écrive dans l'emplacement par défaut.
- Séquence validée localement à l'identique avant commit ; casse des imports relatifs vérifiée une à une (piège classique Windows → Linux, invisible en local).

### 4. Durcissement de la CSP (P2)
- `'unsafe-inline'` **retiré de `script-src`** : le build Vite de production n'émet aucun script inline (vérifié sur `dist/index.html`, puis dans un vrai navigateur servant le build sous la CSP candidate — zéro violation console sur les 4 vues).
- `'unsafe-inline'` **conservé sur `style-src`** : framer-motion écrit des attributs `style="opacity: …; transform: …"` au runtime ; le retirer casse toutes les animations. Vérifié empiriquement, pas supposé.
- `https://img.shields.io` retiré (badges présents uniquement dans le README, rendu par GitHub). Ajout de `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`, `form-action 'self'`.

### 5. Suivi du temps consommé (F19)
- **Cycle de vie complet respecté** (règle CLAUDE.md) : `schema_version` 3 avec migration `_to_v3` → routes backend → types TypeScript → client API → UI → tests des deux côtés.
- Modèle : journal d'entrées horodatées (`socle.temps.entrees`), pas un chronomètre live qui perdrait son état à la fermeture. Validation stricte côté serveur : durée > 0, plafond à 24 h par entrée (garde-fou anti-faute de frappe), phase dans une liste fermée, note tronquée à 200 caractères.
- `TempsPanel.tsx` : total cumulé, ventilation par phase, comparaison au **budget vendu** (`socle.qualification.budget`, champ qui existait depuis le jalon 1 sans être exploité). `formatDuree` isolée dans `lib/duree.ts` (fonction pure, et son export depuis un fichier de composant cassait le Fast Refresh).
- **Régression détectée puis corrigée grâce à la vérification navigateur :** les deux routes de temps renvoyaient la progression *stockée* au lieu de la recalculer, ce qui faisait chuter la jauge de mission de 85 % à 0 % à chaque saisie. Les tests unitaires ne l'avaient pas vu (ils ne vérifiaient que les entrées de temps). Corrigé + test de non-régression dédié.
- **Tests :** `test_temps.py` (21, dont tous les cas limites de validation), `TempsPanel.test.tsx` (17), `duree.test.ts` (5).

### 6. Bug bloquant révélé par le premier run de CI — `python-multipart` manquant
- **Le premier run de CI a échoué**, et a immédiatement payé son investissement : `python-multipart` était **absent de `api/requirements.txt`** alors que la route d'import de configuration client (`UploadFile`/`File`) en dépend.
- **Gravité réelle :** FastAPI lève une `RuntimeError` **au moment de l'import** du module déclarant la route — pas à l'appel. Conséquence : avec une installation propre depuis `requirements.txt`, `api/modules/projects.py` ne s'importe pas et **l'API ne démarre pas du tout**, image Docker comprise. Le bug préexistait à cette session ; il était masqué parce que le paquet est installé par ailleurs sur le poste de développement.
- **Correctif :** `python-multipart==0.0.32` ajouté à `requirements.txt`, avec le commentaire expliquant pourquoi son absence est fatale à l'import.
- **Test de non-régression :** `api/tests/test_app_demarre.py` — vérifie que `main` s'importe et que les routes des 4 modules (dont `/api/projects/{p_id}/upload` et les routes de suivi du temps) sont réellement montées. Aucun test ne couvrait « l'application démarre-t-elle » : ils importaient tous des modules isolément.
- **Diagnostic de la CI amélioré au passage :** les logs bruts et le résumé de job d'Actions exigent une session authentifiée même sur un dépôt public (« Sign in to view logs »). La sortie pytest est donc republiée en **annotation**, canal exposé par l'API publique — sans quoi un échec de CI n'est pas analysable. Actions mises à jour (`checkout@v5`, `setup-python@v6`, `setup-node@v5`, Node 22) pour lever l'avertissement de dépréciation de Node 20.
- **Leçon :** les 152 tests passaient en local sous Windows/Python 3.14 avec des dépendances plus récentes que celles épinglées. La CI teste la combinaison qui compte réellement — Linux, Python 3.12, versions épinglées.

### Bilan de vérification
- **157 tests backend + 61 tests frontend**, tous verts. `typecheck`, `lint` (0 avertissement) et `build` propres.
- Vérifié en conditions réelles dans le navigateur sur une **mission fictive** dans un répertoire de données jetable — jamais sur les missions clientes réelles.
- Constats ouverts consignés dans [todo.md](todo.md), dont un découvert en session : `_migrate_legacy_projects()` recopie les données clients dans tout `GREENSHIELD_DATA_DIR`, à chaque démarrage.

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

### 9. Application des conventions frontend documentées dans CLAUDE.md
Suite à la revue d'un gabarit générique React/Next.js (28/07/2026), les points réellement transposables identifiés dans CLAUDE.md ont été implémentés (pas seulement documentés) :

- **Génération d'ID unifiée** (`web/src/lib/ids.ts`, `nextId()`) : remplace les 7 générateurs `"PREFIX-" + Math.random()` de `Projects.tsx` (valeurs métier, biens supports, registre RGPD, remédiations — gabarit et saisie personnalisée) par un algorithme séquentiel sans collision, miroir de `_next_bs_id` côté backend. Élimine le risque de collision d'id déjà identifié entre le formulaire manuel et l'import Collecte technique. Vérifié en direct : ajout d'un bien support sur la mission Cassiopé → `BS-04` généré correctement (BS-01 à BS-03 existants), puis retiré après vérification.
- **localStorage protégé** (`web/src/lib/storage.ts`, `safeGetItem`/`safeSetItem`) : tous les accès directs (`Settings.tsx`, `Projects.tsx`, `CopilotGRC.tsx`, `lib/api.ts`) passent désormais par ces wrappers `try/catch`. `Settings.tsx` affiche un état d'erreur explicite si l'enregistrement échoue (mode privé, quota dépassé) au lieu d'afficher un faux succès. Vérifié en direct par un test aveugle (`Storage.prototype.setItem` patché pour lever une exception) : l'état d'erreur s'affiche, l'écran ne casse pas.
- **Overlays fermables** (`web/src/lib/useDismissOnOutsideOrEscape.ts`) : les 3 menus déroulants de `Projects.tsx` (valeurs métier, biens supports, registre RGPD) se ferment désormais à `Échap` et au clic extérieur, avec `max-h-72 overflow-y-auto` sur les listes. Vérifié en direct dans le navigateur (clic extérieur et Échap testés séparément, les deux ferment bien le menu).
- **Accessibilité** : `aria-label` ajouté sur les 7 boutons icône-seule qui n'en avaient pas (suppression de valeur métier/bien support/traitement RGPD/tiers/remédiation, notification, suppression de mission).
- **`no-explicit-any` réduit à zéro** en dehors des fichiers de test (exception documentée) : `lib/api.ts` (`post`/`put` typés `unknown`, `frameworks.import` typé explicitement), `Projects.tsx` (`updateStepData` typé via un pont `Record<string, Record<string, unknown>>` plutôt que `any`, casts `as Remediation["axe"|"priority"]` au lieu de `as any`, annotations `: any` superflues supprimées sur des `.map()` déjà inférables).
- **`iconFor` extrait** de `Sidebar.tsx` vers `web/src/lib/icons.ts` (le composant `Sidebar.tsx` n'exporte plus que le composant lui-même — élimine le warning `react-refresh/only-export-components`).
- **Bug réel corrigé au passage** : `loadProjectsAndFrameworks` était référencée dans un `useEffect` avant sa déclaration `const` dans `Projects.tsx` (sans conséquence à l'exécution, mais fragile) — réordonné.
- **ESLint configuré** (`web/eslint.config.js`, flat config ESLint 10 + typescript-eslint) : `npm run lint` fonctionne réellement désormais (n'existait pas avant). Règles `react-hooks` limitées volontairement aux deux règles classiques (`rules-of-hooks`, `exhaustive-deps`) — le préréglage `recommended` de `eslint-plugin-react-hooks` v7 embarque par défaut les règles orientées React Compiler (`set-state-in-effect`, `immutability`...) qui signalent en erreur le pattern standard « fetch au montage + setState », légitime et déjà testé partout dans ce projet qui n'utilise pas le React Compiler.
- **Scripts npm ajoutés** : `typecheck`, `lint`.
- **Vérification complète, 4 commandes :** `npm run typecheck` (propre), `npm run lint` (0 erreur/warning), `npm run test` (42 tests, dont 16 nouveaux : `ids.test.ts` ×7, `storage.test.ts` ×5, `useDismissOnOutsideOrEscape.test.tsx` ×4), `npm run build` (réussit). Backend inchangé, re-vérifié : 113 tests toujours verts. Comportement vérifié en conditions réelles dans le navigateur pour chaque changement UI (pas seulement `tsc`).
