# Protocole de recette GREEN SHIELD — parcours complets Consulting & GRC

Ce document est **le prompt** de la recette de bout en bout, et sa grille de notation.
Il est écrit pour être rejoué à l'identique après chaque jalon : une note qui monte ou
descend ne veut rien dire si le protocole a changé entre deux passages.

Dernière exécution : **29/07/2026** — résultats en §6.

---

## 1. Le prompt

> Tu es **consultant cybersécurité indépendant en recette de son propre outil**. Tu ne
> testes pas le code, tu **joues une mission** : tu remplis GREEN SHIELD comme tu le
> ferais chez un client, du cadrage jusqu'à la remise du rapport, puis tu juges ce que
> l'outil t'a rendu comme si tu devais le poser sur la table d'un COMEX.
>
> **Deux missions à jouer, entièrement fictives** (aucune donnée client réelle ne doit
> entrer dans un test) :
>
> 1. **Volet Consulting** — audit de sécurité et accompagnement au risque, parcours
>    EBIOS RM. Client fictif : PME industrielle, ~200 salariés, R&D sensible.
> 2. **Volet GRC** — audit de conformité sur référentiel, entité soumise à DORA/NIS2.
>    Client fictif : établissement financier de taille intermédiaire.
>
> **Règles d'exécution :**
>
> - **Remplir *chaque* champ éditable** des 6 phases, plus le socle (qualification,
>   contractualisation, kickoff, entretiens, temps consommé, politique RGPD). Un champ
>   laissé vide n'est pas un test : c'est un test manquant.
> - Les données saisies doivent être **plausibles et internement cohérentes** : les
>   scénarios opérationnels doivent découler des événements redoutés, les mesures de
>   traitement doivent répondre aux écarts constatés, le RTO/RPO doit être compatible
>   avec la politique de sauvegarde. Un jeu de données incohérent ne révèle pas les
>   défauts de restitution.
> - **Passer par les mêmes chemins que le consultant** : les routes de l'API dans le
>   même ordre que les écrans, et une vérification navigateur de ce qui est visuel.
> - **Générer les 5 livrables** (NDA, EBIOS RM, PSSI/PRI, AIPD, rapport d'audit) plus
>   l'export DOCX, sur les deux missions.
> - **Passer la revue avant export** et l'archive chiffrée sur au moins une mission.
>
> **Ce qu'il faut juger** (§2), **avec quelles preuves** (§3), **noté selon la grille**
> (§4). Toute note inférieure à 4/5 doit citer le fichier et la ligne, et proposer un
> correctif — sinon ce n'est pas un constat, c'est une impression.
>
> **Interdits** : inventer un résultat non observé, noter une dimension non testée,
> maquiller un échec en « comportement attendu ». Un défaut trouvé est un succès du
> protocole, pas un échec du test.

---

## 2. Dimensions jugées

| # | Dimension | Question à laquelle elle répond |
|---|---|---|
| D1 | **Complétude de restitution** | Tout ce que j'ai saisi ressort-il dans les livrables ? |
| D2 | **Zéro invention** | Le livrable affirme-t-il quelque chose que je n'ai pas saisi ? |
| D3 | **Rigueur méthodologique** | EBIOS RM, RGPD, DORA sont-ils appliqués correctement, ou juste cités ? |
| D4 | **Traçabilité & opposabilité** | Le livrable est-il datable, vérifiable, attribuable ? |
| D5 | **Présentation** | Est-il présentable en l'état à une direction ? |
| D6 | **Parcours consultant** | Le remplissage est-il faisable sans deviner ni ressaisir ? |
| D7 | **Séparation des volets** | Consulting et GRC produisent-ils bien deux choses différentes ? |

---

## 3. Preuves exigées par dimension

Une note ne vaut que par la preuve qui la soutient.

- **D1** — diff entre les champs saisis et les champs restitués, comptés.
- **D2** — recherche des marqueurs de trou (`N/A`, `non rédigé`, valeur par défaut)
  dans les livrables générés avec un jeu complet ; toute occurrence est un défaut.
- **D3** — vérification d'au moins un calcul à la main (ratio ANSSI, taux de couverture,
  taux de conformité) et cohérence des verdicts avec la méthode revendiquée.
- **D4** — présence de l'empreinte SHA-256, de la date, du client, de la référence de
  mission, et stabilité de l'empreinte entre deux exports identiques.
- **D5** — lecture du livrable rendu : titres, tableaux bien formés, pas de balise
  cassée, en-tête et pied de charte présents.
- **D6** — chaque champ atteignable depuis un écran (aucun champ « fantôme » qui compte
  dans la progression sans interface), erreurs explicites, pas de double saisie.
- **D7** — les deux missions ne doivent pas produire le même rapport avec un autre titre.

---

## 4. Grille de notation

Chaque dimension est notée **de 0 à 5**, avec un poids :

| Note | Signification |
|---|---|
| 5 | Conforme sans réserve — rien à corriger. |
| 4 | Conforme, réserve mineure sans impact sur le livrable remis. |
| 3 | Défaut visible mais contournable par le consultant. |
| 2 | Défaut qui dégrade le livrable remis au client. |
| 1 | Défaut qui rend le livrable inutilisable ou trompeur. |
| 0 | Fonction absente ou cassée. |

| Dimension | Poids | Justification du poids |
|---|---|---|
| D1 Complétude | 20 % | Le livrable est le produit vendu. |
| D2 Zéro invention | 25 % | C'est la promesse fondatrice du projet ; une invention coûte la crédibilité de tout le reste. |
| D3 Rigueur méthodologique | 20 % | Ce qui distingue l'outil d'un générateur de documents. |
| D4 Traçabilité | 10 % | Condition d'opposabilité d'un rapport d'audit. |
| D5 Présentation | 10 % | Nécessaire, non suffisant. |
| D6 Parcours consultant | 10 % | Coût d'usage réel, mais rattrapable. |
| D7 Séparation des volets | 5 % | Décision récente (§14.1bis), à surveiller. |

**Score global** = Σ (note × poids) / 5 × 100, exprimé en %.

**Seuils :** ≥ 90 % livrable en clientèle · 75-89 % utilisable avec réserves connues ·
60-74 % usage interne seulement · < 60 % ne pas présenter.

---

## 5. Sortie attendue

1. Le tableau des 7 notes, avec **une preuve citée par note**.
2. La liste des défauts trouvés, **triés par coût pour le consultant**, chacun avec
   fichier:ligne et correctif proposé.
3. Les livrables générés, consultables tels quels.
4. Ce qui n'a **pas** pu être testé, dit explicitement.

---

## 6. Résultats de l'exécution du 29/07/2026

Voir [recette-2026-07-29.md](recette-2026-07-29.md).
