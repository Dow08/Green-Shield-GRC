# Journal de bord - GREEN SHIELD

Ce document retrace l'ensemble des actions menées sur le projet afin d'assurer une traçabilité complète des évolutions techniques et fonctionnelles.

---

## [30/07/2026] — Volet stratégique ANSSI, alertes RGPD, vitrine régénérée

Trois améliorations enchaînées après les corrections d'identité de la session, plus la régénération de la vitrine `docs/exemples`.

**§14.2.3 — Volet stratégique de la remédiation ANSSI.** La séquence E3R (endiguement/éviction/éradication/reconstruction) est technique et opérationnelle ; il manquait les critères d'arbitrage Direction entre urgence de redémarrage et coûts/risques induits par un redémarrage précipité. `schema_version` **7** (`steps.resilience.strategie_remediation` : trois champs libres), exposé en Phase 5 sous la séquence E3R, repris dans le rapport de mission (chapitre Résilience, §7.3) et dans le PSSI/PRI (Word, HTML, Markdown, §2.4).

**Alertes d'échéances RGPD, portées sur tout le portefeuille.** L'échéance de conservation (F17) n'était visible qu'en ouvrant une mission une à une (`RgpdPanel`). Un bandeau sur le registre des missions signale maintenant, sans rien ouvrir : les missions à échéance dépassée (rouge) et celles à moins de 30 jours (ambre), chacune cliquable vers la mission concernée. S'appuie sur la route `GET /api/rgpd/echeances` déjà existante — aucun nouveau calcul, seulement sa mise en avant proactive.

**Logo personnalisé étendu aux exports HTML** — voir l'entrée précédente : ce qui restait « à faire » (M1, M2, M4) est fait le jour même, `charte.logo_data_uri()` branché dans `report_html.py`.

### Vitrine `docs/exemples` régénérée
Les 18 fichiers existants dataient d'avant les corrections du jour (pied de page peu lisible, vide sur la page de garde, identité codée en dur) et n'exposaient qu'un seul `.docx` par mission. Régénérés avec le code courant : **28 fichiers** (les 5 livrables Word pour chaque mission — pas seulement le rapport —, plus les 5 exports HTML et les 5 Markdown). Le `README.md` de la vitrine est mis à jour en conséquence (liens `.docx` ajoutés, description du format Word plus fidèle — elle affirmait encore « sept chapitres », reliquat d'avant la reconstruction complète du 31/07/2026).

### Deux tâches volontairement non traitées — signalées plutôt que contournées
Le plan de build restant comptait aussi **§14.3 (glossaire des 25 concepts)** et **§14.2.5 (NIST CSF en 6ᵉ parcours)**. Les deux citent une matière source externe (« Hermes ») absente de ce dépôt — aucun fichier de glossaire, aucun `references/nist-csf.md`, aucun script de scoring. Les construire aurait exigé d'inventer un contenu réglementaire/méthodologique (définitions, catégories NIST CSF, grille de maturité) — exactement ce que la philosophie « zéro invention » du projet interdit. Laissées de côté, à trancher avec l'utilisateur (obtenir la matière source, ou accepter un contenu construit et explicitement marqué comme non sourcé).

**14 tests ajoutés** (`test_schema_migration.py`, `test_report_docx.py`, `test_revue_export.py`). **560 tests backend, 150 tests frontend.**

---

## [30/07/2026] — L'application n'est plus dédiée à un seul consultant

