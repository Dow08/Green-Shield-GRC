# TODO — GREEN SHIELD

Tâches connues et non fictives : chaque ligne cite sa source (friction identifiée dans [docs/audit-critique-plan.md](docs/audit-critique-plan.md) §6bis, ou constat direct de session). Rien n'est inventé — cocher au fur et à mesure, ajouter la date de complétion dans [TRACKING.md](TRACKING.md).

## Hygiène immédiate

- [x] **Committer le travail en cours** — fait le 28/07/2026, poussé sur [github.com/Dow08/Green-Shield-GRC](https://github.com/Dow08/Green-Shield-GRC) (branche `main`, commit `d4b4e0d`).
- [x] **README.md** — mis à jour le 29/07/2026 : table des modules corrigée (les 4 modules sont actifs), section Documentation complétée, section Tests ajoutée.

## Identité visuelle

- [x] **Logo** — le logo bouclier + arbre de vie (`ChatGPT Image 28 juil. 2026, 10_50_25.png`, à la racine du dépôt) est intégré le 29/07/2026 : `web/public/logo.png` (version 256px optimisée), utilisé dans la pastille de la sidebar (`Sidebar.tsx`) et en favicon (`index.html`).
- [x] **Maquettes de rapports** livrées le 29/07/2026 : `api/modules/charte.py` porte l'identité visuelle (logo embarqué en base64 pour rester lisible hors ligne, en-tête marque/client/référence, bandeau de confidentialité, pied avec empreinte SHA-256, feuille de style d'impression). Appliquée aux 5 livrables Markdown et au gabarit Word, qui affiche désormais le logo et la marque en page de garde.

## Frictions non résolues de l'audit critique (§6bis)

- [x] **F14 — Export/Import d'une mission** livré le 29/07/2026 : archive ZIP chiffrée AES-256 (`api/modules/archive.py`), routes `POST /api/projects/{id}/archive` et `POST /api/projects/import-archive`, panneau `ArchivePanel.tsx`. Couvre aussi le reste de **F15** (chiffrement du vecteur le plus exposé). Import durci contre le Zip Slip, la bombe de décompression et les archives malformées.
- [x] **F15 — Chiffrement au repos documenté** le 29/07/2026 : section « Prérequis d'exploitation (non négociables) » en tête de [README.md](README.md), avec les commandes de vérification (`manage-bde -status` / `lsblk -f`). Reste à faire une fois F14 livré : **chiffrer l'archive d'export**, qui est le vecteur le plus exposé.
- [x] **F16 — Jeu de démonstration** livré le 29/07/2026 : bouton « Mission de démo » dans le registre, `POST /api/projects/demo`. Mission entièrement fictive (« Cabinet Fictif SAS »), marquée `is_demo`, garnie de temps consommé et d'une configuration SSH volontairement vulnérable pour que le scan technique ait de quoi montrer.
- [x] **F17 — Conservation et purge des données personnelles** livré le 29/07/2026 : `schema_version` 4 (`socle.rgpd_consultant`), `api/modules/retention.py`, routes de politique / purge / échéances, panneau `RgpdPanel.tsx`. Le délai court depuis la **fin** de mission. La purge efface les personnes interrogées mais **jamais les constats d'audit** (minimisation, pas destruction) et prend un instantané de secours avant.
- [x] **F18 — Licence** tranchée le 29/07/2026 : **PolyForm Noncommercial 1.0.0** (cohérence avec RED SHIELD), texte canonique récupéré depuis le dépôt officiel PolyForm et vérifié mot pour mot. Annoncée dans le README avec un tableau des usages autorisés. **F3 vérifié au passage** : les référentiels ne contiennent que des identifiants et intitulés courts reformulés (132 caractères au plus), jamais de texte normatif ISO.
- [x] **F19 — Temps consommé suivi** le 29/07/2026 : `schema_version` 3 (`socle.temps.entrees`), routes `POST/DELETE /api/projects/{id}/temps`, composant `TempsPanel.tsx` affichant total, ventilation par phase et comparaison au budget vendu. Complété le 29/07/2026 : cumul du portefeuille affiché sur le tableau de bord du registre, et tableau « charges consommées vs budget vendu » ajouté au rapport d'audit exporté.

## Frictions traitées hors §6bis

- [x] **F9 — Historique versionné** livré le 29/07/2026 : instantané automatique de `project.json` à chaque validation de phase (`api/modules/snapshots.py`), liste et restauration depuis l'interface, état courant sauvegardé avant tout écrasement, historique embarqué dans l'archive chiffrée. Répond à l'exigence Hermes « tout livrable est daté et versionné ».

## Constats ouverts (découverts en session)

