<div align="center">

# 🛡️ AuditCraft GRC

**Plateforme locale d'audit de conformité hybride — technique × normatif.**

Analyse hors-ligne de configurations · Policy-as-Code (ISO 27001 / RGPD) · rapport COMEX.

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

</div>

---

## Le principe

AuditCraft GRC confronte la **configuration réelle** d'un système à un **référentiel
de conformité** externalisé (Policy-as-Code), et traduit chaque écart technique en
**impact normatif** (ISO 27001, RGPD) et en **risque EBIOS RM** — puis produit un
rapport prêt pour un COMEX.

- **100 % hors-ligne** : aucun scan réseau, aucune connexion SSH. Uniquement du
  *offline parsing* de fichiers, montés en **lecture seule**.
- **Policy-as-Code** : les règles vivent dans `grc_rules.yaml`, éditable sans toucher au code.
- **Zero-friction** : `make up`, et c'est en ligne.

## Architecture

```
┌──────────────────┐        volume :ro        ┌──────────────────────┐
│   target_lab     │  ───────────────────────▶│    auditor_app       │
│ (cible Linux)    │   sshd_config / nginx.conf│ Streamlit + moteurs  │
│ configs vulnér.  │      (lecture seule)      │ parser · engine · rep│
└──────────────────┘                           └──────────┬───────────┘
                                                           │  :8501
                                                     Tableau de bord
```

Deux conteneurs orchestrés par `docker-compose.yml`. L'auditeur n'a **aucun accès en
écriture** à la cible et **aucun canal réseau** vers elle.

## Démarrage

```bash
make up      # construit et lance  ->  http://localhost:8501
make logs    # suit les logs
make down    # arrête
make clean   # nettoie tout (volumes + images)
```

> Sans `make` : `docker compose up --build -d`.

## Les 3 moteurs

| Fichier | Rôle |
|---|---|
| `auditor/parser.py` | Extraction regex robuste des directives (tolérante aux erreurs de syntaxe). |
| `auditor/grc_rules.yaml` + `auditor/engine.py` | Le « cerveau » : référentiel Policy-as-Code + évaluation. |
| `auditor/reporter.py` | Rapport Markdown COMEX (Executive Summary, score, PAA). |

## Étendre le référentiel

Ajouter une règle = ajouter un bloc dans `grc_rules.yaml`. Opérateurs disponibles :
`must_equal`, `must_not_equal`, `must_not_contain`. Aucune modification de code requise.

---

*PoC — DP Cyber Consulting. Fichiers cibles volontairement vulnérables : ne pas déployer en production.*