Retour utilisateur sur le NDA envoyé pour relecture : « Dorian » et « DP Cyber Consulting » apparaissaient dans le document quels que soient l'auditeur et le cabinet réellement saisis dans Réglages — y compris quand ces champs étaient vides. Vérification faite, le défaut était générique : chaque module de génération de livrable (`report_docx.py`, `report_html.py`, `charte.py`, `report_builder.py`) retombait silencieusement sur `cabinet or "DP Cyber Consulting"` / un `"Dorian"` codé en dur, au lieu du paramètre `auditeur`/`cabinet` déjà reçu en argument. Corrigé dans les cinq livrables Word, les cinq exports HTML (M1 à M5) et les cinq exports Markdown, avec un même repli neutre (« Consultant » / « Cabinet non renseigné ») plutôt qu'un nom de personne. `Settings.tsx` ne pré-remplit plus le formulaire avec mon identité par défaut (champs vides à l'installation), et le message d'accueil du tableau de bord (`Home.tsx`) n'affiche « Bonjour, {prénom} » que si un nom a été configuré.

**Deux bugs de rendu supplémentaires** signalés sur le même NDA :
- **Pied de page presque illisible.** Le gris `_DOUX` choisi pour la dernière ligne du pied (contraste ~4,3:1) restait trop pâle une fois combiné au rendu grisé que Word applique par défaut à un pied de page inactif. Les trois lignes passent à la couleur du corps de texte (`_CORPS`, ~11:1) ; la hiérarchie visuelle reste portée par l'italique et la taille, pas par le contraste.
- **Grand vide blanc sur la page de garde.** Le bandeau coloré (logo, titre, méta) ne remplissait que sa hauteur de contenu, laissant un espace blanc jusqu'au pied de page sur toute page de garde courte (flagrant sur un NDA d'une page). Le bandeau prend maintenant la hauteur utile de la page (`AT_LEAST`, contenu centré verticalement) — plus de vide, la page de garde est pleine.

**35 tests ajoutés/adaptés** (`test_charte.py`, `test_report_docx.py`) vérifiant qu'aucun des cinq livrables Markdown ne contient plus « Dorian »/« DP Cyber Consulting » par défaut, et qu'une identité personnalisée (auditeur + cabinet) apparaît bien dans chaque document généré.

### Logo de cabinet personnalisable (rapports Word)
Nom et cabinet réglés, restait le logo — figé sur celui de GREEN SHIELD quel que soit le consultant. Choix confirmé avec l'utilisateur : garder le logo GREEN SHIELD par défaut, avec la possibilité d'en déposer un autre dans Réglages.

Un logo dépasse largement la longueur d'URL sûre en paramètre de requête GET une fois encodé en base64 : les cinq routes `.docx` (`report`, `nda`, `ebios`, `pssi`, `aipd`) passent donc de `GET` à `POST`, le corps JSON portant `auditeur`/`cabinet`/`logo`. Côté client, les liens `<a href download>` deviennent des boutons déclenchant un `fetch()` + téléchargement de blob (même schéma que `exportArchive`/`importArchive`), le nom de fichier étant repris de l'en-tête `Content-Disposition` de la réponse plutôt que déduit par le navigateur.

`charte.logo_bytes()`/`logo_data_uri()` centralisent la validation (signature PNG/JPEG vérifiée sur les octets réels, jamais sur le type MIME déclaré) : un logo absent, corrompu ou dans un format non pris en charge retombe silencieusement sur le logo GREEN SHIELD — la génération d'un rapport ne doit jamais échouer à cause d'une image. `Settings.tsx` ajoute le dépôt de fichier (PNG/JPEG, 300 ko max), un aperçu et un bouton de réinitialisation.

**14 tests ajoutés** (`test_charte.py`, `test_report_docx.py`, `test_projects_security.py`) couvrant la validation du logo, son embarquement réel dans le `.docx` généré (comparaison des octets de l'image insérée), et le branchement route → générateur.

### Extension aux exports HTML (M1-M5)
Ce qui était noté « reste à faire » plus haut est fait le jour même : `report_html.py` reçoit le même paramètre `logo` sur `build_report` (M1), `build_synthese` (M2) et `build_registre_conformite` (M4) — M3 et M5 n'ont pas de bandeau de marque, rien à y brancher. Les trois routes `.html` correspondantes acceptent `logo` en paramètre de requête (restées en `GET` : ces routes ne sont consommées par aucun écran du frontend aujourd'hui, seulement par script — la contrainte de longueur d'URL qui a fait basculer les routes `.docx` en `POST` ne s'applique donc pas de la même façon ici). **4 tests ajoutés. 559 tests backend, 150 tests frontend.**

