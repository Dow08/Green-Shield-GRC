# CLAUDE.md — GREEN SHIELD

Contexte pour toute session Claude Code future sur ce dépôt. Préférences, conventions et pièges déjà rencontrés — à lire avant de coder.

## Le projet

GREEN SHIELD est une plateforme locale, modulaire et souveraine (100 % hors-ligne) d'audit de sécurité et d'accompagnement GRC, pour un consultant cybersécurité solo (Dorian, DP Cyber Consulting). Positionnement assumé : **cockpit de conduite de mission pour consultant externe**, pas une plateforme GRC de plus (cf. [docs/audit-critique-plan.md](docs/audit-critique-plan.md), F1).

**Documents de référence — ne pas dupliquer, lire avant de proposer une évolution structurante :**
- [REFERENTIEL.md](REFERENTIEL.md) — spec technique + guide de handoff, vision d'ensemble
- [docs/spec-refonte-grc-consulting.md](docs/spec-refonte-grc-consulting.md) — spec fonctionnelle détaillée (les 6 phases, TPRM, EBIOS RM, E3R...)
- [docs/audit-critique-plan.md](docs/audit-critique-plan.md) — revue adversariale du spec, plan de build par jalons, **10 règles permanentes** (§7) et frictions non résolues F13-F19 (§6bis)
- [TRACKING.md](TRACKING.md) — journal de bord chronologique des évolutions réalisées
- [todo.md](todo.md) — prochaines tâches connues, à jour

## Stack

- **Frontend** : React 19, Vite 6, Tailwind v4, TypeScript strict, `lucide-react`, `framer-motion`
- **Backend** : FastAPI, Python 3.12+ (dev testé sous 3.14), stdlib autant que possible
- **Data** : fichiers JSON/YAML à plat, aucune base de données
- **Packaging** : Docker Compose (3 services : `web`, `api`, `target_lab`)

## Règles non négociables (héritées de l'audit critique, §7)

1. **Aucune dépendance native obligatoire en local** — si une brique ne s'installe pas sur Windows en une commande, elle vit dans Docker ou n'existe pas (raison du choix `docxtpl` plutôt que WeasyPrint pour le DOCX).
2. **Tout composant générique réutilisé ailleurs est testé avant d'être branché.**
3. **Toute écriture dans `project.json` est atomique** (`_write_json_atomic` dans `api/modules/projects.py` — fichier temporaire + `os.replace`).
4. **Un LLM n'écrit jamais directement dans un champ de données structuré** — le Copilote (mission ou transverse) ne produit que du texte libre affiché à l'écran ; aucune saisie de formulaire n'est auto-remplie par une réponse IA.
5. **Aucune donnée client dans le dépôt git.** Les missions vivent hors du dépôt (`GREENSHIELD_DATA_DIR`, par défaut `%APPDATA%\GreenShield\projects` sous Windows). `projects/` reste dans `.gitignore` en double sécurité. Vérifier `git status` avant tout commit.

## Conventions établies pendant les sessions précédentes

