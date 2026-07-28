# SPEC — Refonte GRC / Consulting (2 volets d'une même mission)

> **STATUT : CADRAGE VERROUILLÉ le 28/07/2026**, puis **amendé par l'audit critique du même jour**.
> ⚠️ **Lire [audit-critique-plan.md](audit-critique-plan.md) AVANT ce document** : il corrige 12 points de friction, dont 2 critiques (différenciation surestimée, charge de contenu sous-estimée), et remplace le plan de jalons du §12 par un plan corrigé avec un Jalon 0.

> Document de cadrage produit selon la méthodologie "Brainstormer-Planificateur" (Prompt 1).
> Aucune ligne de code n'est écrite avant validation explicite de ce document par Dorian.
> Source des workflows : skill `grc-agent-hermes` (`C:\Users\Dow\Desktop\Cour GRC\`), croisé avec [REFERENTIEL.md](../REFERENTIEL.md) et [fiche-metier-consultant-grc.md](fiche-metier-consultant-grc.md).

---

## 0. Décisions de cadrage actées (brainstorming)

| # | Question | Décision |
|---|---|---|
| 1 | Critère GRC vs Consulting | Ce sont **2 volets d'une même mission**, pas 2 types de projets exclusifs. GRC = contrôle/audit vs une norme ; Consulting = accompagnement/mise en œuvre piloté par EBIOS RM. |
| 2 | Structure projet | **1 projet = 1 client**, avec un **socle commun** + un **volet GRC** et/ou un **volet Consulting** activables indépendamment. Les écarts GRC peuvent alimenter le plan d'action Consulting. |
| 3 | Granularité | **Fidélité stricte** aux workflows Hermes — chaque étape devient une phase/sous-étape de l'appli, même si ça fait 8-10 phases par volet. |
| 4 | Squelette GRC | **Parcours dédié par référentiel** (pas un squelette générique unique). |
| 5 | Couverture référentiels | On construit **les 5 parcours dès maintenant** (ISO27001, NIS2, DORA, RGPD, AIAct) avant de coder — 2 ont un workflow Hermes prêt (ISO27001, NIS2), 3 sont à construire depuis les fiches de référence Hermes + connaissances générales (AIAct, seul cas sans fiche Hermes du tout). |
| 6 | Squelette Consulting | **Fusion complète** des 6 phases onboarding-client-grc.md + des 5 ateliers EBIOS RM — aucune étape sacrifiée (10 macro-phases). |
| 7 | Navigation UI | **Kanban par macro-phase** (colonnes = macro-phases, cartes = sous-étapes/checklists déplaçables). |
| 8 | Lien AuditCraft-GRC | **Branchement automatique** — le scan technique réel (SSH/Nginx, `grc_rules.yaml`) alimente automatiquement les preuves de l'étape "Exécution / Contrôles Annexe A" du parcours ISO27001. |
| 9 | Multi-référentiel | Un projet peut activer **plusieurs référentiels GRC simultanément** (ex : NIS2 + ISO27001 + DORA pour un même client), avec le crosswalk pour éviter la duplication des preuves. |

### Découverte structurante (post-décision 9)

`references/mapping-crosswalk.md` (Hermes) établit que **ISO 27001 est le socle pivot** :
- ISO 27001 couvre ~80% de NIS2, ~70% de DORA, ~75% de RGPD (sécurité), 100% du socle NIST CSF.
- La bonne pratique n'est **pas** de dupliquer un audit complet par référentiel, mais de construire **1 SMSI ISO 27001** et d'ajouter les **compléments spécifiques** (le différentiel de 20-30%) par référentiel additionnel.

→ Ceci **affine** la décision 4/5 : les parcours NIS2/DORA/RGPD ne sont pas des audits ISO27001 réécrits de zéro, mais des **parcours "pivot + compléments"** qui pointent vers le crosswalk pour la partie déjà couverte. Seul **AIAct** (classification de risque IA, pas de socle SMSI classique) reste un parcours totalement autonome.

---

## 1. Principe général

```
PROJET (1 client, 1 mission)
 ├── SOCLE COMMUN (une fois, partagé)
 ├── VOLET GRC (activable, multi-référentiel)
 │    ├── ISO 27001 (pivot)
 │    ├── NIS2 (pivot + compléments)
 │    ├── DORA (pivot + compléments)
 │    ├── RGPD (pivot + compléments)
 │    └── EU AI Act (autonome)
 └── VOLET CONSULTING (activable)
      └── Parcours fusionné onboarding + EBIOS RM (10 phases)
```

---

## 2. Socle commun — "Cadrage de mission"

Fusion des Phases 0-1 de `workflow-onboarding-client-grc.md`. Formulaire one-shot en tête de mission (pas un Kanban), déjà partiellement codé (NDA, patrimoine VM/BS) :

1. **Qualification commerciale** — déclencheur, sponsor exécutif, budget, équipe interne, cible (certification/conformité/échéance).
2. **Contractualisation** — périmètre inclus/exclu, livrables + critères d'acceptation, modalités, accès SI, NDA *(existant)*, RC pro.
3. **Kick-off** — réunion de lancement, gouvernance projet (comités, cadence, reporting).
4. **Cartographie initiale** — organisation (RSSI/DPO/DSI, comités), référentiels existants, réglementations applicables (RGPD systématique, NIS2/DORA si concerné), périmètre technique, patrimoine (valeurs métier / biens supports — *existant*).
5. **Entretiens prioritaires** — check-list des 8-10 parties prenantes à rencontrer (sponsor, RSSI, DPO, DSI, RH, Achats, Juridique, métier, Audit).

---

## 3. Volet GRC

### 3.1 Parcours ISO 27001 (pivot) — 4 macro-phases

Source : `workflow-audit-iso27001.md`.

| Macro-phase | Contenu |
|---|---|
| **1. Préparation** | Cadrer la mission (périmètre exact, référentiels complémentaires 27017/27018/27701), collecter la documentation (PSSI, SoA, plan de traitement, registre risques, procédures, CR comité SMSI, indicateurs, inventaire actifs, audit précédent), construire le programme d'audit (entretiens, observations, échantillons, planning). |
| **2. Exécution** | Réunion d'ouverture ; audit clauses 4 à 10 (entretien + revue documentaire par clause, table RSSI/Direction/RH/DSI) ; **contrôles Annexe A** (93 contrôles, échantillonnage, focus 11 nouveaux contrôles 2022) **avec preuves techniques automatiques via AuditCraft-GRC** pour les contrôles couverts par le scan (A.8.24, A.8.5, A.8.2, A.8.9...) ; observations physiques ; documentation de chaque constat (Conforme / Observation / NC mineure / NC majeure + preuve). |
| **3. Synthèse & restitution** | Analyse croisée (causes racines, scores par thème, Top 10 actions) ; rédaction du rapport (structure 9 sections) ; restitution intermédiaire (5 jours pour preuves complémentaires) ; réunion de clôture CODIR. |
| **4. Suivi post-audit** | Validation du plan d'action à J+30 (1 ligne/NC, owner, échéance) ; suivi trimestriel ; audit de suivi à 12 mois. |

### 3.2 Parcours NIS2 (pivot ISO27001 + compléments) — 6 macro-phases

Source : `workflow-nis2-mise-en-conformite.md` + différentiel `mapping-crosswalk.md`.

0. **Qualification éligibilité** — secteur (Annexe I essentiel / Annexe II important), seuil taille, classification EE/EI, autorité compétente (ANSSI).
1. **Gap Analysis** — 16 mesures Art.21 (mappées au crosswalk ISO — ne redemande pas de preuve si déjà couverte côté ISO27001), gouvernance Art.20 (formation dirigeants, responsabilité personnelle), dispositif de notification (24h/72h/1 mois).
2. **Plan de mise en conformité** — 3 vagues (fondations 3 mois / gestion des risques 6 mois / maturité 12 mois), budget, plan d'action détaillé (owner, coût, échéance, indicateur).
3. **Exécution** — gouvernance du programme, conduite du changement, articulation avec RGPD/DORA (éviter les doublons de notification).
4. **Démonstration de conformité** — dossier de preuves NIS2 centralisé, préparation à un audit/inspection ANSSI, tableau de bord (KPI mensuels).
5. **Maintien en conformité** — activités récurrentes (revue Direction annuelle, tests PCA/PRA, sensibilisation, revue fournisseurs, scans mensuels).

### 3.3 Parcours DORA (pivot ISO27001 + compléments) — 6 macro-phases

Source : `references/dora.md` (pas de workflow Hermes dédié — construit sur le même schéma que NIS2, adapté aux 5 piliers DORA).

0. **Qualification** — type d'entité financière (banque, assurance, gestion d'actifs, crypto...), taille/proportionnalité, autorité (ACPR/AMF).
1. **Gap Analysis 5 piliers** — Gouvernance & risques TIC / Gestion des incidents / Tests de résilience / Risques fournisseurs TIC / Partage d'information — mappés au crosswalk ISO (différentiel : TLPT, registre info, notification 4h).
2. **Plan de mise en conformité** — registre d'information ESA (Art. 28.3), clauses contractuelles Art. 30, stratégies de sortie par prestataire critique, programme de tests annuel.
3. **Exécution** — préparation TLPT si entité significative (12 semaines mini, tous les 3 ans), notification 4h opérationnelle (plus stricte que NIS2 24h), renégociation contrats prestataires critiques.
4. **Démonstration de conformité** — registre d'information annuel déclaré, dossier de preuves.
5. **Maintien** — revue annuelle du cadre de risques TIC, tests annuels, mise à jour du registre.

### 3.4 Parcours RGPD (pivot ISO27001 + compléments) — 5 macro-phases

Source : `references/rgpd.md` (pas de workflow Hermes dédié — construit depuis les obligations RGPD structurées en cycle de vie).

0. **Cadrage** — cartographie des traitements existants, désignation DPO (grille d'obligation Art. 37), bases légales par traitement (Art. 6).
1. **Registre & conformité documentaire** — registre des traitements Art. 30 (responsable + sous-traitant), contrats sous-traitants Art. 28, mentions d'information.
2. **AIPD / DPIA** — grille CNIL de déclenchement (traitement à risque élevé), 4 volets (description systématique, nécessité/proportionnalité, risques droits/libertés, mesures d'atténuation) — *déjà partiellement codé, à réintégrer ici*.
3. **Droits des personnes & sécurité** — procédure de gestion des 8 droits (délai 1 mois), mesures Art. 32 (mapping direct Annexe A ISO), transferts hors UE (SCC/BCR/adéquation).
4. **Suivi & notification** — procédure de violation (72h CNIL, notification personnes si risque élevé), registre interne des violations, revue annuelle.

### 3.5 Parcours EU AI Act (autonome) — 5 macro-phases

Pas de fiche Hermes — construit depuis la structure du règlement (approche par les risques).

1. **Cartographie des systèmes IA** — inventaire, cas d'usage, rôle de l'organisation (fournisseur / déployeur / importateur / distributeur).
2. **Classification du risque** — par système : inacceptable (interdit) / haut risque (Annexe III) / risque limité (transparence) / minimal.
3. **Exigences applicables** — selon classification : gouvernance des données, transparence, supervision humaine, robustesse/précision, documentation technique, marquage CE (haut risque).
4. **Plan de mise en conformité** — actions par système IA, échéances (calendrier d'application échelonné du règlement : interdictions à 6 mois, obligations générales à 12/24/36 mois).
5. **Suivi & gouvernance IA** — comité IA, revue continue, veille réglementaire (le règlement évolue via actes d'exécution).

---

## 4. Volet Consulting — parcours fusionné (13 macro-phases)

Source : fusion intégrale `workflow-onboarding-client-grc.md` (phases 0-5) + `workflow-ebios-rm.md` (5 ateliers) **+ les phases déjà codées** (`diagnostic`, `tprm`, `resilience`) issues du modèle actuel — décision "extension incrémentale" (§8) oblige : rien de l'existant n'est sacrifié.

> Correction post-décision 11 : la première version de cette table (fusion onboarding+EBIOS seule, 10 phases) oubliait `diagnostic`/`tprm`/`resilience` déjà codés. Corrigé ici — "sans rien omettre" appliqué à la relecture, pas seulement à la promesse.

| # | Macro-phase | Origine | Statut |
|---|---|---|---|
| 1 | Pré-engagement (qualification commerciale, devis) | Onboarding Phase 0 | *mutualisé avec le socle commun* |
| 2 | Kick-off & découverte (réunion lancement, cartographie initiale, entretiens) | Onboarding Phase 1 | *mutualisé avec le socle commun* |
| 3 | Diagnostic & état des lieux (hygiène ANSSI, registre RGPD, AIPD) | Existant (`diagnostic`) | déjà codé |
| 4 | TPRM (criticité fournisseurs, formule pondérée) | Existant (`tprm`) | déjà codé |
| 5 | EBIOS Atelier 1 — Cadrage & socle de sécurité | EBIOS RM | déjà codé (à recaler sur le format 5 ateliers) |
| 6 | EBIOS Atelier 2 — Sources de risque (typologie ANSSI, couples SR/OV) | EBIOS RM | déjà codé |
| 7 | EBIOS Atelier 3 — Scénarios stratégiques (écosystème, chemins d'attaque) | EBIOS RM | déjà codé (partiellement — écosystème parties prenantes à ajouter) |
| 8 | EBIOS Atelier 4 — Scénarios opérationnels (MITRE ATT&CK, points de rupture) | EBIOS RM | **à enrichir** — MITRE ATT&CK absent aujourd'hui |
| 9 | EBIOS Atelier 5 — Traitement du risque (réduire/accepter/transférer/refuser, validation Direction, **+ quantification FAIR**) | EBIOS RM + fonctionnalité #4 | existant + **à enrichir** |
| 10 | Résilience & continuité (E3R, RTO/RPO, **+ module PRI entretien guidé**) | Existant (`resilience`) + fonctionnalité PRI (§10.7) | déjà codé + **à enrichir** |
| 11 | Cadrage approfondi mission (référentiel structurant si pertinent, feuille de route 3 horizons, gouvernance, indicateurs) | Onboarding Phase 2 | **à créer** |
| 12 | Premiers livrables & restitution (quick wins, PSSI, RACI, **présentation CODIR** — fonctionnalité #7) | Onboarding Phase 3 | **à créer** |
| 13 | Run & clôture (suivi, signaux d'alerte, clôture, **RETEX capitalisé** — fonctionnalité #3) | Onboarding Phases 4-5 | **à créer** |

Les phases 1-2 sont **partagées visuellement** avec le socle commun (pas de ressaisie). Phases 3-10 = existant à recaler/enrichir. Phases 11-13 = nouvelles.

---

## 5. Modèle de données (esquisse — à affiner en spec technique)

```jsonc
project = {
  id, name, client, created_at, updated_at,
  socle: { qualification, contractualisation, kickoff, cartographie, entretiens, assets_metier, assets_support, nda },
  grc: {
    active: false,
    referentiels_actifs: [],              // ex: ["iso27001", "nis2"]
    iso27001: { preparation: {}, execution: { clauses_4_10: {}, annexe_a: {} /* alimenté par AuditCraft */ }, synthese: {}, suivi: {} },
    nis2:  { qualification: {}, gap_analysis: {}, plan: {}, execution: {}, demonstration: {}, maintien: {} },
    dora:  { /* même forme que nis2 */ },
    rgpd:  { cadrage: {}, registre: {}, aipd: {}, droits_securite: {}, suivi_notification: {} },
    aiact: { cartographie: {}, classification: {}, exigences: {}, plan: {}, gouvernance: {} }
  },
  consulting: {
    active: false,
    phases: { atelier1: {}, atelier2: {}, atelier3: {}, atelier4: {}, atelier5: {}, cadrage_approfondi: {}, premiers_livrables: {}, run_cloture: {} }
  }
}
```

---

## 6. UI — Navigation Kanban

- 1 board Kanban par volet actif (GRC / Consulting) ; colonnes = macro-phases ; cartes = sous-étapes/checklists déplaçables (à faire / en cours / fait).
- Le socle commun reste un formulaire one-shot en tête de mission (pas un Kanban).
- Sélecteur multi-référentiels en tête du board GRC (chips), avec un bandeau "recouvrement avec ISO 27001 : X %" calculé depuis le crosswalk.

## 7. Intégration AuditCraft-GRC

La carte "Contrôles Annexe A" du board ISO27001 tire automatiquement les résultats de `grc_rules.yaml` (scan SSH/Nginx réel) comme preuve pour les contrôles techniques couverts — reste éditable manuellement pour les contrôles organisationnels non scannables.

---

## 8. Décisions finales de cadrage

| # | Question | Décision |
|---|---|---|
| 10 | Ordre de construction | **Socle → ISO27001 (pivot) → Consulting (fusionné) → compléments NIS2/DORA/RGPD (crosswalk) → AIAct** (le plus autonome, en dernier). |
| 11 | Migration du code existant | **Extension incrémentale** — le modèle actuel (`type: grc\|consulting`, ateliers EBIOS déjà codés) n'est pas jeté : on greffe le socle commun + les nouvelles macro-phases par-dessus. Le projet test `cassiopé` est **migré champ par champ**, pas recréé. |

---

## 9. Plan d'action — Jalon 1 (Socle commun + ISO27001 pivot)

Extension incrémentale du modèle existant (`api/modules/projects.py`, `web/src/pages/Projects.tsx`). Aucune tâche ci-dessous n'est commencée sans validation explicite.

**Backend**
1. Étendre `create_default_state` : ajouter un bloc `socle` (qualification, contractualisation, kickoff — nouveaux ; cartographie/entretiens réutilisent `cadrage`/`assets_metier`/`assets_support` existants).
2. Ajouter `grc.active`, `grc.referentiels_actifs: []`, `grc.iso27001` (4 macro-phases : préparation/exécution/synthèse/suivi) — migrer dedans les champs `evaluation`/`restitution` actuels plutôt que les dupliquer.
3. Nouvelle route API qui appelle `auditcraft_grc.run()` et mappe les résultats sur les contrôles Annexe A concernés (`grc.iso27001.execution.annexe_a`).
4. Script de migration one-shot pour `projects/cassiopé/project.json` vers le nouveau schéma (champ par champ, sans perte).

**Frontend**
5. Nouveau composant Kanban **générique et piloté par données** (colonnes = macro-phases, cartes = sous-étapes déplaçables), lisant un `api/frameworks/<id>/workflow.yaml` plutôt que du contenu codé en dur — `web/src/components/PhaseKanban.tsx` (cf. §10.3, ajouter un référentiel = ajouter un YAML, pas du code).
6. Formulaire socle commun (étend le formulaire de cadrage existant).
7. Board ISO27001 (4 colonnes) avec carte "Contrôles Annexe A" affichant automatiquement les résultats AuditCraft.
8. Toggle d'activation des volets GRC/Consulting sur la fiche projet.
8bis. Modèle de blocs génériques (titre/paragraphe/tableau/liste/checklist, statut exemple-vs-rempli) + contrôles ajouter/supprimer/réordonner, réutilisé formulaires de phase + aperçu rapport (§10.9).
8ter. Moteur d'export DOCX (`docxtpl`, gabarit ISO27001 éditable dans Word) + PDF (`WeasyPrint`) branché sur le modèle de blocs.

**Tests & vérification**
9. Tests backend (`api/tests/test_projects.py`) sur le nouveau schéma socle + `grc.iso27001`.
10. Vérification manuelle dans le navigateur (dev server + clic à travers le board).

→ **En attente de ton feu vert explicite avant de commencer la tâche 1.**

### Où s'insèrent les extensions du §10 dans l'ordre de build

| Extension | Jalon |
|---|---|
| Moteur Kanban générique piloté par YAML (§10.3) | **Jalon 1** (tâche 5, dès le départ — évite de tout reconstruire ensuite) |
| Bouton "Vérifier les référentiels" (§10.2) | Jalon 2 (avec les parcours NIS2/DORA/RGPD, quand plusieurs référentiels existent) |
| Ingestion fichiers SIEM/EDR + Rafraîchir (§10.5) | Jalon 2, en extension d'AuditCraft-GRC |
| Copilote LLM (§10.4) | Jalon 3 (une fois le contenu factuel des parcours en place — l'IA n'a rien à assister avant) |
| Frise court/moyen/long terme dashboard (§10.6) | Jalon 3 |
| Module PRI entretien guidé (§10.7) | Avec le parcours Consulting (phase Résilience) |
| Modèle de blocs génériques + docxtpl/WeasyPrint (§10.9) | **Jalon 1** (tâche 5 bis — le moteur de rendu de rapport doit exister avant le premier export ISO27001) |
| Connecteurs cloud AWS/Azure v1 fichier (§10.8) | Jalon 2, avec l'ingestion SIEM/EDR |
| Connecteurs cloud AWS/Azure v2 live (§10.8) | Jalon 3+, avec les connecteurs live SIEM/EDR |

---

## 10. Extensions stratégiques (évolutivité, LLM, connecteurs, benchmark concurrentiel)

Ajouts demandés le 28/07/2026. Méthodologie appliquée : pour chaque brique, plusieurs options sont notées **0-10** sur (a) fidélité à la souveraineté "100% local par défaut", (b) factualité — zéro donnée inventée, (c) cohérence avec l'architecture Policy-as-Code existante, (d) différenciation concurrentielle réelle. Seule l'option ≥ 9/10 est retenue ; sinon itération. Recherche concurrentielle menée (CISO Assistant, Vanta, Drata, OneTrust, Eramba) — sources en bas de section.

### 10.1 Benchmark concurrentiel — ce qu'on retient / ce qu'on rejette

| Concurrent | Ce qui est bon (à reprendre) | Ce qui ne convient pas (à rejeter) |
|---|---|---|
| **CISO Assistant** (open-source, **le concurrent réel**) | Bibliothèque de 150+ référentiels avec mapping automatique, **framework builder**, **EBIOS RM 5 ateliers natif**, **quantification CRQ**, BIA, TPRM, API/n8n/MCP/Kafka | Registre GRC **pour un RSSI interne**, pas un cockpit de mission consultant : aucun guidage lettre de mission / entretiens par rôle / restitution CODIR / RETEX. Reporting reconnu faible (issue GitHub ouverte sur le rapport EBIOS RM) |
| **Vanta / Drata** | Collecte de preuves continue via connecteurs (evidence-as-code) | SaaS US, hébergement hors UE, prix mensuel élevé, **zéro EBIOS RM / ANSSI / CNIL natif** — gap confirmé par la recherche |
| **OneTrust** | Couverture large (privacy + IA + tiers) | Usine à gaz enterprise, hors de portée d'un consultant solo/PME |
| **Constat marché 2026** | Le battage "IA agentique autonome" (compliance générée seule par l'IA) | **Rejeté explicitement** : contraire au principe "zéro donnée inventée" de GREEN SHIELD. L'IA reste assistante sur des données factuelles saisies, jamais génératrice de conformité de son propre chef. |
| **Gap identifié (Sekurno)** | "Documented ≠ validated" — les concurrents attestent des politiques déclarées, rarement des preuves techniques réelles | GREEN SHIELD a déjà l'avantage ici via **AuditCraft-GRC** (scan technique réel, pas déclaratif) — à mettre en avant, pas à copier |

**Positionnement retenu** *(corrigé le 28/07/2026 après vérification — cf. [audit-critique-plan.md](audit-critique-plan.md) F1)* : **cockpit de conduite de mission pour consultant externe**, pas « une plateforme GRC de plus ».

> ⚠️ La version initiale de ce paragraphe affirmait « EBIOS RM/ANSSI natifs — aucun concurrent ne le fait ». **C'est faux** : CISO Assistant (intuitem, français, open source) implémente EBIOS RM avec les 5 ateliers et un graphe d'objets dédié, plus la quantification CRQ et le TPRM. Affirmation retirée.

Les 3 différenciateurs qui résistent à la vérification :
1. **Guidage pas-à-pas de la mission** (lettre de mission, NDA, grille d'entretien par rôle interrogé, restitution CODIR) — les plateformes GRC servent le RSSI qui pilote son programme, pas le consultant qui enchaîne les missions.
2. **Génération de livrables Word réellement éditables** — point faible reconnu du concurrent.
3. **Capitalisation RETEX personnelle** — par nature non réplicable par un éditeur : c'est l'historique de missions de Dorian.

Complémentarité assumée : le client peut avoir CISO Assistant, le consultant a GREEN SHIELD.

### 10.2 Mise à jour des référentiels — bouton dans la sidebar

**Options notées :**
- Auto-scraping des sources officielles (EUR-Lex, ISO, ANSSI) au clic → **3/10** : casse le "100% hors-ligne", risque juridique (textes ISO payants/copyright), scraping non fiable dans le temps.
- Bouton "Vérifier les référentiels" ouvrant un panneau par référentiel (version actuelle, date de dernière vérification, lien vers la source officielle à consulter manuellement, bouton "Éditer le contenu" ouvrant le YAML/workflow en interne) → **9/10**.

**Retenu (9/10)** : icône ↻ **au-dessus de la roue Réglages** dans la sidebar (comme demandé). Ouvre un panneau listant chaque référentiel avec version, date de vérification, lien source officielle, et action "Marquer à jour" / "Éditer" — le consultant reste l'autorité qui valide tout changement de contenu (cohérent avec "on n'invente rien").

### 10.3 Évolutivité de l'architecture (ne pas rester figé)

Aujourd'hui les référentiels sont déjà en YAML (Policy-as-Code), mais les **parcours/phases restent codés en dur** dans `Projects.tsx`. Pour ajouter un référentiel ou faire évoluer un parcours sans réécrire de code React :

**Retenu (9/10)** : un moteur de Kanban générique (tâche 5 du Jalon 1) qui lit un fichier `api/frameworks/<id>/workflow.yaml` décrivant les macro-phases et sous-étapes — ajouter NIS2-v2 ou un nouveau référentiel = ajouter un fichier YAML, pas du code. C'est le même principe que le "framework builder" de CISO Assistant, adapté au modèle 100% fichiers locaux de GREEN SHIELD.

### 10.4 Copilote LLM intégré

**Options notées :**
- Cloud uniquement (clé API imposée) → 6/10, casse la souveraineté par défaut.
- Local uniquement (LLM embarqué, ex. Ollama) → 7/10, souverain mais moins puissant, pas de choix pour l'utilisateur.
- **Connecteur pluggable : local par défaut + clé API cloud optionnelle chiffrée localement** → **10/10**. C'est déjà amorcé dans [Settings.tsx](../web/src/pages/Settings.tsx) (clé Copilote stockée en `localStorage`, "sans clé = intelligence experte locale") et **c'est exactement le pattern déjà en prod sur RED SHIELD** ("Connecteurs — VT / SIEM / IMAP / LLM chiffrés").

**Retenu** : réutiliser le pattern connecteur chiffré de RED SHIELD. Le Copilote sert à : générer/corriger des sections de rapport, détecter des incohérences (ex : un contrôle marqué "Conforme" sans preuve attachée), reformuler pour le CODIR — **jamais** à inventer un fait, un score ou une preuve non saisie. Chaque suggestion IA doit citer le champ/preuve source dont elle dérive.

### 10.5 Connecteurs réseau (SIEM/EDR et autres sources)

**Options notées :**
- Polling live des API SIEM/EDR clients depuis l'appli → 5/10 : lourd (auth par éditeur), surface d'attaque, hors de portée solo-consultant en v1.
- **Ingestion par dépôt de fichier** (export CSV/JSON/Syslog du SIEM/EDR client déposé dans `targets/`, parsé, avec bouton "Rafraîchir") → **9/10** : réutilise exactement le pattern déjà éprouvé d'AuditCraft-GRC (lecture seule de `sshd_config`/`nginx.conf`), zéro credential réseau à gérer, couvre le besoin "pré-remplir les champs + refresh".
- Connecteurs live (Wazuh/Elastic/Syslog) façon RED SHIELD → bon en v2, explicitement marqué comme sortant du mode 100% hors-ligne, opt-in.

**Retenu v1** : extension du dossier `targets/` à des formats SIEM/EDR/scanner de vulnérabilités (CSV/JSON), bouton "Rafraîchir" qui reparse et met à jour les champs pré-remplis + les documents liés. **v2 (plus tard)** : connecteurs live opt-in sur le modèle RED SHIELD.

### 10.6 Dashboard — visualisation court/moyen/long terme

Se branche naturellement sur les **"3 horizons"** déjà présents dans les workflows Hermes (0-3 mois / 3-9 mois / 9-18 mois — onboarding et NIS2 "3 vagues"). Ajout au dashboard existant (qui a déjà les progress rings, TRACKING.md) : une **frise temporelle agrégée** tous projets confondus, regroupant quick wins (court terme), chantiers structurants (moyen terme) et maturité/certification (long terme).

### 10.7 Module PRI (Plan de Reprise Informatique) — complétion guidée par entretien

Le PRI est pré-rempli par des gabarits standards (déjà dans l'esprit des "sélecteurs de modèles" Phase 1), mais avec un **mode entretien guidé** : le consultant choisit le poste de la personne interrogée (RSSI / DSI / Exploitant / RH...) et l'appli ne montre que les questions pertinentes pour ce rôle, pré-remplies avec des réponses standards éditables — pour coller au plus près du réel pendant l'entretien, sans jamais inventer une réponse à la place de l'interlocuteur. Rattaché au volet Résilience (E3R) du Consulting et à l'A.5.29/30 côté ISO27001.

### 10.8 Agrégation cloud AWS / Azure

**Options notées :**
- Réimplémenter un scanner cloud maison (interroger chaque service et ré-évaluer nous-mêmes) → **3/10** : réinvente ce qu'AWS Security Hub / Azure Defender for Cloud font déjà nativement en continu (CIS/PCI/SOC2 déjà mappés), coût de maintenance disproportionné pour un outil solo.
- **Connecteur lecture seule agrégeant les services de conformité natifs déjà existants** : côté AWS, **Security Hub** (findings normalisés ASFF) + **AWS Config** (rules compliance) ; côté Azure, **Azure Policy** (regulatory compliance dashboard) + **Defender for Cloud** (Secure Score) → **9/10**. On agrège des évaluations déjà produites par le cloud, credentials strictement lecture seule (rôle IAM managé `SecurityAudit` côté AWS, rôle `Reader` côté Azure), chiffrées localement — même pattern que le Copilote LLM (§10.4).
- Export manuel de rapport (Security Hub export JSON / Azure compliance report) déposé dans `targets/cloud/` → **8/10**, cohérent avec le choix déjà acté sur SIEM/EDR (§10.5) mais sans rafraîchissement live.

**Retenu** : **v1 = export/dépôt fichier** (même mécanique que §10.5), **v2 = connecteur lecture seule** (Security Hub/Config + Azure Policy/Defender for Cloud), credentials chiffrées localement, bouton Rafraîchir. Les findings sont mappés vers les contrôles Annexe A / référentiel actif via le crosswalk.

**Insight d'architecture** : AuditCraft-GRC (configs on-prem), l'ingestion SIEM/EDR (§10.5) et les connecteurs cloud (§10.8) alimentent tous la **même colonne "Preuves techniques"** du board ISO27001/référentiel — un seul pipeline d'agrégation de preuves, trois sources.

### 10.9 Génération documentaire — DOCX réel, PDF, blocs éditables

État actuel (`TRACKING.md`) : HTML/Markdown + CSS d'impression, "ouvrable" dans Word, PDF via impression navigateur. **Insuffisant** pour la demande (vrai DOCX, tableaux façon Excel en présentation DOCX, édition libre).

**Options notées (génération) :**
- Garder HTML "ouvrable" dans Word → **4/10** : pas un vrai `.docx`, Word affiche un avertissement de format, tableaux fragiles.
- **`docxtpl` (python-docx-template)** : le gabarit est un **vrai fichier .docx** avec des balises Jinja2, rempli depuis les données du projet, boucles pour les tableaux (registre risques, SoA, RACI, TPRM...) → **10/10**. Fichier natif éditable sans avertissement, tableaux fiables, **et le gabarit est modifiable directement dans Word par Dorian** sans toucher au code — répond aussi à l'exigence d'évolutivité (§10.3).
- Pour le PDF : générer côté serveur avec **WeasyPrint** (pur Python, pas de LibreOffice/Word requis) plutôt que compter sur l'impression navigateur → bouton "Télécharger en PDF" fiable et cohérent avec le mode hors-ligne.
- Contenu "façon Excel" (registres) : rendu en **tableaux formatés dans le même DOCX** (boucle docxtpl) plutôt qu'un `.xlsx` séparé à maintenir — un export CSV brut reste disponible en option pour la réutilisation de la donnée.

**Retenu** : `docxtpl` pour le DOCX (y compris les tableaux type registre), `WeasyPrint` pour le PDF serveur, CSV en option.

**Options notées (édition en direct — "ajouter/supprimer du texte ou une fonction") :**
- Formulaires figés (champs fixes, comme aujourd'hui) → **4/10** : ne permet pas l'ajout/suppression libre demandé.
- **Modèle de blocs générique** : chaque section (une carte de phase Kanban ou une partie du rapport final) est une liste ordonnée de blocs typés (titre / paragraphe / tableau / liste / checklist), avec des contrôles génériques "+ ajouter" / "supprimer" / réordonner, **partagés entre le remplissage des phases ET l'aperçu du rapport avant export** → **9/10** : un seul mécanisme construit une fois, réutilisé partout. Chaque bloc porte un statut `exemple pré-rempli` (affiché grisé/italique, à valider ou remplacer) vs `rempli par le consultant` (texte normal) — distingue visuellement le gabarit du factuel, cohérent avec "on n'invente rien".
- Éditeur riche type traitement de texte intégré (contenteditable libre) → **6/10** : complexité disproportionnée, inutile puisque l'export final est de toute façon réédité dans Word ensuite.

**Retenu** : modèle de blocs générique, rendu ensuite par les 3 sorties (DOCX via docxtpl, PDF via WeasyPrint, Markdown/CSV brut).

## 11. Fonctionnalités de démarcation métier — verrouillées le 28/07/2026

Toutes retenues (validation explicite), notées ≥8/10 :

| # | Fonctionnalité | Score | Où elle s'accroche dans l'existant |
|---|---|---|---|
| 1 | Dossier de preuve partageable hors-ligne ("Trust Center" statique, signé/daté) | 9 | Réutilise le moteur DOCX/PDF (§10.9) + la bibliothèque de preuves (#2) |
| 2 | Bibliothèque de preuves réutilisables multi-référentiels (1 preuve, tags multiples, crosswalk) | 9 | Rend concret le crosswalk (§0 décision 9, §10.1) dans le modèle de données |
| 3 | Capitalisation RETEX personnelle (cas clôturés taggés, suggérés sur missions similaires) | 9 | Phase 13 "Run & clôture" du volet Consulting (§4) |
| 4 | Quantification FAIR branchée sur le plan de traitement EBIOS | 9 | Phase 9 "EBIOS Atelier 5" du volet Consulting (§4) — script `calcul_fair.py` Hermes |
| 5 | Horodatage/hash de chaque preuve et document généré | 8 | Transverse — à poser dans le modèle de données dès le Jalon 1 pour éviter une migration plus tard |
| 6 | Alertes d'échéances proactives sur le dashboard | 8 | Phases "Maintien" NIS2/DORA/RGPD (§3.2-3.4) + audits de suivi ISO27001 (§3.1) |
| 7 | Mode "présentation CODIR" (3ᵉ type d'export, 1-2 pages) | 8 | Phase 12 "Premiers livrables" du volet Consulting (§4) + moteur DOCX (§10.9) |
| 8 | Copilote en mode "second regard" avant livraison | 8 | Extension du Copilote LLM (§10.4) |

## 12. Plan de jalons consolidé (remplace les mentions éparses "Jalon 2/3" plus haut)

| Jalon | Contenu |
|---|---|
| **1** | Socle commun · Kanban générique YAML · **modèle de blocs + docxtpl + WeasyPrint** · parcours **ISO27001** (pivot, 4 macro-phases) · intégration AuditCraft-GRC · structure de données bibliothèque de preuves + horodatage/hash (#2, #5 — posés dès maintenant, exploités plus tard) · migration `cassiopé` |
| **2** | Volet **Consulting** fusionné (13 macro-phases, §4) · enrichissement MITRE ATT&CK (Atelier 4) · **quantification FAIR** (#4) · **mode présentation CODIR** (#7) · module **PRI entretien guidé** (§10.7) |
| **3** | Compléments **NIS2 / DORA / RGPD** (pivot + crosswalk) · bouton **"Vérifier les référentiels"** (§10.2) · exploitation active de la **bibliothèque de preuves multi-référentiels** (#2) · ingestion fichiers **SIEM/EDR + cloud AWS/Azure v1** (§10.5, §10.8) · **alertes d'échéances** (#6) |
| **4** | Parcours **EU AI Act** autonome (5 macro-phases, §3.6) |
| **5** | **Copilote LLM** (§10.4) + mode **"second regard"** (#8) · connecteurs **live v2** (SIEM/EDR, cloud) opt-in · **dossier de preuve partageable** (#1) · dashboard : frise 3 horizons (§10.6) + radar de maturité NIST CSF |

## 13. Agenda de mission, grilles d'entretien et génération de livrables (28/07/2026)

Cette section **recentre le produit** : GREEN SHIELD n'est pas un registre GRC, c'est un **assistant de conduite de mission** dont la fonction première est de **ne rien omettre**. C'est la réponse directe au repositionnement imposé par [audit-critique-plan.md](audit-critique-plan.md) F1.

### 13.1 Découverte : les données temporelles existent déjà

Vérifié dans les workflows Hermes — aucune donnée à inventer :

| Workflow | Données temporelles déjà présentes |
|---|---|
| Onboarding client | Durée 2-4 semaines · « Réunion de lancement (**jour 1**) » · « Entretiens prioritaires (**jours 2-5**) » · liste nominative de **8-10 entretiens d'1h** avec le sujet de chacun |
| Audit ISO 27001 | Durée 4-6 semaines · Préparation Semaine 1 · doc demandée **J-15** · programme envoyé **J-7** · Exécution Semaines 2-4 · Restitution Semaines 5-6 · table **Clause → Personne à rencontrer → Questions clés** |
| EBIOS RM | Durée 6-10 semaines · durée par atelier (**1-2 j**, 1-2 j, 2-3 j, 3-5 j, 2-3 j) · **5-10 jours de consolidation entre ateliers** |
| NIS2 | Durée 6-12 mois · Phase 0 : 1-2 sem · Phase 1 : 4-6 sem · Phase 2 : 2-3 sem · 3 vagues (3/6/12 mois) |

**Conséquence d'architecture** : l'agenda n'est **pas un module séparé**, c'est une **seconde vue sur le même `workflow.yaml`** qui pilote déjà le Kanban (§10.3). On enrichit chaque étape de métadonnées `jour_relatif` / `duree` / `role_a_rencontrer` / `questions[]` / `livrable[]`, et on obtient trois vues sans duplication :

```
workflow.yaml  ──┬──▶ Vue Kanban      (où j'en suis)
                 ├──▶ Vue Agenda      (quoi faire J1, J2, J3… et avec qui)
                 └──▶ Grille entretien (quelles questions poser à cette personne)
```

Les dates sont **relatives** (J+1, S+2) et deviennent absolues au lancement du projet, via une date de démarrage saisie à la création — l'agenda se recalcule si la mission glisse.

### 13.2 Grilles d'entretien par rôle

Généralise le §10.7 (qui limitait à tort ce mécanisme au seul module PRI) : **chaque étape** peut porter une grille d'entretien ciblée par rôle (Sponsor, RSSI, DPO, DSI, RH, Achats, Juridique, Métier, Audit — la liste des 8-10 entretiens Hermes). L'appli affiche les questions pertinentes pour la personne en face, avec réponses pré-remplies éditables.

**Attribution obligatoire** : chaque réponse est horodatée et rattachée à **qui l'a déclarée** (nom, fonction, date). C'est le socle du §13.4.

### 13.3 Génération des livrables méthodologiques

Les réponses aux grilles alimentent directement le contexte `docxtpl` (§10.9). Aucun mécanisme nouveau : registre RGPD Art.30, AIPD/PIA, rapport d'audit, PSSI, plan de traitement sont des **restitutions factuelles de ce que le client a déclaré**. C'est exactement le cas d'usage prévu.

Base légale solide pour le RGPD : la CNIL publie des **modèles libres** (registre des traitements, méthode PIA) — contrairement au texte ISO qui est sous copyright ([audit-critique-plan.md](audit-critique-plan.md) F3).

### 13.4 ⚠️ Documents contractuels : ce que l'appli peut et ne peut PAS faire

**Demande initiale** : « un QCM qui génère automatiquement le rapport de confidentialité à signer, pour me dédouaner de toute problématique ».

**Ce qui ne marche pas (noté 4/10)** : assembler dynamiquement des **clauses juridiques** via un QCM. Un NDA est un **contrat** : il engage la responsabilité professionnelle du consultant. Un document dont les clauses varient au gré de réponses à un questionnaire est un document **que personne n'a validé juridiquement**. Et surtout : **une application ne peut pas dédouaner son auteur**. Générer un contrat automatiquement *augmente* l'exposition au lieu de la réduire.

**Alternative retenue (9/10)** — séparation nette de deux natures de documents :

| Nature | Exemples | Règle |
|---|---|---|
| **Contractuel** (engage juridiquement) | NDA, lettre de mission, clauses de sous-traitance Art. 28 | Gabarit **figé, validé une seule fois par un juriste**. Le QCM ne remplit que les **variables factuelles** (raison sociale, périmètre, dates, signataires). **Aucune clause générée dynamiquement, jamais de rédaction LLM.** |
| **Méthodologique** (restitue un constat) | Registre RGPD, AIPD, rapport d'audit, PSSI, plan de traitement | QCM + génération automatique : c'est le cas d'usage prévu (§13.3). |

**Ce qui protège réellement le consultant** — et que l'appli sait faire :

1. **Attribution nominative + horodatage** de chaque déclaration (§13.2) — « qui a dit quoi, quand ». Hermes le formule explicitement : *documenter les décisions protège le consultant*.
2. **Hash + horodatage** de chaque livrable émis (fonctionnalité #5, §11) — prouve qu'un rapport daté du X contenait bien Y.
3. **Mention de réserve automatique** insérée dans chaque livrable généré : les constats reposent sur les déclarations des personnes interrogées à telle date, et sur les preuves collectées listées en annexe. C'est la pratique d'audit standard (ISO 19011 : constats fondés sur des preuves) — et c'est ce qui délimite la responsabilité, pas une clause auto-générée.

→ La protection vient de la **traçabilité**, pas de l'automatisation du juridique.

### 13.5 Renvois aux sources officielles (« hors couverture »)

Concept de premier ordre, directement issu de la demande : quand un sujet n'est pas couvert par l'appli, elle **ne fait pas semblant**. Chaque étape peut porter :

- `sources[]` — liens vers la source faisant autorité (guide ANSSI, page CNIL, article EUR-Lex, contrôle ISO)
- un statut explicite **`hors couverture — se référer à`** plutôt qu'un champ vide ou une réponse approximative

C'est l'application littérale du principe « on n'invente rien », et cela résout aussi partiellement la charge de contenu ([audit-critique-plan.md](audit-critique-plan.md) F2) : un sujet non encore rédigé est **honnêtement marqué comme tel avec sa source**, au lieu de bloquer la sortie du jalon.

### 13.6 Impact sur le plan de build

L'agenda et les grilles d'entretien étant des **vues sur le `workflow.yaml`**, ils ne créent pas de jalon supplémentaire — mais le schéma du YAML doit être conçu **dès le Jalon 0** pour porter ces métadonnées, sinon il faudra le remanier ensuite.

| Élément | Jalon |
|---|---|
| Schéma `workflow.yaml` incluant `jour_relatif`, `duree`, `role_a_rencontrer`, `questions[]`, `sources[]` | **Jalon 0** (conception du schéma uniquement) |
| Vue Agenda + date de démarrage projet + recalcul si glissement | **Jalon 1** |
| Grilles d'entretien avec attribution nominative | **Jalon 1** |
| Gabarit NDA figé + variables factuelles + mention de réserve | **Jalon 1** |
| Statut « hors couverture » + `sources[]` affichés dans l'UI | **Jalon 1** |

## 14. Matrice de couverture & écarts résiduels (28/07/2026)

Contrôle de couverture mené à partir du glossaire de 25 concepts et du corpus de questions d'audit fournis par Dorian. Le contenu des questions est stocké dans [contenu-grilles-entretien.md](contenu-grilles-entretien.md) — il alimentera directement le champ `questions[]` des `workflow.yaml` (§13.2) et **réduit d'autant la charge de contenu** ([F2](audit-critique-plan.md)).

### 14.1 Écarts de périmètre — TRANCHÉS le 28/07/2026

| # | Écart | Décision actée | Jalon |
|---|---|---|---|
| **G1** | **Homologation de sécurité** | **IN — pas un 6ᵉ parcours.** Livrable optionnel **généré depuis l'Atelier 5** : risques résiduels + autorité d'homologation + **décision formelle d'acceptation**. ~90 % de réutilisation de l'EBIOS existant. | 2 |
| **G2** | **Revue d'architecture** (défense en profondeur, Zero Trust) | **IN — réduite à une checklist** intégrée à la phase Diagnostic : segmentation réseau, IAM, durcissement, défense en profondeur, maturité Zero Trust. Alimente les recommandations. **Pas de module de cartographie d'architecture** (maîtrise de la charge, F12). | 2 |
| **G3** | **Catalogue de mesures de sécurité** | **IN et TÔT.** C'est de l'**infrastructure**, même motif « écrire une fois / taguer / réutiliser » que la bibliothèque de preuves (#2) : mesures mappées aux référentiels, réutilisées par le plan de traitement, les quick wins et les plans NIS2/DORA. Sans elle, les mesures seraient codées en dur dans 5 parcours puis à refactorer. | **1** |
| **G4** | **Exercice / simulation de crise** | **IN — scénario + injects + grille d'observation + RETEX**, **généré depuis les scénarios opérationnels de l'Atelier 4** déjà modélisés. Quasi gratuit puisque les scénarios existent. Pas un simulateur. | 2 |
| **G5** | **Registre interne des violations** (Art. 33.5) | **IN.** Petite table, y compris violations non notifiables (conséquences + actions de remédiation). Obligation légale, coût négligeable. | 3 |

### 14.1bis Criticité des tiers — écart TPRM / EBIOS TRANCHÉ

**Décision : ratio ANSSI + scission selon les deux volets.**

| Volet | Méthode retenue |
|---|---|
| **Consulting** (EBIOS RM Atelier 3) | Formule officielle ANSSI : **(dépendance × pénétration) / (maturité × confiance)**, restituée par le **radar des parties prenantes** (zones concentriques). |
| **GRC** (DORA / NIS2) | **Aucun scoring EBIOS** — ces référentiels ne s'en réclament pas. À la place : exigences de conformité (registre d'information DORA Art. 28.3, clauses contractuelles Art. 30, stratégie de sortie, évaluation avant acquisition NIST ID.RA-10). |

**Justification chiffrée** (sur les données pré-remplies actuelles) : la moyenne arithmétique du code donne AWS 3,5 et ESN 3,75 — quasi indistinguables. Le ratio ANSSI donne AWS 1,56 et ESN 2,22, soit un écart de 1,4× méthodologiquement correct (l'ESN a plus de pénétration pour moins de maturité et de confiance), et fait tomber le cabinet comptable à 0,25 au lieu de 2,25. **La moyenne compresse les écarts et empêche de prioriser** — ce qui est précisément l'objet de l'atelier.

**Bug à corriger au passage** : la donnée pré-remplie « Hébergeur Cloud AWS » stocke `score: 4.5 / rating: "Critique"` alors que la formule effectivement appliquée en [Projects.tsx:233](../web/src/pages/Projects.tsx:233) produit **3,5 → « Élevé »**. La note change donc dès la première réédition du tiers, potentiellement devant le client.

### 14.2 Enrichissements à intégrer (pas des manques de périmètre, des précisions méthodologiques)

1. **AIPD — 5 obligations organisationnelles absentes du module codé** : consulter le DPO · recueillir l'avis des personnes concernées · se référer aux listes CNIL · **saisir la CNIL avant traitement si risque résiduel élevé (Art. 36)** · mettre à jour l'AIPD à chaque changement de niveau de risque.
2. **⚠️ Écart méthodologique EBIOS Atelier 3 vs TPRM codé** : le code calcule une **moyenne arithmétique** des 4 critères `(dépendance + pénétration + (6−maturité) + (6−confiance)) / 4`. EBIOS RM croise **deux axes** : *exposition* (dépendance × pénétration) × *fiabilité cyber* (maturité × confiance). Les deux ne donnent pas le même classement. **À trancher avant de figer le module TPRM.**
3. **Remédiation — 3 volets ANSSI** (stratégique / opérationnel / technique) : le spec ne porte que E3R, qui est la séquence. Manquent les **critères d'arbitrage Direction** entre urgence de redémarrage et coûts induits à long terme (volet stratégique).
4. **Mappings de contrôles techniques à ajouter** : CIS 7 + NIST ID.RA-01 (vulnérabilités) · CIS 8 (journalisation) · NIST ID.RA-10 (évaluation fournisseurs avant acquisition) · NIST ID.AM (inventaire sur tout le cycle de vie). Les booléens `vulnerabilities_active` / `logging_active` existent déjà mais **sans mapping**.
5. **NIST CSF / SP 800-53** ne font pas partie des 5 référentiels retenus (§3), alors qu'ils sont cités comme sources et que Hermes fournit `references/nist-csf.md` + `scripts/scoring_maturite_nist_csf.py` **inexploités**. NIST CSF n'apparaît qu'au Jalon 5 comme « radar de maturité ». Candidat naturel au **6ᵉ parcours**.

### 14.3 Réutilisation du glossaire comme aide contextuelle

Le glossaire des 25 concepts (définition · application · importance · source) constitue la matière du **module d'aide contextuelle** déjà prévu comme intention dans [REFERENTIEL.md](../REFERENTIEL.md) (« expliquer à quoi correspond chaque case de manière pédagogique »). Ses sources (EUR-Lex, cyber.gouv.fr, CNIL, ANSSI, NIST) alimentent directement le `sources[]` de §13.5.

> ⚠️ **Réserve de rigueur** : la colonne « Objectif Pédagogique » du glossaire est marquée *(Inferred)* par son auteur — donc **déduite, non sourcée**. Dans une application qui promet le zéro-invention, elle doit être soit validée explicitement, soit affichée comme interprétation, jamais présentée au même niveau que les définitions sourcées.

### Sources (recherche concurrentielle)
- [CISO Assistant — Open-source GRC](https://intuitem.com/) / [GitBook](https://intuitem.gitbook.io/ciso-assistant) / [Help Net Security](https://www.helpnetsecurity.com/2026/01/14/ciso-assistant-open-source-cybersecurity-management-grc/)
- [Vanta vs Drata vs OneTrust — what none of them cover](https://www.sekurno.com/post/vanta-vs-drata-vs-onetrust-which-compliance-platform-do-you-need-and-what-none-of-them-cover)
- [Best AI GRC Platforms Compared 2026](https://compyl.com/blog/best-ai-grc-platforms-compared-2026/)
- [SIEM/EDR integration in GRC continuous monitoring](https://continuumgrc.com/using-siem-soar-and-grc-tools-for-continuous-monitoring/)
- [Air-gapped LLM deployment architecture](https://discretestack.com/blog/air-gapped-ai-deployment-no-internet-guide)

---

## STATUT : CADRAGE VERROUILLÉ (28/07/2026)

Plus aucune modification de périmètre sans repasser par ce document. Prochaine étape : tâche 1 du Jalon 1 (§9), sur feu vert de Dorian.
