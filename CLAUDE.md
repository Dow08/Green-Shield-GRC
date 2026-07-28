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

## Piège Windows connu

`uvicorn --reload` sur Windows spawne un process `multiprocessing` enfant (visible via `Get-CimInstance Win32_Process -Filter "Name='python.exe'"`, colonne `CommandLine` contenant `spawn_main(parent_pid=...)`). Tuer uniquement le PID du reloader **n'arrête pas cet enfant** : il reste orphelin, garde le port lié et sert l'ancien code en mémoire — symptôme typique : les nouvelles routes renvoient `404 Not Found` alors que `/health` répond normalement. Toujours identifier et tuer l'arbre complet des process `python.exe` liés avant de relancer.

## Philosophie produit (à ne jamais casser)

- **Factuel** : aucune donnée inventée, chaque constat s'appuie sur une preuve (fichier, ligne, valeur relevée).
- **100 % local / hors-ligne par défaut** : toute capacité réseau (Copilote en ligne) est strictement opt-in via une clé API saisie par le consultant.
- **Rôles de module strictement séparés** : AuditCraft-GRC juge la conformité, EBIOS RM évalue le risque, Collecte technique fait de l'inventaire (aucun verdict). Ne pas mélanger ces responsabilités dans un futur module.