- **Modules backend** : chaque module vit dans `api/modules/<nom>.py` (ou `<nom>/` si plusieurs fichiers, cf. `auditcraft_grc/`), expose un `router = APIRouter(prefix="/api")` et, si présenté dans la nav, un dict `MODULE`. Enregistrement dans `api/main.py` via `app.include_router(...)`.
- **Appels sortants vers un LLM** : point de passage unique `api/modules/ai_gateway.py::call_gemini()`. Ne jamais appeler `urlopen` vers un fournisseur LLM ailleurs. Bascule en ligne/hors-ligne systématique : sans clé API (fournie par l'utilisateur dans Réglages, jamais stockée côté serveur), réponse locale factuelle construite à partir des données réelles ; toute erreur réseau/clé retombe silencieusement sur ce même repli (`source: "offline" | "online" | "offline_fallback"`).
- **Tests** : pytest colocalisé dans `api/tests/` (un fichier par module) ; vitest colocalisé en `*.test.tsx` à côté du composant testé (pas de dossier `__tests__` séparé, exception faite de `web/src/test/setup.ts`). Commandes :
  ```bash
  cd api && py -3 -m pytest api/tests -q
  cd web && npx vitest run && npx tsc --noEmit
  ```
- **Langue** : code et UI en français (commentaires, messages, noms de champs métier). Identifiants techniques (variables, fonctions) en anglais/français mixte selon l'existant — suivre le fichier édité.
- **Commentaires** : uniquement quand le POURQUOI n'est pas évident (contrainte cachée, contournement, décision d'architecture) — jamais pour décrire ce que fait le code.
- **Git** : ne jamais committer sans demande explicite de l'utilisateur. Toujours `git status` avant un commit pour repérer un fichier suspect avant de l'ajouter.

## Conventions frontend (adaptées d'un gabarit générique React/Next.js)

Un gabarit générique "Universal Instructions for React/Next.js" a été passé en revue le 28/07/2026. La majorité ne s'applique pas ici — **à écarter explicitement**, pour qu'une session future n'essaie pas de "corriger" le stack vers ça :

- **Pas de Next.js.** Le choix Vite est assumé (outil 100 % client, pas de SEO, pas de SSR/auth/DB côté framework — cf. §2 du gabarit, critères qui pointent tous vers React+Vite ici). Aucune section Next.js (App Router, Server Components, `"use client"`, Server Actions) ne s'applique.
- **Pas de `shadcn/ui`.** Le projet a son propre design system CSS (variables `--g1`/`--g3`/`--stroke`/`--bg2`/`--soft`/`--faint`..., classes utilitaires `glass`, `glass-2`, `tile`/`tile-*`) déjà cohérent sur toutes les pages. Ne pas introduire shadcn ni un autre kit UI par-dessus — adapter les primitives existantes (`Sidebar.tsx`, boutons/inputs inline stylés) plutôt que copier une nouvelle bibliothèque.
- **Pas d'architecture FSD** (`app/views/widgets/features/entities/shared`). La structure actuelle (`web/src/{pages,components,lib,types}`) suffit à la taille du projet ; ne pas la réorganiser sans besoin réel.

Ce qui est **réellement transposable** et à appliquer :

- **TypeScript strict** déjà actif (`tsconfig.json`, `strict: true`) — le garder. Pas de `as any` sauf cas isolé documenté ; les tests mockant `fetch` (`global.fetch = ... as any`) sont l'exception tolérée (interop avec l'API DOM native), pas un précédent pour le reste du code.
- **Validation runtime des données externes** : aujourd'hui absente côté frontend (les réponses API sont consommées telles quelles, cf. `lib/api.ts`). Le backend valide déjà ses propres entrées (`path_safety.py`, migrations `schema_migration.py`) ; si un champ de réponse API devient incertain, valider côté client plutôt que supposer la forme.
- **Cycle de vie complet d'un nouveau champ** (§9 du gabarit, très aligné avec l'existant) : type TypeScript (`types.ts`) → défauts (`create_default_state` côté backend) → migration (`schema_migration.py`) → UI (lecture + édition) → export/import → cas limites. Ne jamais ajouter un champ seulement côté UI.
- **Overlays/dropdowns** (sélecteurs de modèles dans `Projects.tsx`, menus déroulants) : fermeture au `Escape` et au clic extérieur, `z-index` explicite, `max-height` + `overflow-y-auto` sur les listes longues — à vérifier si un nouveau menu est ajouté.
- **Tailwind v4 spécifiquement** (`web/package.json`, `^4.0.0`) : la syntaxe diffère de v3 sur plusieurs points (config CSS-first, certaines classes de wrap/overflow renommées). Avant d'utiliser une classe potentiellement version-dépendante, vérifier qu'elle existe en v4 plutôt que de la recopier d'un exemple v3.
  - **Piège vérifié le 29/07/2026** (tiroir de navigation mobile) : `translate-x-0` **ne reprend pas la main** sur `-translate-x-full` — en v4 ces utilitaires écrivent la propriété CSS `translate` (et non `transform`), et le calcul restait bloqué à `translate: -100%` alors que le DOM portait bien la classe `translate-x-0`. Le décalage arbitraire négatif `-left-[76px]` n'était pas généré non plus (`left-[-76px]` non plus). Solution retenue : bascule `hidden`/`flex`, utilitaires de base, aucune valeur arbitraire. **Toujours vérifier dans le navigateur** qu'une classe de positionnement produit l'effet attendu — la classe peut être présente dans le DOM sans que le style calculé suive.
