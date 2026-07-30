# Livrables produits par GREEN SHIELD — deux missions d'exemple

Ces fichiers sont la **sortie brute de l'application**, sans retouche. Deux missions ont été menées
de bout en bout, du cadrage à la remise, puis exportées : une mission de **conseil** et une mission
de **conformité**. Ils sont ici pour qu'on puisse juger le produit sans l'installer.

**Cinq vues sur la même mission** — un consultant ne restitue pas la même chose à un COMEX, à un
comité de suivi ou dans un registre opposable. L'application produit les cinq, alimentées par les
mêmes données. *Téléchargez le `.html` et ouvrez-le : GitHub affiche le code source, pas la page.*

| Vue | Ce qu'elle montre | Mission conseil | Mission GRC |
|---|---|---|---|
| **Rapport de mission** | Le document complet : page de garde, sommaire, 13 chapitres | [`.html`](conseil/05-rapport-d-audit.html) · [`.docx`](conseil/05-rapport-d-audit.docx) | [`.html`](grc/05-rapport-d-audit.html) · [`.docx`](grc/05-rapport-d-audit.docx) |
| **Synthèse direction** | Une page : avancement, écarts prioritaires, charges | [`.html`](conseil/06-synthese-direction.html) | [`.html`](grc/06-synthese-direction.html) |
| **Tableau de restitution** | Écran de clôture : diagnostiqué face à ce qu'il reste à faire | [`.html`](conseil/07-tableau-de-restitution.html) | [`.html`](grc/07-tableau-de-restitution.html) |
| **Registre de conformité** | Écarts organisationnels avec preuve, registre des tiers | [`.html`](conseil/08-registre-de-conformite.html) | [`.html`](grc/08-registre-de-conformite.html) |
| **Cartographie du risque** | Matrice gravité × vraisemblance, classement des tiers | [`.html`](conseil/09-cartographie-du-risque.html) | [`.html`](grc/09-cartographie-du-risque.html) |