- [x] **Migration legacy rendue unique** le 29/07/2026 : marqueur `.legacy-migre` posé dans le répertoire de destination, et suppression du dossier `GREEN SHIELD/projects/` (le projet de test « cassiopé » qu'il contenait n'était pas une vraie mission cliente). Sans ce marqueur, pointer `GREENSHIELD_DATA_DIR` vers un répertoire de test y recopiait les missions à chaque démarrage — et une mission volontairement supprimée réapparaissait au redémarrage suivant.
- [x] **`bcp_strategy` (RTO/RPO) exposé** le 29/07/2026 : trois champs éditables en Phase 5 (RTO, RPO, politique de sauvegarde), sous l'intitulé « Cibles de continuité (reprises dans le livrable PSSI / PRI) ». Le consultant exportait jusque-là des cibles temporelles qu'il n'avait jamais vues ni validées.
- [x] **Bundle découpé** le 29/07/2026 : `React.lazy()` sur les 5 modules, l'accueil restant chargé d'emblée. Le fichier initial passe de 471 kB / 134 kB gzip à **329 kB / 105 kB gzip** ; le registre de missions (119 kB) n'est plus téléchargé qu'à son ouverture.
- [x] **Coquille applicative responsive** le 29/07/2026 : barre latérale en tiroir sous le point de rupture `md` (voile, fermeture au clic extérieur et à Échap, navigation qui referme), bouton hamburger, marges et coins arrondis retirés sur petit écran. Vérifié à 375 / 768 / 1280 px, sans débordement horizontal.

## Track contenu (mené en parallèle du code, indépendamment)

- [~] **Référentiels YAML sous-dimensionnés** (F2) — `api/frameworks/*.yaml` ne couvrent qu'une fraction des exigences réelles (ISO 27001 Annexe A = 93 contrôles). **Volontairement laissé ouvert** : l'audit prescrit d'enrichir au fil des missions réelles, pas en amont (F2), et générer en masse 93 intitulés reviendrait à inventer du contenu métier — exactement ce que la philosophie « zéro invention » interdit — tout en frôlant la limite de F3 (copyright ISO). Le taux de couverture technique désormais affiché rend d'ailleurs cette incomplétude visible plutôt que masquée.

  **Ce qui a été livré le 29/07/2026, en revanche : le moyen d'enrichir.** La route `POST /api/frameworks/import` existait depuis le début sans qu'aucune interface ne l'appelle — le consultant n'avait donc aucun moyen d'ajouter une exigence sans éditer un YAML à la main, ce qui rendait la consigne « enrichir au fil des missions » inapplicable. `ReferentielsPanel.tsx` (Réglages) permet désormais de créer et d'enrichir des référentiels personnels, avec l'inventaire des exigences par référentiel et un rappel de F3 en évidence. Le contenu métier, lui, reste à saisir par le consultant à partir de la norme qu'il possède.
- [x] **F10 — Taux de couverture technique affiché** le 29/07/2026 : `api/modules/couverture.py` rapproche chaque contrôle organisationnel des règles techniques qui l'appuient (correspondance sur la référence de clause, `A.8.2` ne pouvant être confondue avec `A.8.20`). Le taux réel est affiché en Phase 4 **et** dans le rapport exporté, avec la mention explicite que le reste repose sur du déclaratif. L'audit note que l'afficher est à la fois plus honnête et différenciant.

## Jalon 2 — décisions méthodologiques du spec (§14)

- [x] **§14.1bis — Ratio ANSSI + scission TPRM par volet** livré le 29/07/2026 : `api/modules/tprm.py`. Volet Consulting au ratio `(dépendance × pénétration) / (maturité × confiance)` ; volet GRC sans aucun score, avec quatre exigences DORA/NIS2 vérifiables. `schema_version` 5 étiquette les tiers existants sans jamais recalculer leur note — le passage au ratio est une action explicite précédée d'un instantané. La formule dupliquée côté frontend est supprimée : le serveur seul note.
- [x] **§14.2.1 — 5 obligations organisationnelles de l'AIPD** livré le 29/07/2026 : `api/modules/aipd.py`, `schema_version` 6. La consultation préalable de la CNIL (Art. 36) reste conditionnelle au risque résiduel, qualifié par le consultant et jamais déduit. Le livrable affiche les manques.
- [x] **§14.2.4 — Mappings de contrôles techniques** livré le 29/07/2026 : `api/modules/controles_techniques.py`. Quatre pratiques rattachées à CIS v8 / NIST CSF 2.0, badges à l'écran, section dédiée au rapport d'audit. Au passage : `logging_active` comptait 5 % de la progression sans qu'aucun écran ne permette de le cocher — case ajoutée en Phase 5.

## Reste du plan de build (docs/audit-critique-plan.md §6)

Non entamé — évolutions fonctionnelles majeures, pas des correctifs :