---

## [30/07/2026] — Les quatre autres livrables en Word : NDA, EBIOS RM, PSSI/PRI, AIPD

Le rapport de mission avait déjà son identité Word (page de garde, sommaire, tableaux, pied de page à empreinte). Les quatre autres documents produits par `report_builder.py` (NDA, analyse EBIOS RM, PSSI & PRI, AIPD/PIA) n'existaient qu'en Markdown — un consultant qui voulait remettre un NDA signable au client n'avait rien d'autre à télécharger que du texte brut.

**`report_docx.py`** gagne quatre nouveaux bâtisseurs : `build_nda_docx`, `build_ebios_docx`, `build_pssi_docx`, `build_aipd_docx`. Même contenu que la version Markdown correspondante (même source de données, même structure), seule la mise en forme change. Là où c'est le même contenu qu'une section du rapport de mission (patrimoine, cartographie des menaces, écosystème des tiers, plan d'action), les bâtisseurs `_ch_patrimoine`/`_ch_risque`/`_ch_ecosysteme`/`_ch_traitement` sont **réutilisés avec leur propre numérotation** plutôt que dupliqués — l'EBIOS RM autonome numérote ses 4 chapitres 1 à 4, indépendamment de leur position dans le rapport complet.

Aidé par cet effort de réutilisation à repasser sur `report_html.py` et `report_docx.py`, un bug préexistant est ressorti : le chapitre « Plan de traitement » (chapitre **11** dans `report_html.CHAPITRES`) affichait encore des sous-titres « 10.1 »/« 10.2 » — reliquat d'avant l'ajout du chapitre AIPD, qui a décalé toute la numérotation en aval sans que ces deux chaînes codées en dur ne suivent. Les deux fichiers acceptent maintenant un paramètre `prefixe` sur les fonctions concernées (`_patrimoine`/`_ch_patrimoine`, `_risque`/`_ch_risque`, `_traitement`/`_ch_traitement`), avec la bonne valeur par défaut pour le rapport complet — le même paramètre qui permet leur réutilisation dans les documents autonomes sert aussi de garde-fou contre cette classe de bug.

**Routes et frontend.** Quatre routes `GET /api/projects/{id}/{nda,ebios,pssi,aipd}.docx` dans `projects.py`, sur le même schéma que `/report.docx` (auditeur/cabinet en requête, jamais stockés côté serveur). Dans `PhaseTraitement.tsx`, chacun des quatre livrables affiche désormais son bouton `.md` et son lien `Word (.docx)` côte à côte plutôt qu'un unique format Markdown.

Vérifié de bout en bout après redémarrage propre de l'API (le piège Windows `uvicorn --reload` documenté plus bas a de nouveau servi du code obsolète le temps du redémarrage) : les 5 routes `.docx` répondent, chaque fichier est un Word 2007+ valide, `Content-Disposition` porte le bon nom de fichier accentué.

**35 tests ajoutés** dans `test_report_docx.py` pour les quatre nouveaux bâtisseurs (fichier valide, empreinte en pied de page, réutilisation correcte du contenu partagé, aucune ligne de tableau vide, survie aux caractères spéciaux). **543 tests backend, 150 tests frontend.**

---

## [29/07/2026] — Points restants du todo : rendre visible ce qui était calculé sans être montré

Quatre points, un même défaut de fond : des données produites ou stockées mais jamais présentées.

**Cibles de continuité (RTO/RPO).** `steps.resilience.bcp_strategy` était rempli par défaut et repris dans le livrable PSSI/PRI, mais aucun écran ne l'affichait — le consultant **exportait des cibles temporelles qu'il n'avait jamais vues ni validées**. Trois champs éditables ajoutés en Phase 5. Constat trouvé en écrivant les tests de caractérisation, pas par relecture.

**Charges consommées (reste de F19).** Le cumul n'existait que mission par mission. Il apparaît désormais sur le tableau de bord du registre et, surtout, dans le rapport exporté : l'indicateur « charges consommées vs budget vendu » exigé par Hermes ne parvenait jamais au client.

**Taux de couverture technique (F10).** La promesse « preuve technique plutôt que déclaratif » est vraie mais partielle — la taire serait une survente. `api/modules/couverture.py` rapproche chaque contrôle organisationnel des règles techniques qui l'appuient et affiche le taux réel, en Phase 4 comme dans le rapport, en précisant explicitement que le reste repose sur du déclaratif. La correspondance se fait sur la référence de clause avec **frontière stricte** : sans elle, `A.8.2` serait comptée comme couverte par une règle ne visant qu'`A.8.20`, et le taux serait artificiellement gonflé. Vérifié sur la démo : 3 contrôles sur 4, `ISO-A.5` (politiques) correctement **non** couvert — aucune règle automatisée ne peut constater l'existence d'une PSSI.

**Bundle.** `React.lazy()` sur les 5 modules, l'accueil restant chargé d'emblée : le fichier initial passe de 471 kB / 134 kB gzip à **329 kB / 105 kB gzip**, et le registre de missions (119 kB) n'est plus téléchargé qu'à son ouverture.

### Un point volontairement laissé ouvert
L'enrichissement des référentiels YAML (**F2**) n'a pas été fait, et c'est délibéré : l'audit prescrit d'enrichir **au fil des missions réelles**, pas en amont. Générer en masse 93 intitulés ISO reviendrait à inventer du contenu métier — ce que la philosophie « zéro invention » interdit — tout en frôlant la limite de **F3** (copyright ISO/AFNOR). Le taux de couverture désormais affiché rend d'ailleurs cette incomplétude **visible plutôt que masquée**.

**344 tests backend + 108 tests frontend.**

---

## [29/07/2026] — F17 et F18 : conformité RGPD du consultant et licence

### F17 — Conservation et purge des données personnelles
Le paradoxe relevé par l'audit : GREEN SHIELD vend du registre Art. 30 à ses clients sans tenir le même standard sur ses **propres** traitements. Les grilles d'entretien recueillent noms, fonctions et déclarations de personnes physiques — le consultant en est responsable de traitement.

`schema_version` **4** (`socle.rgpd_consultant`) et `api/modules/retention.py` : durée de conservation par mission, date de fin, échéance calculée, vue transverse des missions échues. Le délai ne court qu'à partir de la **fin** de la relation, pas de son début.

**La purge applique la minimisation, pas la destruction.** Elle efface les personnes interrogées et laisse intacts les constats d'audit, l'inventaire et le plan de traitement — qui ne sont pas des données personnelles et portent la valeur du travail. Une mission purgée reste exploitable, elle ne désigne simplement plus personne. Un instantané est pris juste avant (l'opération est irréversible) et les deux actions sont tracées au journal d'audit.

Vérifié de bout en bout : politique fixée → échéance calculée à `-560 jours` (échue) → purge de 4 enregistrements → entretiens et participants vidés, 2 biens supports et la gouvernance conservés, point de restauration créé.

### F18 — Licence
Le dépôt était **public sans licence**, situation juridiquement ambiguë. Choix retenu : **PolyForm Noncommercial 1.0.0**, en cohérence avec le dépôt jumeau RED SHIELD — lecture, étude et usage non commercial permis, exploitation commerciale par un tiers exclue, droits de l'auteur intacts (y compris l'usage en mission facturée).

Le texte a été **récupéré depuis le dépôt officiel PolyForm** plutôt qu'écrit de mémoire, et sa présence mot pour mot vérifiée par comparaison : une licence retouchée n'est plus la licence qu'elle prétend être.

**F3 vérifié à cette occasion** : les référentiels livrés ne contiennent que des identifiants et intitulés courts reformulés (132 caractères au plus), jamais de texte normatif ISO. La limite est désormais écrite dans le README pour qu'un contributeur ne l'enfreigne pas par méconnaissance.

**322 tests backend + 108 tests frontend.**

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

### 10. Jalon 2 — décisions méthodologiques tranchées du spec (§14.1bis et §14.2)

Trois points que le spec laissait ouverts ou que le code contredisait, traités le 29/07/2026 avec le même exigence de traçabilité : chaque décision est justifiée sur les données réelles, pas sur une préférence.

**§14.1bis — Criticité des tiers scindée par volet** (`api/modules/tprm.py`)
- **Volet Consulting** : la moyenne arithmétique `(dép + pén + (6−mat) + (6−conf)) / 4` est remplacée par la formule ANSSI `(dépendance × pénétration) / (maturité × confiance)`. Justification vérifiée sur les tiers pré-remplis avant d'écrire une ligne : la moyenne donnait AWS 3,50 et ESN 3,75 — indistinguables, et dans le mauvais ordre au regard du risque. Le ratio donne 1,56 et 2,22 (écart de 1,4×, l'ESN ayant plus de pénétration pour moins de maturité et de confiance) et fait tomber le cabinet comptable de 2,25 à 0,25. L'amplitude du classement passe d'un intervalle de 1,5 point à un facteur 9 : il redevient priorisable, ce qui est l'objet même de l'atelier EBIOS RM 3.
- **Volet GRC** : **aucun score**. DORA et NIS2 ne se réclament pas d'EBIOS RM ; leur appliquer un scoring de risque inventerait une exigence qu'ils ne portent pas. À la place, quatre exigences vérifiables par tiers (registre d'information DORA Art. 28.3, clauses contractuelles Art. 30, stratégie de sortie, évaluation avant acquisition NIST ID.RA-10), avec une métrique « prestataires sans écart » et non une criticité.
- **Aucune note n'est recalculée en silence.** Un consultant a pu présenter une criticité à son client : chaque tiers porte donc la méthode qui l'a produit (`ratio_anssi` / `moyenne_historique`), la migration `schema_version` 5 se contente de l'étiqueter, et le passage au ratio est une action explicite (`POST /api/projects/{id}/tprm/recalculer`) précédée d'un instantané. Un bandeau propose la migration sans l'imposer.
- **Duplication de formule éliminée au passage** : `PhaseTprm.tsx` possédait sa propre copie du calcul et renotait le tiers à chaque édition — les deux versions avaient déjà divergé. Le navigateur n'envoie plus que les curseurs (`POST /api/projects/{id}/tprm/tiers`), le serveur seul note. Un test (`test_docx_export.py`) échoue désormais si une affectation de `score` ou `rating` réapparaît côté frontend.

**§14.2.1 — Les cinq obligations organisationnelles de l'AIPD** (`api/modules/aipd.py`)
Le module couvrait les quatre volets d'*analyse* ; manquaient les obligations de *conduite* : avis du DPO (Art. 35 §2), avis des personnes concernées (Art. 35 §9), confrontation aux listes CNIL (Art. 35 §4-5), réexamen à chaque évolution du risque (Art. 35 §11) et consultation préalable de la CNIL (Art. 36 §1). Sans elles, une AIPD peut être parfaitement argumentée et néanmoins irrégulière. La cinquième est **conditionnelle** : elle n'entre au dénominateur que si le risque résiduel après mesures est qualifié d'élevé — la compter systématiquement afficherait un taux inférieur à la réalité. Ce risque résiduel démarre à « non évalué » et non à « acceptable » : le supposer acceptable ferait disparaître l'obligation Art. 36 sans que personne ne l'ait jugée. Un avertissement explicite s'affiche tant qu'un risque élevé n'a pas été soumis, et le livrable AIPD porte le tableau des obligations *y compris les manques* — taire un manque laisserait croire la démarche achevée.

**§14.2.4 — Rattachement des pratiques aux référentiels** (`api/modules/controles_techniques.py`)
`vulnerabilities_active` et `logging_active` existaient sans mapping : une case cochée qui ne se rattache à rien ne vaut rien devant un client. Quatre pratiques sont désormais rattachées à leurs contrôles (inventaire → NIST ID.AM + CIS 1/2, vulnérabilités → CIS 7 + NIST ID.RA-01, journalisation → CIS 8, évaluation fournisseurs → NIST ID.RA-10), avec badges à l'écran et section dédiée au rapport d'audit citant la phase d'origine de chaque constat. Le module lit un état saisi ailleurs, il ne le rejuge pas — et sur une mission Consulting, l'évaluation fournisseurs est « non tracée » plutôt que « non satisfaite », l'écart serait inventé.
- **Bug réel corrigé** : `logging_active` comptait pour 5 % de la progression de mission alors qu'**aucun écran ne permettait de le cocher**. Case ajoutée en Phase 5.

**Vérification** : 448 tests backend (+57) et 150 tests frontend (+31), `tsc --noEmit` propre. Vérifié en conditions réelles dans le navigateur, pas seulement en unitaire : classement ANSSI affiché sur une mission Consulting, check-list DORA sur la mission de démo GRC (bascule d'exigence persistée côté serveur), bascule 0/4 → 0/5 des obligations AIPD au passage en risque élevé avec apparition de l'alerte Art. 36, badges CIS 7 / ID.RA-01 / CIS 8 rendus, et taux de rattachement passant de 25 % à 50 % après activation de la journalisation.

### 11. Rapport Word reconstruit en `python-docx` direct — le `.docx` ne ressemblait à rien

Constat le 31/07/2026, captures d'écran Word à l'appui : le rapport `.docx` n'avait aucun rapport visuel avec le rapport HTML (M1) livré la veille — police par défaut, aucune couleur, page de garde nue. En creusant `api/modules/docx_export.py`, deux causes distinctes :

- Le `.docx` passait par un **gabarit `docxtpl` statique** (`api/templates/rapport_iso27001.docx`), généré en `python-docx` nu par `build_templates.py` — jamais mis à jour au fil des jalons : **7 sections génériques** (aucun TPRM, AIPD, E3R, DORA) pendant que `report_html.py` montait à **13**.
- Le titre était **écrit en dur** — `"titre_rapport": "Rapport d'audit de conformité"` — affiché tel quel même sur une mission de conseil, indépendamment du volet réel.

Quatre solutions évaluées avec l'utilisateur : retoucher le gabarit existant (écarté — reconduit le problème, deux implémentations tenues à la main qui peuvent diverger) ; conversion HTML→DOCX par bibliothèque tierce type `htmldocx` (écarté — dépendance non testée, fidélité incertaine sur le dégradé de la page de garde et les badges de chapitre) ; Pandoc (écarté d'emblée — dépendance native, interdite en local par la règle n°1) ; **reconstruire en `python-docx` directement, sur les mêmes données que le HTML** — retenu.

**`api/modules/report_docx.py`** (nouveau) : page de garde à bande verte foncée (logo, titre, client, méta), sommaire, 13 chapitres + signatures, tableaux tramés (en-tête `#F2FBF7`, cellules de sévérité colorées dans la même palette que l'app), pied de page avec l'empreinte SHA-256. Deux points de passage uniques empêchent HTML et Word de diverger à nouveau :
- `report_html.CHAPITRES` (renommé depuis `_CHAPITRES`) — la liste des titres de chapitre, importée telle quelle par les deux rendus.
- `report_html.titre_et_meta()` (extrait de `build_report`) — même titre, même bandeau méta sur les deux formats. `test_le_titre_est_identique_a_celui_du_rapport_html` verrouille l'égalité, et `test_chaque_chapitre_a_son_batisseur` échoue si un chapitre est ajouté à l'un sans l'autre.

**Retiré** : le gabarit `api/templates/rapport_iso27001.docx`, `build_templates.py`, la dépendance `docxtpl` (requirements.txt), et dans `docx_export.py` tout ce qui ne servait qu'au gabarit (`build_iso27001_context`, `render_iso27001`, `_collect_constats`, `_score_and_band`) — ne restent que les utilitaires réellement partagés (`data_fingerprint`, `mention_reserve`, `STATUS_LABELS`).

**Bug trouvé en inspectant le `.docx` régénéré**, pas par un test : le tableau de signatures avait une ligne entièrement vide — `doc.add_table(rows=2, ...)` réserve déjà une deuxième ligne, et y appeler ensuite `table.add_row()` en ajoutait une troisième au lieu de remplir la deuxième. Corrigé (`rows=1`), et verrouillé par `test_aucune_ligne_de_tableau_n_est_entierement_vide`, qui parcourt tous les tableaux du document plutôt que de ne tester que les cas déjà connus.

**Tests** : `test_docx_export.py` recentré sur les utilitaires survivants (retire les tests qui appelaient l'ancien `render_iso27001`) ; nouveau `test_report_docx.py` (21 tests) — fichier Word valide, titre par volet, parité de sommaire avec `report_html.CHAPITRES`, toutes les données d'une mission complète restituées chapitre par chapitre, section vide annoncée explicitement, volet GRC sans colonne « Ratio », statuts lisibles (pas de `NON_CONFORME` brut), empreinte au pied de page, caractères spéciaux (`&`, `<`, `>`) intacts, aucune ligne de tableau vide. **508 tests backend** (+18 nets), tous verts. Les deux missions de démonstration (`docs/exemples/`) régénérées : parité de chapitres confirmée par script, aucune anomalie de texte, aucune cellule ni ligne vide.

### 12. Rapport Word — largeurs de colonnes et contraste corrigés

Retour immédiat après livraison du rapport reconstruit (§11) : les tableaux étaient visuellement cassés — colonnes toutes de largeur égale quel que soit leur contenu (une colonne « G » à un chiffre aussi large qu'une colonne de scénario sur huit lignes), et la dernière ligne du pied de page presque invisible.

**Cause des tableaux** : un tableau `python-docx` créé sans largeur de colonne explicite se répartit à parts égales à l'ouverture dans Word, quelle que soit la longueur du contenu — `table.autofit = True` ne suffit pas à empêcher ça. Corrigé par `_fixer_largeurs()` (`api/modules/report_docx.py`) : layout fixe (`autofit = False`) et largeur posée explicitement sur *chaque cellule de chaque ligne*, pas seulement sur `table.columns[i]` — cette dernière ne met à jour que les lignes déjà présentes au moment de l'appel, jamais celles ajoutées ensuite par `add_row()`. `_table()` accepte désormais un paramètre `largeurs` (poids relatifs, ex. `(0.7, 2.6, 0.55, 0.55, 2.6)` pour ID/Scénario/G/V/Mesure), renseigné à chacun des vingt appels du module en fonction de ce que chaque colonne contient réellement.

**Cause du contraste** : une couleur `97A5A0` (contraste ~2:1 sur blanc) sur la dernière ligne du pied de page, en plus d'être en italique et à 6 pt. Remplacée par le même gris que le reste du pied.

**Au passage** : le document ciblait la taille Letter par défaut de `python-docx` au lieu de l'A4 déjà utilisé par le rapport HTML (`@page{size:A4}`) — incohérence latente, jamais signalée, corrigée dans la foulée puisque la géométrie de page était déjà le sujet.

**Vérifié** : script d'audit sur une mission complète — 20 des 22 tableaux du document ont des largeurs non uniformes correctes (les 2 restants sont volontairement à poids égal — cadrage « cible »/« valeur retenue » et bloc de signatures) ; page 21,0 × 29,7 cm confirmée. 508 tests toujours verts.
