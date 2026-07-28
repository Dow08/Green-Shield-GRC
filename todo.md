# TODO — GREEN SHIELD

Tâches connues et non fictives : chaque ligne cite sa source (friction identifiée dans [docs/audit-critique-plan.md](docs/audit-critique-plan.md) §6bis, ou constat direct de session). Rien n'est inventé — cocher au fur et à mesure, ajouter la date de complétion dans [TRACKING.md](TRACKING.md).

## Hygiène immédiate

- [ ] **Committer le travail en cours** — 14 fichiers modifiés + ~20 fichiers nouveaux non trackés depuis la session du 28/07/2026 (refonte plateforme, modules Copilote GRC/Collecte technique). Rien n'est commité à ce jour ; réviser `git status` avant de committer (règle CLAUDE.md).
- [ ] **README.md** — la ligne de roadmap (« Registre de missions · Copilote GRC · Collecte technique | 🔜 ») est stale : les 3 modules sont désormais actifs. Mettre à jour la table des modules et la section Documentation.

## Frictions non résolues de l'audit critique (§6bis)

- [ ] **F14 — Export/Import d'une mission.** Aucun mécanisme de sauvegarde ni de portabilité entre postes. Prévu : export d'une mission en archive unique (`project.json` + `evidence/` + `reports/`), import symétrique. Sert aussi à la remise des données au client en fin de mission.
- [ ] **F15 — Chiffrement au repos non documenté.** Les `project.json` stockent en clair les vulnérabilités/faiblesses clients. Documenter BitLocker (Windows) / LUKS (Linux) comme **prérequis d'exploitation non négociable** (README ou docs/), et chiffrer l'archive d'export une fois F14 fait.
- [ ] **F16 — Aucun jeu de démonstration anonymisé.** Démontrer l'outil (portfolio, entretien) exige aujourd'hui d'ouvrir une mission réelle. Créer un projet fictif explicitement marqué `DEMO`, distinct des vraies missions.
- [ ] **F17 — Obligations RGPD du consultant sur ses propres traitements.** Les grilles d'entretien collectent nom/fonction/déclarations de personnes physiques interrogées : Dorian est responsable de traitement pour ces données. Définir une durée de conservation par mission + suppression/restitution en fin de mission.
- [ ] **F18 — Aucun fichier LICENSE.** À trancher avant toute diffusion, en lien avec F3 (copyright ISO 27001 : ne jamais embarquer le texte normatif, seulement identifiants + intitulés courts).
- [ ] **F19 — Temps/budget non suivis.** Le champ `budget` existe déjà dans `schema_migration.py` mais n'est exploité par aucune UI. Ajouter un compteur de temps simple par mission/phase, alimentant le dashboard et le calcul de ROSI.

## Track contenu (mené en parallèle du code, indépendamment)

- [ ] **Référentiels YAML sous-dimensionnés** (F2) — `api/frameworks/*.yaml` ne couvrent qu'une fraction des exigences réelles (ISO 27001 Annexe A = 93 contrôles). Enrichir au fil des missions réelles plutôt qu'en amont, en respectant F3 (identifiants + intitulés courts, jamais le texte normatif).
- [ ] **Couverture technique AuditCraft-GRC limitée** (F10) — `grc_rules.yaml` ne couvre qu'environ 5 contrôles sur 93. L'UI affiche déjà le principe de preuve factuelle ; vérifier que le taux de couverture réel est visible explicitement (« X contrôles sur Y appuyés par une preuve technique »).

## Notes

- Ne pas ajouter de tâche à cette liste sans la relier à une friction sourcée ou à une demande explicite de l'utilisateur — évite de transformer ce fichier en backlog spéculatif (cf. règle CLAUDE.md, F12 de l'audit critique : périmètre piloté par les besoins réels, pas par la spéculation).
- Jalons 2 à 5 du plan de build (`docs/audit-critique-plan.md` §6) restent la référence pour les évolutions fonctionnelles majeures (volet Consulting, NIS2/DORA/RGPD, EU AI Act, Copilote LLM contraint) — ce fichier ne les recopie pas, il ne liste que ce qui est immédiatement actionnable.
