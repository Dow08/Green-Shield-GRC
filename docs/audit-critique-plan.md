# AUDIT CRITIQUE DU PLAN — GREEN SHIELD

> Revue adversariale du [spec-refonte-grc-consulting.md](spec-refonte-grc-consulting.md), menée le 28/07/2026 **sans biais de complaisance** : objectif = trouver ce qui casse avant de coder, pas valider le travail déjà fait.
> Méthode : notation 0-10 sur 6 axes → identification des frictions → alternatives → re-notation. Seul un résultat ≥ 9/10 sur les axes bloquants est retenu.

---

## 1. Notation initiale (avant correctifs)

| # | Axe | Note | Justification factuelle |
|---|---|:---:|---|
| 1 | Viabilité technique | 7/10 | Faisable, mais WeasyPrint/Windows et `project.json` monolithique sont des impasses connues |
| 2 | Différenciation marché | **5/10** | CISO Assistant occupe déjà le terrain revendiqué (voir F1) |
| 3 | Cohérence interne du plan | **5/10** | 3 contradictions non tranchées (F4, F5, + parcours dédié vs pivot) |
| 4 | Réalisme de la charge | **3/10** | Contenu des référentiels à ~2 % (F2), pour un consultant solo |
| 5 | Robustesse du build | **4/10** | Jalon 1 surchargé, 0 test frontend, refonte de 1939 lignes sans filet |
| 6 | Fidélité "zéro invention" | 8/10 | Bien pensé, mais le copilote LLM n'est pas contraint architecturalement |
| | **Moyenne** | **5,3/10** | → itération obligatoire |

---

## 2. Ce qui va (à conserver tel quel)

1. **Socle méthodologique Hermes** — workflows ISO27001 / EBIOS RM / NIS2 de niveau professionnel. Rare et solide.
2. **Insight "ISO 27001 pivot + crosswalk"** — évite de ré-auditer 4 fois la même chose. Juste et structurant.
3. **Pipeline unique de preuves** (AuditCraft + SIEM/EDR + cloud → une seule colonne) — bonne abstraction, évite 3 mécanismes concurrents.
4. **Policy-as-Code YAML déjà en place** — fondation d'évolutivité réelle, pas théorique.
5. **Rejet explicite de l'« IA agentique autonome »** — choix mûr, à contre-courant du marketing 2026, cohérent avec la promesse produit.
6. **Distinction visuelle `exemple pré-rempli` vs `rempli par le consultant`** — c'est le garde-fou concret du "on n'invente rien". Excellent.
7. **Hash + horodatage des livrables** — répond à un angle mort juridique réel du métier, quasi gratuit à implémenter.
8. **Persona "consultant externe multi-clients"** — réellement mal servi par le marché (voir F1).

---

## 3. Points de friction (numérotés, avec alternative)

### F1 — Différenciation surestimée : CISO Assistant occupe déjà le terrain ⚠️ CRITIQUE

**Fait vérifié** : CISO Assistant (intuitem, **français**, open source, auto-hébergeable) propose déjà nativement : **EBIOS RM avec les 5 ateliers et un graphe d'objets dédié**, la **quantification du risque (CRQ)**, le **BIA**, le **TPRM**, la privacy, **150+ référentiels avec mapping automatique**, un framework builder, et des intégrations API/n8n/MCP/Kafka.

→ Tombent donc, comme différenciateurs : EBIOS RM natif, quantification FAIR/CRQ, TPRM, multi-référentiel + crosswalk, souveraineté, open source. Le §10.1 du spec affirmait « aucun concurrent US ne fait EBIOS » — vrai pour Vanta/Drata, **faux pour le concurrent le plus proche, qui est français**.

**Ce qui reste vrai et défendable** : CISO Assistant est un **registre GRC pour une équipe interne (RSSI qui pilote son propre programme)**. Ce n'est pas un **cockpit de conduite de mission pour un consultant externe**. Il ne guide pas : lettre de mission, NDA, grille d'entretien par rôle interrogé, restitution CODIR, RETEX capitalisé, ROSI. Et son reporting est un point faible reconnu (issue GitHub ouverte « EBIOS RM : amélioration du rapport »).

