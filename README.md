<div align="center">

# 🟢 GREEN SHIELD

**Plateforme locale d'audit cyber & de conformité — modulaire, hors-ligne, orientée GRC.**

Un projet, décomposé en **modules indépendants** qui partagent une même philosophie :
mesurer factuellement, corréler au normatif, produire un livrable exploitable.

</div>

---

## Philosophie

GREEN SHIELD n'est pas un outil de plus : c'est un **socle d'audit** pensé pour le
conseil (GRC / DevSecOps). Chaque module se déploie seul, se démontre en quelques
secondes, et respecte trois principes :

- **100 % local & hors-ligne** — pas de cloud, pas d'exfiltration ; les données restent sur le poste.
- **Factuel** — aucune donnée inventée : chaque constat est appuyé par une preuve.
- **Technique × Normatif** — chaque écart technique est relié à une exigence (ISO 27001, RGPD, EBIOS RM).

## Modules

| Module | Rôle | État |
|---|---|:---:|
| **[AuditCraft-GRC](AuditCraft-GRC/)** | Audit de conformité par *offline parsing* de configurations + Policy-as-Code + rapport COMEX. | ✅ Livré |
| *(à venir)* | D'autres briques d'audit viendront s'ajouter au socle. | 🔜 |

## Démarrage rapide

Chaque module est autonome et conteneurisé. Exemple :

```bash
cd AuditCraft-GRC
make up          # -> http://localhost:8501
```

Voir le README de chaque module pour le détail.

---

*GREEN SHIELD — DP Cyber Consulting. PoC de démonstration d'expertise cyber / GRC.*