- **localStorage** : utilisé sans `try/catch` aujourd'hui (`Settings.tsx`, `Projects.tsx` pour la clé Copilote). Pas bloquant pour un outil mono-poste, mais toute nouvelle lecture/écriture devrait être protégée (mode privé, quota dépassé) plutôt que de casser l'écran.
- **Une seule source de vérité par opération de domaine** : point de vigilance concret déjà identifié — l'ajout d'un Bien Support existe par **deux chemins différents** (formulaire manuel de la Phase 1 dans `Projects.tsx`, génération d'id `"BS-" + random`) et l'import depuis Collecte technique (`collecte_technique.py::_next_bs_id`, génération séquentielle). Les deux écrivent dans le même `steps.cadrage.assets_support`, avec deux logiques d'id différentes qui peuvent un jour se percuter. À unifier si un troisième point d'entrée apparaît.
- **Accessibilité de base** : `aria-label` sur les boutons icône-seule (déjà fait dans `Sidebar.tsx` — garder ce réflexe sur toute nouvelle icône cliquable), navigation clavier, focus visible.
- **États de chargement/vide/erreur** : déjà globalement suivis (`CopilotGRC.tsx` a un état de chargement explicite, `Projects.tsx` gère "aucun fichier déposé") — maintenir ce standard sur toute nouvelle vue pilotée par l'API.
- **Pas d'ESLint configuré actuellement** (aucun `eslint.config.*`, aucune dépendance) — ne pas prétendre qu'un `npm run lint` existe. Les checks réels du projet restent `npx tsc --noEmit` et `npx vitest run` (déjà documentés ci-dessus).
- **Tester le contenu réaliste avant de livrer une UI** (§27 du gabarit) : nom de mission très long sans espace, client vide, liste de tiers TPRM longue, etc. — cohérent avec la philosophie "n'invente rien / ne casse rien" déjà en place sur les tests (`PhaseKanban.test.tsx`).

## Piège Windows connu

`uvicorn --reload` sur Windows spawne un process `multiprocessing` enfant (visible via `Get-CimInstance Win32_Process -Filter "Name='python.exe'"`, colonne `CommandLine` contenant `spawn_main(parent_pid=...)`). Tuer uniquement le PID du reloader **n'arrête pas cet enfant** : il reste orphelin, garde le port lié et sert l'ancien code en mémoire — symptôme typique : les nouvelles routes renvoient `404 Not Found` alors que `/health` répond normalement. Toujours identifier et tuer l'arbre complet des process `python.exe` liés avant de relancer.

## Philosophie produit (à ne jamais casser)

- **Factuel** : aucune donnée inventée, chaque constat s'appuie sur une preuve (fichier, ligne, valeur relevée).
- **100 % local / hors-ligne par défaut** : toute capacité réseau (Copilote en ligne) est strictement opt-in via une clé API saisie par le consultant.
- **Rôles de module strictement séparés** : AuditCraft-GRC juge la conformité, EBIOS RM évalue le risque, Collecte technique fait de l'inventaire (aucun verdict). Ne pas mélanger ces responsabilités dans un futur module.
