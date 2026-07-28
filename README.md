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
| Registre de missions · Copilote GRC · Collecte technique | Prochaines briques du socle. | 🔜 |

### Ajouter un module

1. `api/modules/<mon_module>/` : le moteur + un `__init__.py` exposant `MODULE` (descripteur) et `run()`.
2. L'enregistrer dans `api/main.py` (registre).
3. Une page dans `web/src/pages/` + une entrée dans le shell.

## Documentation

- [Fiche métier — Consultant en Cybersécurité & GRC](docs/fiche-metier-consultant-grc.md) : contexte fonctionnel (missions, référentiels, fonctions transverses) qui cadre le périmètre GRC couvert par la plateforme et guide les modules à venir (Copilote GRC, Registre de missions).

---

*GREEN SHIELD — DP Cyber Consulting. PoC de démonstration d'expertise cyber / GRC.*