- [x] **§14.2.3 — Volet stratégique de la remédiation ANSSI** livré le 30/07/2026 : `schema_version` 7, trois champs en Phase 5 (urgence de redémarrage, coûts/risques d'un redémarrage précipité, décision retenue et autorité), repris dans le rapport de mission (chapitre Résilience) et le PSSI/PRI (Word, HTML, Markdown).
- [x] **§14.2.5 — NIST CSF comme 6ᵉ parcours** livré le 30/07/2026 : `api/frameworks/nist_csf.yaml`, sélectionnable au même titre qu'ISO 27001/DORA/NIS2/EU AI Act. Le blocage du même jour (« aucune matière source dans ce dépôt ») était une erreur de contexte : la matière (`references/nist-csf.md`, script de scoring `scoring_maturite_nist_csf.py`) existe dans le skill `grc-agent-hermes` de l'utilisateur (`C:\Users\Dow\Desktop\Mes prompts\Dossier MCP\grc-agent-hermes`), simplement absente de ce dépôt-ci. 5 exigences représentatives (une par fonction GV/ID/PR/DE/RC), à l'image des 4 exigences des autres référentiels — pas les 106 sous-catégories complètes (même logique F2 : enrichir au fil des missions). Le radar de maturité visuel évoqué au Jalon 5 reste hors périmètre de cette tâche.
- [ ] **§14.3 — Glossaire des 25 concepts en aide contextuelle** — **bloqué le 30/07/2026** : l'intention est bien dans REFERENTIEL.md, mais le glossaire lui-même (25 définitions sourcées EUR-Lex/cyber.gouv.fr/CNIL/ANSSI/NIST) n'existe dans aucun fichier de ce dépôt — seule son intention est décrite. Rédiger 25 définitions réglementaires de mémoire serait une invention de contenu. Nécessite le glossaire source avant de brancher le module d'aide contextuelle.
- [~] **Jalons 3 à 5** — revue GRC senior du 31/07/2026, plan détaillé écrit dans `C:\Users\Dow\.claude\plans\parsed-percolating-sifakis.md` (hors dépôt, à relire en premier si le fichier existe encore). État au 31/07/2026 :
  - **Déjà couvert** (pas de nouveau code nécessaire) : EU AI Act sélectionnable comme référentiel générique (comme NIST CSF), Copilote LLM déjà contraint (F11) et déjà disponible par mission ET transverse, registre des violations (Lot C), alertes d'échéances, catalogue de mesures.
  - **Explicitement hors scope** (décision du spec lui-même) : approfondissement du contenu NIS2/DORA (track contenu, pas une tâche de code), connecteurs SIEM/EDR/cloud **live** (v2, explicitement différé par le spec).
  - **[x] Lot D — Multi-référentiel par mission GRC**, livré le 31/07/2026 : une mission peut porter plusieurs référentiels actifs (`schema_version` 12, `manual_controls[].referentiel_id`, sélection multiple à la création, regroupement par référentiel en Phase 5, colonne « Référentiel » dans les 3 exports). Nécessaire car le Lot E ci-dessous supposait à tort que le multi-référentiel existait déjà. 610 tests backend / 150 frontend.
  - **[ ] Lot E — Bibliothèque de preuves multi-référentiels** (prochain) : `steps.evaluation.preuves`, nouveau module `api/modules/preuves.py`, `PreuveLibraryPanel.tsx` en Phase 5, colonne « Preuve(s) associée(s) » dans les exports. Détail complet dans le fichier de plan cité ci-dessus.
  - **[ ] Lot F — Vérification croisée des référentiels** (dépend du Lot E) : bouton « Vérifier les référentiels », suggestions de réutilisation de preuve par similarité de titre (`difflib`), jamais de rattachement automatique.
  - **[ ] Lot G — Ingestion SIEM/EDR par dépôt de fichier v1** : brancher le dossier `targets/` déjà créé par mission (jusqu'ici jamais lu), parseur CSV/JSON générique, bouton « Rafraîchir » en Phase 2.
  - **[ ] Lot H — Frise 3 horizons au dashboard** : agrégation court/moyen/long terme tous projets confondus sur `Home.tsx`.
  - Séquence de dépendance : D (fait) → E → F → G → H. Après chaque lot : `py -3 -m pytest api/tests -q` + `npx vitest run && npx tsc --noEmit`, vérification navigateur, régénération de `docs/exemples/` si le rendu change, entrée `TRACKING.md`, commit + push.

## Notes

- Ne pas ajouter de tâche à cette liste sans la relier à une friction sourcée ou à une demande explicite de l'utilisateur — évite de transformer ce fichier en backlog spéculatif (cf. règle CLAUDE.md, F12 de l'audit critique : périmètre piloté par les besoins réels, pas par la spéculation).
- Jalons 2 à 5 du plan de build (`docs/audit-critique-plan.md` §6) restent la référence pour les évolutions fonctionnelles majeures (volet Consulting, NIS2/DORA/RGPD, EU AI Act, Copilote LLM contraint) — ce fichier ne les recopie pas, il ne liste que ce qui est immédiatement actionnable.