**Alternative retenue** : repositionner explicitement GREEN SHIELD en **« cockpit de mission du consultant »**, pas en « plateforme GRC de plus ». Assumer la complémentarité : le client peut avoir CISO Assistant, le consultant a GREEN SHIELD. Concentrer l'effort sur les 3 choses que CISO Assistant ne fait pas : **guidage pas-à-pas de la mission**, **génération de livrables Word éditables**, **capitalisation RETEX personnelle**.

### F2 — Charge de contenu massivement sous-estimée ⚠️ CRITIQUE

**Fait vérifié** : les 4 fichiers `api/frameworks/*.yaml` contiennent **4 exigences chacun (16 lignes)**. ISO 27001 seul en compte 93 (Annexe A) + les clauses 4 à 10. Le contenu réel est à **~2 %** de ce que le plan suppose — alors que le spec prévoit 5 parcours × macro-phases × sous-étapes × exemples pré-remplis × questions d'entretien par rôle × gabarits DOCX.

→ **Le goulot d'étranglement n'est pas le code, c'est la rédaction du contenu métier.**

**Alternative retenue** : (a) découpler un **track contenu** du track code — le code générique doit être fini bien avant que le contenu soit complet ; (b) démarrer avec **un seul référentiel à profondeur limitée** (ISO 27001 : identifiants + intitulés courts) ; (c) rendre l'import de référentiel trivial (CSV/YAML) pour enrichir **au fil des missions réelles** plutôt qu'en amont ; (d) ne pas embarquer le texte normatif (cf. F3).

### F3 — Risque juridique : le texte ISO 27001 est sous copyright

**Fait** : les normes ISO 27001/27002 sont vendues (ISO/AFNOR). Reproduire l'intitulé + le texte des 93 contrôles dans un fichier distribué est un risque. NIS2, DORA, RGPD, AI Act = droit UE, librement reproductibles. EBIOS RM / guides ANSSI = libres.

**Alternative retenue** : embarquer **identifiants + intitulés courts** (référence factuelle, comme le fait CISO Assistant) et non le texte normatif ; laisser le consultant coller son propre texte s'il possède la norme ; documenter la limite. Sans objet tant que l'app reste à usage interne, **bloquant dès la première distribution/vente**.

### F4 — Contradiction : « extension incrémentale » vs réécriture réelle

**Fait** : la décision 11 dit « extension incrémentale », mais le plan introduit un nouveau modèle de données (`socle`/`grc`/`consulting`), un moteur de blocs qui remplace les formulaires figés, et un Kanban piloté par YAML qui remplace les phases codées en dur. Appliqué à `Projects.tsx` (1939 lignes), **c'est une réécriture**. Le label rassure et masque le vrai risque : deux paradigmes cohabitant dans le même fichier.

**Alternative retenue** : assumer une **réécriture par tranche verticale** dans un nouveau module (`web/src/modules/mission/`), l'ancien `Projects.tsx` restant fonctionnel jusqu'à la bascule. Côté données : champ `schema_version` dans `project.json` + **chaîne de migration** (pas un script one-shot, puisque le schéma bougera encore aux jalons 2 et 3).

### F5 — Conflit architectural : blocs libres vs docxtpl

**Fait** : `docxtpl` remplit un gabarit Word à partir de **champs connus** (`{{ client }}`, boucles sur listes typées). Un modèle de « blocs libres réordonnables » n'a par définition pas de structure prévisible. Les deux ne peuvent pas coexister naïvement : soit le gabarit se réduit à une boucle générique (et la mise en page professionnelle est perdue), soit la liberté d'édition est perdue.

