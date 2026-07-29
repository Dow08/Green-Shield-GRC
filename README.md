<div align="center">

# 🟢 GREEN SHIELD

**Plateforme locale d'audit cyber & de conformité — modulaire, hors-ligne, orientée GRC.**

Un shell moderne (React) qui héberge des **modules** branchés sur un moteur Python (FastAPI).

![React](https://img.shields.io/badge/React-19-61DAFB)
![Vite](https://img.shields.io/badge/Vite-6-646CFF)
![Tailwind](https://img.shields.io/badge/Tailwind-v4-38BDF8)
![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

</div>

---

## Philosophie

GREEN SHIELD est un **socle d'audit** pensé pour le conseil (GRC / DevSecOps). Chaque
capacité est un **module autonome** branché sur une coquille commune :

- **100 % local & hors-ligne** — pas de cloud, pas d'exfiltration.
- **Factuel** — aucune donnée inventée : chaque constat est appuyé par une preuve.
- **Technique × Normatif** — chaque écart est relié à une exigence (ISO 27001, RGPD, EBIOS RM).
- **Portable** — conteneurisé : tourne à l'identique sous **Linux et Windows**.

## Architecture

```
┌────────────┐   /api    ┌──────────────┐   :ro    ┌──────────────┐
│  web       │ ────────▶ │  api          │ ───────▶ │  target_lab   │
│ React/Vite │  (nginx)  │ FastAPI +     │ lecture  │ configs       │
│ shell +    │           │ moteurs des   │ seule    │ vulnérables   │
│ modules    │           │ modules       │          │               │
└─────┬──────┘           └──────────────┘          └──────────────┘
   :8080
```

- **web/** — shell React (nav pilotée par un registre de modules) + design SaaS moderne.
- **api/** — FastAPI ; chaque module expose son moteur (`api/modules/<module>/`).
- **lab_target/** — configurations de la cible (lues en lecture seule).

## ⚠️ Prérequis d'exploitation (non négociables)

GREEN SHIELD manipule des **données client hautement sensibles** : vulnérabilités
relevées, faiblesses de configuration, noms et déclarations des personnes
interrogées. Avant toute utilisation sur une mission réelle :

| Prérequis | Pourquoi | Comment vérifier |
|---|---|---|
| **Chiffrement du disque activé** | Les missions sont stockées en clair dans des fichiers JSON. Un portable volé sans chiffrement = **violation de données** avec obligation de notification aux clients et à la CNIL. | Windows : `manage-bde -status C:` (BitLocker doit être *Protection activée*).<br>Linux : `lsblk -f` (LUKS attendu sur la partition de données). |
| **Accès réseau restreint au loopback** | L'API n'a **aucune authentification** : elle est conçue pour un poste unique. `docker-compose.yml` publie déjà sur `127.0.0.1` uniquement — ne pas retirer cette restriction sans mettre en place une authentification. | `docker compose config \| grep 8080` → doit afficher `127.0.0.1:8080`. |
| **Aucune donnée client dans git** | Les missions vivent hors du dépôt (`GREENSHIELD_DATA_DIR`). | `git status` avant tout commit ; `projects/` est dans `.gitignore` en double sécurité. |

> Ces trois points sont des **conditions d'usage**, pas des recommandations : l'application
> ne peut pas les garantir à votre place. Voir [docs/audit-critique-plan.md](docs/audit-critique-plan.md) (F13, F15).

### Où vivent les données

| Élément | Emplacement (défaut) |
|---|---|
| Missions | Windows `%APPDATA%\GreenShield\projects` · Linux `~/.local/share/greenshield/projects` |
| Journal d'audit | `<racine de données>/logs/audit.log` (rotation automatique, 5 × 1 Mo) |
| Override | Variable d'environnement `GREENSHIELD_DATA_DIR` (cf. [.env.example](.env.example)) |

Le **journal d'audit** trace les actions sensibles (création / modification / suppression
de mission, import de référentiel, export de livrable, appels au Copilote, tentatives
d'accès rejetées). Il enregistre l'action et l'identifiant de la mission concernée,
**jamais le contenu** des missions ni le texte des prompts.

## Démarrage

```bash
make up          # construit et lance  ->  http://localhost:8080
make logs
make down
make clean
```

> Sans `make` (ex. Windows sans make) : `docker compose up --build -d`.

### Développement (hors Docker)

```bash
# Terminal 1 — API
cd api && uvicorn main:app --reload --port 8000
# Terminal 2 — Frontend
cd web && npm install && npm run dev      # http://localhost:5173 (proxifie /api)
```

## Modules

| Module | Rôle | État |
|---|---|:---:|
| **AuditCraft-GRC** | Audit de conformité (offline parsing + Policy-as-Code ISO 27001/RGPD/EBIOS + rapport COMEX). | ✅ Actif |
| **Registre de missions** | Conduite de mission en 6 phases (cadrage, diagnostic RGPD, TPRM, EBIOS RM, résilience E3R, plan de traitement) + génération des livrables Word/Markdown. | ✅ Actif |
| **Copilote GRC** | Synthèse transverse du portefeuille : priorise les constats réels de toutes les missions. Hors-ligne par défaut, en ligne (Gemini) uniquement si le consultant fournit sa clé API. | ✅ Actif |
| **Collecte technique** | Empreinte factuelle d'une configuration (SSH, Nginx, Apache, MySQL, PostgreSQL, Docker Compose, OS) alimentant l'inventaire des Biens Supports. Aucun verdict de conformité. | ✅ Actif |

### Ajouter un module

1. `api/modules/<mon_module>/` : le moteur + un `__init__.py` exposant `MODULE` (descripteur) et `run()`.
2. L'enregistrer dans `api/main.py` (registre).
3. Une page dans `web/src/pages/` + une entrée dans le shell.

## Tests

```bash
py -3 -m pytest api/tests -q                       # backend
cd web && npm run typecheck && npm run lint && npm run test && npm run build   # frontend
```

## Documentation

- [REFERENTIEL.md](REFERENTIEL.md) — spécification technique et guide de reprise (handoff).
- [docs/audit-critique-plan.md](docs/audit-critique-plan.md) — revue adversariale du plan, règles permanentes, frictions identifiées (F1-F19).
- [docs/spec-refonte-grc-consulting.md](docs/spec-refonte-grc-consulting.md) — spécification fonctionnelle détaillée.
- [docs/fiche-metier-consultant-grc.md](docs/fiche-metier-consultant-grc.md) — contexte métier (missions, référentiels, fonctions transverses) qui cadre le périmètre GRC couvert.
- [TRACKING.md](TRACKING.md) — journal de bord des évolutions · [todo.md](todo.md) — tâches connues.
- [CLAUDE.md](CLAUDE.md) — conventions de développement et pièges connus.

---

*GREEN SHIELD — DP Cyber Consulting. PoC de démonstration d'expertise cyber / GRC.*
