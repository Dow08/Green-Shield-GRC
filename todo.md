# TODO — GREEN SHIELD

Tâches connues et non fictives : chaque ligne cite sa source (friction identifiée dans [docs/audit-critique-plan.md](docs/audit-critique-plan.md) §6bis, ou constat direct de session). Rien n'est inventé — cocher au fur et à mesure, ajouter la date de complétion dans [TRACKING.md](TRACKING.md).

## Hygiène immédiate

- [x] **Committer le travail en cours** — fait le 28/07/2026, poussé sur [github.com/Dow08/Green-Shield-GRC](https://github.com/Dow08/Green-Shield-GRC) (branche `main`, commit `d4b4e0d`).
- [x] **README.md** — mis à jour le 29/07/2026 : table des modules corrigée (les 4 modules sont actifs), section Documentation complétée, section Tests ajoutée.

## Identité visuelle

- [x] **Logo** — le logo bouclier + arbre de vie (`ChatGPT Image 28 juil. 2026, 10_50_25.png`, à la racine du dépôt) est intégré le 29/07/2026 : `web/public/logo.png` (version 256px optimisée), utilisé dans la pastille de la sidebar (`Sidebar.tsx`) et en favicon (`index.html`).
- [ ] **Maquettes de rapports** — réaliser des maquettes stylisées et adaptées à l'identité visuelle (logo bouclier/arbre de vie) pour les documents exportés (NDA, Analyse EBIOS RM, PSSI/PRI, AIPD, Rapport GRC complet, rapport Word `.docx`). Aujourd'hui ces documents utilisent une feuille de style CSS d'impression générique (`pdf_style` dans `api/modules/projects.py`) et un gabarit Word neutre (`api/templates/rapport_iso27001.docx`) — aucun n'intègre le logo ni une charte graphique dédiée. Rappel posé le 29/07/2026, à la demande explicite du consultant — pas encore réalisé.

## Frictions non résolues de l'audit critique (§6bis)

- [x] **F14 — Export/Import d'une mission** livré le 29/07/2026 : archive ZIP chiffrée AES-256 (`api/modules/archive.py`), routes `POST /api/projects/{id}/archive` et `POST /api/projects/import-archive`, panneau `ArchivePanel.tsx`. Couvre aussi le reste de **F15** (chiffrement du vecteur le plus exposé). Import durci contre le Zip Slip, la bombe de décompression et les archives malformées.
- [x] **F15 — Chiffrement au repos documenté** le 29/07/2026 : section « Prérequis d'exploitation (non négociables) » en tête de [README.md](README.md), avec les commandes de vérification (`manage-bde -status` / `lsblk -f`). Reste à faire une fois F14 livré : **chiffrer l'archive d'export**, qui est le vecteur le plus exposé.
- [ ] **F16 — Aucun jeu de démonstration anonymisé.** Démontrer l'outil (portfolio, entretien) exige aujourd'hui d'ouvrir une mission réelle. Créer un projet fictif explicitement marqué `DEMO`, distinct des vraies missions.
- [ ] **F17 — Obligations RGPD du consultant sur ses propres traitements.** Les grilles d'entretien collectent nom/fonction/déclarations de personnes physiques interrogées : Dorian est responsable de traitement pour ces données. Définir une durée de conservation par mission + suppression/restitution en fin de mission.
- [ ] **F18 — Aucun fichier LICENSE.** À trancher avant toute diffusion, en lien avec F3 (copyright ISO 27001 : ne jamais embarquer le texte normatif, seulement identifiants + intitulés courts).
- [x] **F19 — Temps consommé suivi** le 29/07/2026 : `schema_version` 3 (`socle.temps.entrees`), routes `POST/DELETE /api/projects/{id}/temps`, composant `TempsPanel.tsx` affichant total, ventilation par phase et comparaison au budget vendu. Reste ouvert : exposer le cumul dans le **tableau de bord d'accueil** et dans les **exports** (aujourd'hui visible uniquement dans la vue mission).

## Constats ouverts (découverts en session)

- [x] **Migration legacy rendue unique** le 29/07/2026 : marqueur `.legacy-migre` posé dans le répertoire de destination, et suppression du dossier `GREEN SHIELD/projects/` (le projet de test « cassiopé » qu'il contenait n'était pas une vraie mission cliente). Sans ce marqueur, pointer `GREENSHIELD_DATA_DIR` vers un répertoire de test y recopiait les missions à chaque démarrage — et une mission volontairement supprimée réapparaissait au redémarrage suivant.
- [ ] **Bundle JS monolithique** (449 kB / 129 kB gzip, aucun code-splitting). Non bloquant au volume actuel, pertinent surtout pour l'usage tablette. `React.lazy()` sur les 4 pages principales.
- [x] **Coquille applicative responsive** le 29/07/2026 : barre latérale en tiroir sous le point de rupture `md` (voile, fermeture au clic extérieur et à Échap, navigation qui referme), bouton hamburger, marges et coins arrondis retirés sur petit écran. Vérifié à 375 / 768 / 1280 px, sans débordement horizontal.

## Track contenu (mené en parallèle du code, indépendamment)

- [ ] **Référentiels YAML sous-dimensionnés** (F2) — `api/frameworks/*.yaml` ne couvrent qu'une fraction des exigences réelles (ISO 27001 Annexe A = 93 contrôles). Enrichir au fil des missions réelles plutôt qu'en amont, en respectant F3 (identifiants + intitulés courts, jamais le texte normatif).
- [ ] **Couverture technique AuditCraft-GRC limitée** (F10) — `grc_rules.yaml` ne couvre qu'environ 5 contrôles sur 93. L'UI affiche déjà le principe de preuve factuelle ; vérifier que le taux de couverture réel est visible explicitement (« X contrôles sur Y appuyés par une preuve technique »).

## Notes

- Ne pas ajouter de tâche à cette liste sans la relier à une friction sourcée ou à une demande explicite de l'utilisateur — évite de transformer ce fichier en backlog spéculatif (cf. règle CLAUDE.md, F12 de l'audit critique : périmètre piloté par les besoins réels, pas par la spéculation).
- Jalons 2 à 5 du plan de build (`docs/audit-critique-plan.md` §6) restent la référence pour les évolutions fonctionnelles majeures (volet Consulting, NIS2/DORA/RGPD, EU AI Act, Copilote LLM contraint) — ce fichier ne les recopie pas, il ne liste que ce qui est immédiatement actionnable.
