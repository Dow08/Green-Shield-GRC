# CONTENU — Grilles d'entretien & questions d'évaluation

> **Nature de ce document** : contenu métier source, destiné à alimenter le champ `questions[]` des `workflow.yaml` (cf. [spec §13.2](spec-refonte-grc-consulting.md)). Ce n'est pas un document de conception — c'est de la matière première validée par Dorian.
> **Statut** : rédigé et sourcé par Dorian le 28/07/2026. Réduit d'autant la charge de contenu identifiée en [F2](audit-critique-plan.md).
> **Colonne « rôle à interroger »** : dérivée de la liste des 8-10 entretiens prioritaires du workflow Hermes `workflow-onboarding-client-grc.md`.

---

## 1. EBIOS Risk Manager — les 5 ateliers

### Atelier 1 — Cadrage et socle de sécurité
*Rôles à interroger : Sponsor exécutif, RSSI, Direction métier*

- Quelles sont les missions principales de l'organisation et quelles sont les **valeurs métier** (processus, informations) essentielles pour les accomplir ?
- Quels sont les **biens supports** (réseaux, applications, locaux, personnel) sur lesquels reposent ces valeurs métier ?
- Quels sont les **événements redoutés** (vol de données, arrêt de production…) et comment évaluez-vous la **gravité** de leurs impacts (financiers, juridiques, image, environnement) ?
- Le **socle de sécurité** (réglementations, normes ISO, PSSI, guides d'hygiène) est-il clairement défini, et les **écarts de conformité sont-ils justifiés** ?

### Atelier 2 — Sources de risque
*Rôles : RSSI, Lead Sécurité*

- Avez-vous identifié les **sources de risque (SR)** pertinentes pour votre secteur (cybercriminels, concurrents, activistes…) et quels sont leurs **objectifs visés (OV)** ?
- Comment évaluez-vous la **pertinence** de ces attaquants selon leur **motivation** et leurs **ressources** (financières, techniques, temps) ?

### Atelier 3 — Scénarios stratégiques
*Rôles : RSSI, Achats, Juridique*

- Avez-vous **cartographié votre écosystème** (clients, prestataires, partenaires, filiales) ?
- Avez-vous évalué le **niveau de menace** de chaque partie prenante en calculant son **exposition** (dépendance × pénétration dans le SI) croisée avec sa **fiabilité cyber** (maturité × confiance) ?
- Quels sont les scénarios stratégiques d'**attaque directe** ou **par rebond** via une partie prenante critique ?

> ⚠️ **Écart méthodologique à corriger dans le code** : le module TPRM actuel utilise ces 4 mêmes critères mais avec une **moyenne arithmétique** `(dépendance + pénétration + (6-maturité) + (6-confiance)) / 4`. EBIOS RM procède différemment : **exposition × fiabilité** (deux axes croisés, pas une moyenne). À trancher — voir [spec §14](spec-refonte-grc-consulting.md).

### Atelier 4 — Scénarios opérationnels
*Rôles : Lead Sécurité / Architecte, DSI*

- Avez-vous modélisé les **modes opératoires** selon la séquence type : **Connaître** (reconnaissance) → **Rentrer** (intrusion) → **Trouver** (latéralisation / élévation de privilèges) → **Exploiter** (vol, destruction) ?
- Comment évaluez-vous la **vraisemblance** (probabilité de succès, difficulté technique) de ces chemins d'attaque ?

### Atelier 5 — Traitement du risque
*Rôles : Sponsor exécutif, RSSI*

- Pour chaque risque inacceptable, quelle est la **stratégie de traitement** : réduction, maintien (acceptation), transfert, ou évitement ?
- Le plan de traitement définit-il des mesures réparties en **4 axes** : Gouvernance, Protection, Défense, Résilience ?

---

## 2. Directive NIS 2

*Rôles : Sponsor exécutif, RSSI, Juridique*

- L'organisation a-t-elle réalisé une évaluation pour déterminer si elle entre dans les critères d'**Entité Essentielle (EE)** ou **Entité Importante (EI)**, selon son secteur d'activité et sa taille ?
- Les exigences NIS 2 ont-elles été **intégrées formellement dans le socle de sécurité réglementaire** de l'organisation ?
- La direction a-t-elle bénéficié (ou prévu) d'un **diagnostic cyber** (ANSSI / MesServicesCyber) pour identifier ses lacunes et lancer sa mise en conformité ?

---

## 3. Gestion de crise et remédiation

*Rôles : Sponsor exécutif, RSSI, DSI*

- L'entreprise a-t-elle défini une **stratégie de remédiation** permettant de reprendre le contrôle d'un SI compromis ?
- L'organisation organise-t-elle régulièrement des **exercices de gestion de crise cyber** pour entraîner ses équipes dirigeantes et opérationnelles ?
- Le plan de réponse à incident intègre-t-il la séquence **E3R** de l'ANSSI ?
  - **Endiguement** — freiner la progression de l'attaquant et gagner du temps
  - **Éviction** — reprendre le contrôle de l'administration IT (cœur de confiance, Active Directory)
  - **Éradication** — nettoyer intégralement les systèmes métiers des emprises résiduelles
  - **Reconstruction** — rebâtir les fondations de manière *security-by-design*
- La direction a-t-elle défini des **critères d'arbitrage** du plan de remédiation, entre **urgence de redémarrage** et **coûts induits à long terme** ?

> La doctrine ANSSI structure la remédiation en **trois volets — stratégique, opérationnel, technique**. E3R en est la séquence ; les critères d'arbitrage relèvent du volet stratégique (décision Direction).

---

## 4. Études de cas — fiches réflexes EBIOS

*Usage : tester la résilience de l'entreprise face à des scénarios réels et éprouvés. Déjà présents dans le code (`case_studies`), enrichis ici de questions d'audit.*

### Marriott — fuite massive de données (500 M de clients)
- Les bases contenant des **données à caractère personnel** sont-elles identifiées comme **biens supports critiques** ?
- Les **impacts juridiques (RGPD)** et d'**image** d'une fuite ont-ils été évalués ?
- Des mesures de **chiffrement** et de **détection** adéquates sont-elles en place ?

### Pathé — arnaque au président
- Face à des escrocs cherchant un profit financier par **usurpation d'identité de dirigeants**, existe-t-il des mesures de **gouvernance** (procédure de validation des virements, double signature) ?
- Une **sensibilisation à l'ingénierie sociale** est-elle menée ?

### Société de biotechnologies — espionnage et sabotage R&D
- Si l'entreprise possède un **savoir-faire sensible (R&D)**, le scénario d'un concurrent volant ces informations **via un prestataire informatique ou un partenaire** a-t-il été modélisé ?
- Des mesures spécifiques sont-elles **imposées aux fournisseurs** (clauses contractuelles strictes, audits de prestataires, matériel de maintenance maîtrisé par la DSI) pour éviter un **arrêt de production par sabotage** ?

---

## 5. RGPD — intégration dans l'audit cyber

*Rôles : DPO, Juridique, RSSI*

### Inventaire et cartographie
- Existe-t-il un **registre des activités de traitement** à jour, tenu par le responsable de traitement **et ses sous-traitants** ?
- Les **données à caractère personnel** sont-elles explicitement qualifiées de **valeurs métier critiques** lors du cadrage ?

### Mesures techniques et organisationnelles
- Les principes de **protection dès la conception (by design) et par défaut** sont-ils appliqués ?
- Les mesures d'atténuation concrètes sont-elles déployées : **minimisation**, **pseudonymisation**, **chiffrement** ?
- Existe-t-il un processus de **test et d'évaluation réguliers de l'efficacité** de ces mesures (confidentialité, intégrité, disponibilité) ?

### Écosystème et sous-traitants
- Les contrats prestataires prévoient-ils des **garanties suffisantes** en matière de sécurité ?
- Les sous-traitants **documentent-ils leurs mesures**, tiennent-ils un **registre de leurs catégories de traitement**, et s'engagent-ils à **assister l'entreprise lors d'audits et inspections** ?

### Violations de données
- La procédure de réponse à incident permet-elle d'**identifier immédiatement** qu'une violation de données personnelles a eu lieu ?
- Un processus formel de **notification à la CNIL** (72 h) et de **communication aux personnes concernées** (si risque élevé) est-il en place ?
- L'entreprise tient-elle une **documentation interne de TOUTES les violations** — y compris non notifiables — avec leurs conséquences et les actions de remédiation ? *(RGPD Art. 33.5)*

### Impacts juridiques et image
- Lors de l'évaluation de la **gravité** d'un événement redouté, les **impacts juridiques** (sanctions CNIL) et d'**image/confiance** sont-ils systématiquement intégrés ?

---

## 6. AIPD / PIA — contenu minimal exigé et obligations organisationnelles

*Rôle : DPO (obligatoirement consulté)*

### Les 4 étapes de rédaction (contenu minimal RGPD Art. 35.7)
1. **Description systématique** des opérations de traitement et de leurs finalités — y compris l'intérêt légitime poursuivi, en tenant compte de la nature, la portée et le contexte.
2. **Évaluation de la nécessité et de la proportionnalité** au regard des finalités.
3. **Évaluation des risques pour les droits et libertés** — origine, nature, particularité, probabilité d'occurrence et gravité.
4. **Mesures de traitement des risques** — garanties, mécanismes et mesures de sécurité prévus pour atténuer les risques et démontrer la conformité.

### Obligations organisationnelles ⚠️ *(absentes du module AIPD actuellement codé)*
- **Consulter le DPO** lors de la réalisation de l'analyse, s'il en existe un.
- **Recueillir l'avis des personnes concernées** (ou de leurs représentants) lorsque approprié, sans compromettre la sécurité ni le secret des affaires.
- **Se référer aux listes CNIL** des traitements nécessitant obligatoirement une AIPD — et de ceux qui en sont dispensés.
- **Saisir l'autorité de contrôle (CNIL)** — obligatoire **avant** de débuter le traitement si l'analyse révèle un **risque élevé résiduel** que l'entreprise ne peut atténuer *(RGPD Art. 36)*.
- **Mettre à jour l'AIPD** dans le temps — au minimum à chaque changement du niveau de risque.

### Déclenchement
L'AIPD est menée **par le responsable de traitement**, **avant** la mise en œuvre du traitement, en particulier en cas de nouvelles technologies susceptibles d'engendrer un **risque élevé** pour les droits et libertés.

---

## 7. Contrôles techniques référencés

Mappings explicites à conserver lors de la construction des `workflow.yaml` :

| Sujet | Référence | État dans le code |
|---|---|---|
| Gestion continue des vulnérabilités | **CIS 7**, NIST **ID.RA-01** | booléen `vulnerabilities_active` — mapping à ajouter |
| Journaux d'audit (collecte et conservation) | **CIS 8** | booléen `logging_active` — mapping à ajouter |
| Évaluation des fournisseurs avant acquisition | NIST **ID.RA-10** | TPRM — mapping à ajouter |
| Inventaire des données, systèmes, matériels et logiciels sur tout le cycle de vie | NIST CSF (ID.AM) | `assets_support` — mapping à ajouter |

---

## Sources (fournies par Dorian)

| Réf | Source |
|---|---|
| [1] | Règlement (UE) 2016/679 — RGPD (EUR-Lex) |
| [2] | ANSSI — Support du stagiaire EBIOS RM (`cyber.gouv.fr/documents/478`) |
| [3] | ANSSI — Correction étude de cas EBIOS RM (`cyber.gouv.fr/documents/479`) |
| [4] | NIST SP 800-53 Rev. 5 — Security and Privacy Controls |
| [5] | CNIL — cnil.fr (boîte à outils conformité, modèles PIA) |
| [6] | ANSSI — Formation EBIOS Risk Manager |
| [7] | MesServicesCyber — services et ressources cyber |
| [8] | ANSSI — Piloter la remédiation d'un incident cyber |
| [9] | ANSSI — Support de formation EBIOS RM (`cyber.gouv.fr/documents/477`) |
| [10] | ANSSI — Volet stratégique : cyberattaques et remédiation |
| [11] | NIST — Incident Response 4-Step Life Cycle |
| [12] | MesServicesCyber — NIS 2 |
| [13] | NIST CSWP 29 — C-SCRM |