**Alternative retenue** : **hybride assumé** — champs **structurés** pour les parties normées (registre des risques, SoA, TPRM, plan d'action → tables typées, boucles docxtpl propres) et **blocs libres uniquement dans les sections narratives** (synthèse exécutive, constats, recommandations).

### F6 — WeasyPrint impraticable sur le poste de dev

**Fait vérifié** : WeasyPrint exige GTK/Pango via MSYS2 sur Windows, ne supporte officiellement que Windows 10 64-bit, et cumule les tickets ouverts sur Windows 11 / Python récent. Le poste est **Windows 11 Pro / Python 3.14**.

**Alternative retenue** : **DOCX en sortie primaire** (`docxtpl` est pur Python, zéro dépendance native, fonctionne sur Windows). Pour le PDF : impression navigateur (déjà en place, zéro dépendance) en local, et WeasyPrint **uniquement dans le conteneur Docker Linux** si un PDF serveur est requis. **Le PDF ne doit jamais bloquer le développement local.**

### F7 — Jalon 1 surchargé : 4 fondations + 1 parcours + migration

**Fait** : le Jalon 1 empile Kanban générique YAML + moteur de blocs + moteur DOCX/PDF + bibliothèque de preuves + hash + parcours ISO 27001 + intégration AuditCraft + migration — soit 12 tâches **sans aucune démo intermédiaire**. Cela contredit frontalement le critère d'auto-vérification du Prompt 1 : « milestones indépendants et testables ».

**Alternative retenue** : insérer un **Jalon 0 — tranche verticale minimale** : créer un projet → remplir **une** phase ISO 27001 → exporter un DOCX. Un seul chemin bout-en-bout qui prouve toute la chaîne. Les fondations génériques se dérisquent sur un cas réel au lieu d'être conçues dans le vide.

### F8 — Zéro test frontend pour un refactor de 1939 lignes

**Fait vérifié** : `web/package.json` ne contient **ni vitest ni script de test**. La seule validation mentionnée dans TRACKING.md est `tsc --noEmit` — qui vérifie les types, pas le comportement. Or les composants génériques (blocs, Kanban) seront réutilisés partout : une régression s'y propage à toute l'application.

**Alternative retenue** : installer vitest et couvrir **les 2 composants génériques + le calcul de progression** avant de les brancher partout. Non négociable vu leur rôle de socle.

### F9 — `project.json` monolithique

**Fait** : tout est dans un fichier unique (kanban, formulaires, blocs, preuves, hash, 13 phases × 5 référentiels). Chaque autosave le réécrit intégralement → corruption possible si crash en cours d'écriture, et aucun historique.

**Alternative retenue** : **écriture atomique** (fichier temporaire + `rename`) dès maintenant, coût quasi nul ; **pièces jointes hors JSON** dans `projects/<id>/evidence/` ; **snapshot horodaté à chaque validation de phase** — ce qui répond en prime à l'exigence Hermes « tout livrable est daté et versionné ».

### F10 — AuditCraft couvre 8 règles (SSH/Nginx)

**Fait** : `grc_rules.yaml` contient 8 règles, couvrant environ 5 contrôles sur 93. La promesse « preuve technique réelle vs déclaratif » est vraie mais très partielle.

**Alternative retenue** : afficher explicitement le **taux de couverture technique** dans l'UI (« X contrôles sur Y appuyés par une preuve technique »). C'est honnête, factuel, et cela devient un **argument différenciant** — aucun concurrent n'affiche cette métrique — au lieu d'une survente.

### F11 — Le copilote LLM menace le principe « zéro invention »

**Fait** : un LLM qui « corrige un rapport » peut fabriquer un fait plausible. Le risque est existentiel pour la promesse produit, et une simple consigne de prompt ne suffit pas à le contenir.

**Alternative retenue** : **contrainte architecturale dure** — le copilote écrit uniquement dans une zone `suggestions[]` séparée, **jamais** dans les champs de données ; chaque suggestion cite le champ source dont elle dérive ; acceptation explicite obligatoire ; un export ne peut pas contenir de texte issu du LLM sans `validated_by_human: true`.

### F12 — Charge globale irréaliste pour un solo

**Fait** : 5 jalons couvrant 5 parcours référentiels + 13 phases consulting + connecteurs cloud/SIEM + LLM + moteur documentaire, en parallèle de missions réelles.

**Alternative retenue** : définir un **MVP démontrable** (Jalon 0 + 1 réduit : socle + ISO 27001 + export DOCX) qui a **déjà une valeur commerciale de démonstration**, et traiter le reste comme un backlog **priorisé par les besoins clients réellement rencontrés** — pas construit en spéculation.

---

## 4. Notation après correctifs (itération 2)

| # | Axe | Avant | Après | Correctif appliqué |
|---|---|:---:|:---:|---|
| 1 | Viabilité technique | 7 | **9** | F6 (DOCX pur Python, PDF non bloquant), F9 (écriture atomique) |
| 2 | Différenciation marché | 5 | **8** | F1 (repositionnement cockpit de mission), F10 (couverture technique affichée) |
| 3 | Cohérence interne | 5 | **9** | F4 (réécriture assumée), F5 (hybride champs/blocs) |
| 4 | Réalisme de la charge | 3 | **7** | F2 (track contenu découplé), F12 (MVP + backlog piloté par les missions) |
| 5 | Robustesse du build | 4 | **9** | F7 (Jalon 0 vertical), F8 (vitest sur les génériques), F4 (`schema_version`) |
| 6 | Fidélité "zéro invention" | 8 | **10** | F11 (contrainte architecturale LLM) |
| | **Moyenne** | **5,3** | **8,7** | |

L'axe 4 (réalisme de la charge) reste à 7/10 : il ne dépend pas d'une décision d'architecture mais du **temps réellement disponible**. C'est le risque résiduel assumé du projet — il se pilote par la réduction du périmètre, pas par la technique.

---

## 5. Verdict de viabilité

**Le projet est viable et apporte une plus-value réelle — à condition d'être repositionné.**

- ❌ **Non viable** comme « plateforme GRC open source souveraine » : CISO Assistant occupe ce terrain avec une équipe financée, 150+ référentiels et EBIOS RM natif. Une construction solo n'y rattrapera pas son retard.
- ✅ **Viable et différenciant** comme **cockpit de conduite de mission pour consultant** : guidage pas-à-pas, livrables Word éditables, capitalisation RETEX, preuve technique mesurée. Ce segment est réellement mal servi — les plateformes GRC servent le RSSI interne, pas le consultant externe qui enchaîne les missions.
- ✅ **Valeur immédiate garantie même en cas d'arrêt** : c'est un outil de production personnel et une pièce de portfolio démontrable en entretien ou en rendez-vous commercial, indépendamment de toute ambition marché.

---

## 6. Plan de build corrigé

| Jalon | Contenu | Critère de sortie (testable) |
|---|---|---|
| **0** *(nouveau)* | Tranche verticale : créer un projet → 1 phase ISO 27001 → export DOCX | Un `.docx` s'ouvre dans Word sans avertissement, contenant des données réellement saisies |
| **1** | Généralisation : Kanban YAML, moteur de blocs (hybride F5), socle commun, AuditCraft branché, **catalogue de mesures (G3)**, `schema_version` + migration `cassiopé`, vitest sur les génériques, écriture atomique, **données hors dépôt (F13)** | Les 4 macro-phases ISO 27001 sont remplissables et exportables ; tests verts |
| **2** | Volet Consulting (13 phases), MITRE ATT&CK, FAIR, présentation CODIR, PRI guidé, **ratio ANSSI + radar parties prenantes (§14.1bis)**, **checklist architecture (G2)**, **exercice de crise (G4)**, **dossier d'homologation (G1)** | Une mission conseil complète est réalisable de bout en bout |
| **3** | Compléments NIS2 / DORA / RGPD, bibliothèque de preuves multi-référentiels, bouton "Vérifier les référentiels", ingestion SIEM/EDR + cloud v1, alertes d'échéances, **registre des violations (G5)** | Un même client auditable sur 2 référentiels sans ressaisie |
| **4** | Parcours EU AI Act | — |
| **5** | Copilote LLM (contraint F11), connecteurs live v2, dossier de preuve partageable, frise 3 horizons | Aucune suggestion LLM n'atteint un export sans validation humaine |

**Track contenu, mené en parallèle et indépendamment** : enrichissement progressif des `frameworks/*.yaml` (aujourd'hui à 4 exigences chacun), alimenté au fil des missions réelles plutôt qu'en amont.

---

## 6bis. Angles morts identifiés avant démarrage (28/07/2026)

Points absents du plan initial, trouvés lors du contrôle final. Le F13 est **bloquant immédiat**.

### F13 — ⚠️ BLOQUANT : les données clients peuvent partir dans l'historique git

**Fait vérifié** : `projects/` (qui contient `projects/cassiopé/project.json`, données de mission réelles) n'est **ni suivi par git, ni présent dans `.gitignore`** — il est simplement *untracked*. Les deux issues sont mauvaises :

| Commande courante | Conséquence |
|---|---|
| `git add -A` + commit + push | Les données d'audit client (vulnérabilités, faiblesses de configuration, noms des personnes interrogées) entrent dans **l'historique git de façon permanente**. Le dépôt jumeau RED SHIELD est déjà publié sur GitHub. |
| `git clean -fdx` | **Suppression de toutes les missions**, sans sauvegarde (cf. F14). |

Le risque est immédiat : le plan de build prévoit **un commit par tâche**.

**Correctif retenu (à appliquer avant la tâche 1)** : sortir les données du dépôt — répertoire configurable `GREENSHIELD_DATA_DIR`, par défaut `%APPDATA%\GreenShield\projects` (Windows) / `~/.local/share/greenshield/projects` (Linux) — **et** ajouter `projects/` au `.gitignore` en double sécurité. Bénéfice collatéral : une mise à jour ou une réinstallation de l'application ne peut plus effacer les missions.

### F14 — Aucune sauvegarde ni export/import de mission

Point unique de défaillance : toutes les missions vivent dans un seul répertoire local, sans mécanisme de sauvegarde ni de portabilité entre postes. Incohérent pour un outil qui vend du PCA/PRA aux clients — le RPO du consultant lui-même est infini.

**Correctif** : export d'une mission en archive unique (`project.json` + `evidence/` + `reports/`), import symétrique. Sert aussi à la remise des données au client en fin de mission (exigence Hermes de transfert).

### F15 — Aucun chiffrement des données clients au repos

Les fichiers `project.json` stockent en clair les vulnérabilités et faiblesses de configuration des clients. Un portable volé = **violation de données affectant les clients**, avec obligation de notification. Le gabarit AIPD du code promet d'ailleurs déjà un « chiffrement AES du disque local » que l'application n'assure pas elle-même.

**Correctif minimal** : documenter BitLocker (Windows) / LUKS (Linux) comme **prérequis d'exploitation**, pas comme option. Complément : chiffrer l'archive d'export (F14), qui est le vecteur le plus exposé.

### F16 — Pas de jeu de données de démonstration anonymisé

L'audit valide l'usage « démonstration commerciale / portfolio ». Démontrer l'outil avec une mission réelle est un manquement à la confidentialité.

**Correctif** : un projet d'exemple **fictif**, explicitement marqué `DEMO`, distinct des missions réelles.

### F17 — Obligations RGPD du consultant sur ses propres traitements

Les grilles d'entretien (§13.2 du spec) collectent nom, fonction et déclarations de personnes physiques : Dorian est **responsable de traitement** pour ces données.

**Correctif** : durée de conservation définie par mission + suppression/restitution en fin de mission (souvent une obligation contractuelle). Cohérent avec le fait de vendre du registre Art. 30 aux clients.

### F18 — Aucun fichier LICENSE

RED SHIELD porte une licence PolyForm Noncommercial ; GREEN SHIELD n'en a aucune. À trancher **avant toute diffusion**, en lien avec F3 (copyright ISO).

### F19 — Temps passé / budget consommé non suivis

Hermes liste « charges consommées vs budget » parmi les indicateurs à reporter dès le démarrage d'une mission. Absent du plan, alors que la donnée alimente à la fois le pilotage client et la facturation du consultant.

**Correctif** : compteur de temps simple par mission/phase, alimentant le tableau de bord (§10.6) et le calcul de ROSI.

---

## 7. Règles permanentes issues de cet audit

À respecter pendant tout le build, pour que les frictions ci-dessus ne se reproduisent pas :

1. **Aucune dépendance native obligatoire pour le développement local** (F6) — si une brique ne s'installe pas sur Windows en une commande, elle vit dans Docker ou n'existe pas.
2. **Tout composant générique réutilisé ailleurs est testé avant d'être branché** (F8).
3. **Toute écriture dans `project.json` est atomique** (F9).
4. **Le LLM n'écrit jamais dans un champ de données** (F11).
5. **Aucune affirmation de différenciation sans vérification du concurrent le plus proche** (F1) — l'erreur commise dans le §10.1 initial du spec.
6. **Un jalon sans critère de sortie testable n'est pas un jalon** (F7).
7. **Le contenu métier se mesure et se planifie séparément du code** (F2).
8. **Aucune donnée client ne réside dans le dépôt git** (F13) — vérifier `git status` avant chaque commit.
9. **Toute donnée client est chiffrée au repos** (F15) — chiffrement de disque activé, prérequis non négociable.
10. **Aucune démonstration sur une mission réelle** (F16) — le jeu `DEMO` existe pour ça.