Chaque mission est également exportée en **Markdown**, cinq livrables réglementaires (NDA, EBIOS RM,
PSSI/PRI, AIPD, rapport d'audit) qui se lisent directement dans GitHub — voir le tableau détaillé
plus bas.

> **Données entièrement fictives.** « Vernier Composites SAS » et « Banque Aurore SA » n'existent
> pas. Aucune donnée de mission réelle ne se trouve dans ce dépôt, ni dans son historique : les
> missions vivent hors du dépôt (`GREENSHIELD_DATA_DIR`, par défaut `%APPDATA%\GreenShield\projects`).

## Ce que ces deux missions démontrent

Le point n'est pas qu'un générateur de documents produise des documents. C'est que **les deux volets
ne répondent pas à la même question**, et que l'outil le sait.

| | Volet **conseil** | Volet **GRC** |
|---|---|---|
| Question posée | Quel risque ce client court-il ? | Cette exigence est-elle respectée ? |
| Méthode | EBIOS RM, ateliers 1 à 5 (ANSSI) | Check-list du référentiel + registre réglementaire |
| Unité de travail | le scénario opérationnel | l'exigence et sa preuve |
| Criticité d'un tiers | ratio ANSSI **(dépendance × pénétration) / (maturité × confiance)** | **aucun score** — DORA et NIS2 ne se réclament pas d'EBIOS RM |
| Ce qui fait foi | la vraisemblance du scénario, argumentée | la preuve rattachée à l'exigence |
| Verdict rendu | une priorisation | un écart, ou son absence |
| Livrable central | analyse de risque + plan de traitement | registre de conformité + écarts opposables |

Cette séparation est une décision documentée, pas un effet de bord : appliquer un scoring de risque
à un référentiel réglementaire reviendrait à lui inventer une exigence qu'il ne porte pas. Le
raisonnement complet est dans [../spec-refonte-grc-consulting.md](../spec-refonte-grc-consulting.md)
§14.1bis, avec sa justification chiffrée.

### Le ratio ANSSI, sur les tiers réels de la mission conseil

La moyenne arithmétique employée au départ compressait les écarts et empêchait donc de prioriser —
ce qui est pourtant l'objet même de l'atelier 3. Le ratio les rouvre :

| Tiers | Dép. | Pén. | Mat. | Conf. | Ratio | Criticité |
|---|---:|---:|---:|---:|---:|---|
| Prestataire maintenance automates (VPN permanent) | 5 | 5 | 2 | 3 | **4,17** | Critique |
| Infogéreur poste de travail | 4 | 4 | 3 | 4 | 1,33 | Moyen |
| Hébergeur Microsoft 365 | 5 | 4 | 5 | 5 | 0,80 | Faible |
| Fournisseur de résines (portail EDI) | 3 | 2 | 3 | 3 | 0,67 | Faible |
| Cabinet d'expertise comptable | 2 | 1 | 3 | 4 | 0,17 | Faible |

Le tiers le plus critique n'est ni le plus gros ni le plus visible : c'est celui qui cumule un accès
large et une maturité faible. Il est aussi celui que le scénario SO-02 désigne comme vecteur — les
deux analyses se recoupent, ce qui est le signe qu'elles sont justes.

### Le registre DORA, sur les prestataires de la mission GRC

Quatre exigences par prestataire, aucun score : inscription au registre d'information (Art. 28.3),
clauses contractuelles obligatoires (Art. 30), stratégie de sortie documentée et testable,
évaluation avant acquisition (NIST ID.RA-10).

| Prestataire | Exigences satisfaites | Écart |
|---|---:|---|
| Éditeur core banking *(critique)* | 2 / 4 | Clauses DORA absentes du contrat ; sortie non documentée |
| Opérateur d'interconnexion STET | 4 / 4 | — |
| Hébergeur du site de repli | 0 / 4 | Quatre exigences ouvertes |
| Prestataire d'infogérance poste de travail | 0 / 4 | Quatre exigences ouvertes |

**Un prestataire sur quatre sans écart.** Ce chiffre est celui que le responsable conformité a
lui-même déclaré en entretien — l'outil restitue le terrain, il ne le corrige pas.

Cette séparation traverse les cinq vues, pas seulement le rapport complet : le **registre de
conformité** GRC n'affiche aucune colonne « Ratio », et sa **cartographie du risque** classe les
tiers par taux de conformité plutôt que par criticité, avec la même mention explicite qu'aucun
score n'est produit. Vérifiable en ouvrant [grc/08-registre-de-conformite.html](grc/08-registre-de-conformite.html)
et [grc/09-cartographie-du-risque.html](grc/09-cartographie-du-risque.html) côte à côte avec leurs équivalents
[conseil/08-registre-de-conformite.html](conseil/08-registre-de-conformite.html) et
[conseil/09-cartographie-du-risque.html](conseil/09-cartographie-du-risque.html).

## Les fichiers

### Mission conseil — Vernier Composites SAS
PME industrielle fictive, 204 salariés, R&D composites aéronautiques non brevetée.
100 % du parcours renseigné · 85 h consommées sur 18 jours vendus.

| Livrable | Ce qu'il contient |
|---|---|
| [01 · Accord de confidentialité](conseil/01-accord-de-confidentialite.md) · [`.docx`](conseil/01-accord-de-confidentialite.docx) | NDA, engagements réciproques |
| [02 · Analyse de risque EBIOS RM](conseil/02-analyse-de-risque-ebios-rm.md) · [`.docx`](conseil/02-analyse-de-risque-ebios-rm.docx) | Patrimoine, 4 événements redoutés, 3 sources de risque, 4 scénarios, écosystème, plan d'action |
| [03 · PSSI & plan de reprise](conseil/03-pssi-et-plan-de-reprise.md) · [`.docx`](conseil/03-pssi-et-plan-de-reprise.docx) | RTO/RPO, politique de sauvegarde, séquence E3R de l'ANSSI, volet stratégique d'arbitrage Direction |
| [04 · AIPD RGPD](conseil/04-aipd-rgpd.md) · [`.docx`](conseil/04-aipd-rgpd.docx) | Registre Art. 30, les 4 volets d'analyse, les 5 obligations de procédure |
| [05 · Rapport d'audit](conseil/05-rapport-d-audit.md) · [`.html`](conseil/05-rapport-d-audit.html) · [`.docx`](conseil/05-rapport-d-audit.docx) | 13 chapitres, de la synthèse direction aux signatures |

### Mission GRC — Banque Aurore SA
Établissement de crédit fictif, 640 collaborateurs, service de paiement instantané soumis à DORA
et entité essentielle NIS2. 100 % du parcours renseigné · 111 h sur 34 jours vendus.

| Livrable | Ce qu'il contient |
|---|---|
| [01 · Accord de confidentialité](grc/01-accord-de-confidentialite.md) · [`.docx`](grc/01-accord-de-confidentialite.docx) | NDA |
| [02 · Analyse de risque EBIOS RM](grc/02-analyse-de-risque-ebios-rm.md) · [`.docx`](grc/02-analyse-de-risque-ebios-rm.docx) | Scénarios de chaîne d'approvisionnement, registre des prestataires |
| [03 · PSSI & plan de reprise](grc/03-pssi-et-plan-de-reprise.md) · [`.docx`](grc/03-pssi-et-plan-de-reprise.docx) | RTO 2 h sur la fonction critique DORA, bascule testée trimestriellement, volet stratégique d'arbitrage Direction |
| [04 · AIPD RGPD](grc/04-aipd-rgpd.md) · [`.docx`](grc/04-aipd-rgpd.docx) | Scoring de crédit, décision automatisée Art. 22, **consultation préalable CNIL Art. 36** déclenchée par un risque résiduel élevé |
| [05 · Rapport d'audit](grc/05-rapport-d-audit.md) · [`.html`](grc/05-rapport-d-audit.html) · [`.docx`](grc/05-rapport-d-audit.docx) | Écarts ISO 27001 avec preuve, registre DORA, plan de remédiation |

## Ce que ces documents ne font jamais

C'est le point qui a demandé le plus de travail, et il se vérifie dans les fichiers :

- **Aucune valeur n'est inventée pour combler un vide.** Un champ non saisi apparaît comme non
  saisi. Il n'y a ni « N/A » masqué, ni chapitre annoncé puis laissé vide, ni référentiel supposé.
- **Chaque constat est attribuable.** Le chapitre 2.1 du rapport liste les entretiens conduits, par
  rôle et sans nom — ISO 19011 pour l'attribution, minimisation RGPD pour l'absence d'identité.
- **La couverture technique est annoncée telle quelle.** Ces deux missions n'ont pas exécuté de scan
  automatisé : les rapports écrivent que 0 % des constats reposent sur une mesure technique. Aucune
  plateforme GRC ne dit ça à son client ; c'est pourtant l'information la plus honnête du document.
- **Aucun texte de norme n'est recopié.** Identifiants de contrôles et intitulés courts reformulés
  seulement — le texte ISO est sous copyright AFNOR.
- **Un modèle de langage n'écrit jamais dans un champ structuré.** Le copilote intégré produit du
  texte libre affiché à l'écran ; aucun formulaire n'est auto-rempli par une réponse d'IA. Ces
  livrables ne contiennent donc pas une ligne générée par un LLM.

## Comment ces fichiers ont été produits

L'application tourne en local, sans réseau. Les deux missions ont été remplies via son API, puis
exportées par ses propres routes (`/api/projects/{id}/export/{type}` et `/report.docx`). Le
protocole rejouable et sa grille de notation sont dans
[../protocole-recette.md](../protocole-recette.md) ; les résultats, défauts trouvés et corrections
apportées dans [../recette-2026-07-29.md](../recette-2026-07-29.md).

## Cinq vues, trois formats

**Cinq vues** parce qu'un consultant ne restitue pas la même chose selon l'auditoire — un COMEX ne
lit pas un registre de preuves, une matrice de risque ne remplace pas un plan de traitement daté.
Chacune est un export indépendant (`GET /api/projects/{id}/report/...`), alimenté par les mêmes
données de mission, jamais par du texte généré à la volée.

| Vue | Sert à | Contenu dérivé de |
|---|---|---|
| Rapport de mission | Archiver, transmettre l'intégralité de la mission | Les 13 chapitres du parcours |
| Synthèse direction | Ouvrir une réunion de clôture avec un décideur | La synthèse rédigée par le consultant (phase 6) + le plan de traitement |
| Tableau de restitution | Projeter en séance : diagnostic ⟷ mesures | Événements/scénarios/écarts vs remédiations |
| Registre de conformité | Documenter un audit, dossier opposable | Exigences organisationnelles + registre des tiers |
| Cartographie du risque | Ouvrir la discussion sur les priorités | Matrice gravité × vraisemblance + classement des tiers |

**Trois formats** parce que chacun sert un usage différent :

| Format | Pour quoi | Mise en page |
|---|---|---|
| **`.html`** | Le livrable remis au client. Autonome, aucune ressource externe, donc lisible hors ligne. Imprimable en A4 depuis le navigateur, et donc convertible en PDF sans outil supplémentaire. | Page de garde, tableaux tramés, pastilles de sévérité — thème clair pour les documents (rapport, synthèse, registre), thème écran pour les vues de restitution (tableau, cartographie) |
| **`.docx`** | Quand le client veut annoter ou reprendre le texte. Disponible pour les 5 livrables (rapport, NDA, EBIOS RM, PSSI/PRI, AIPD), pas seulement le rapport. | Page de garde pleine hauteur, sommaire, tableaux à largeurs de colonnes réelles, logo personnalisable (Réglages) |
| **`.md`** | La lecture directe dans GitHub ou un éditeur, et le versionnement — un diff Markdown est lisible, un diff Word ne l'est pas. | Markdown pur : titres, tableaux, emphase. Aucun HTML, aucun CSS. |

Le choix du PDF passe par l'impression navigateur et non par une bibliothèque de rendu : la première
règle du projet interdit toute dépendance native obligatoire en local, et une chaîne PDF Python en
est une.
