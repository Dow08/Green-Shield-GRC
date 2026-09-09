"""Cohérence entre le modèle de mission et les écrans de saisie.

Incident du 09/09/2026 — quatre champs du modèle étaient réclamés par le
vérificateur de complétude (`modules/revue_export.py`) et imprimés dans le
rapport client (`modules/report_builder.py`), **sans qu'aucun formulaire de
l'interface ne permette de les remplir** :

  * `steps.ebios.redoute_events[].source` — aucun champ dans PhaseEbios ;
  * `steps.ebios.operational_scenarios[].date_revue` — idem ;
  * `steps.resilience.e3r.eviction` / `.eradication` — PhaseResilience
    n'offrait que 2 des 4 étapes de la séquence ANSSI ;
  * `steps.traitement.quick_wins` — affiché en lecture seule, jamais éditable.

Conséquence : le consultant voyait le vérificateur réclamer indéfiniment des
champs impossibles à saisir, et des chapitres du rapport sortaient vides.

**Pourquoi la suite ne l'a pas vu** : `modules/demo_fixture.py` pré-remplit
ces champs pour la mission de démonstration. Tous les tests travaillent donc
sur des données déjà peuplées — le trou de saisie reste strictement invisible
tant qu'on ne regarde pas l'interface elle-même.

Ce test regarde l'interface. Il inventorie les clés du modèle de mission puis
exige que chacune dispose d'un moyen de saisie dans `web/src/`.

**Correctif du 09/09/2026 — indexation par (étape, clé).** La première version
raisonnait sur le *nom* de la clé et cherchait la preuve dans tout `web/src/` :
deux clés homonymes appartenant à deux étapes différentes se couvraient donc
mutuellement, et une quinzaine de noms passaient grâce à un homonyme saisi
ailleurs. Le cas prouvé : `steps.evaluation.soa[].date_revue` n'a aucun champ
dans SoaPanel, mais passait grâce au `date_revue` des scénarios EBIOS. Le test
raisonne désormais sur le **couple (étape, clé)** et ne cherche la preuve de
saisie que dans les fichiers de l'étape concernée (`_FICHIERS_PAR_ETAPE`).

Limites assumées, à lire avant d'ajouter une exclusion :
  * l'analyse est **textuelle** (pas d'AST TypeScript) — elle prouve qu'un
    champ de saisie mentionne la clé, pas que ce champ soit atteignable,
    branché sur la bonne donnée, ni que la valeur soit bien enregistrée ;
  * la portée par étape vaut ce que vaut `_FICHIERS_PAR_ETAPE` : un panneau
    de saisie déplacé dans un fichier non répertorié fait échouer le test
    (bruit visible), un panneau étranger ajouté par erreur à la liste d'une
    étape rouvre un trou (silence). C'est le seul endroit à relire quand on
    découpe ou renomme un composant de phase ;
  * elle ne couvre que `steps.*` — le socle de mission (`socle.*`) et le volet
    GRC (`grc.*`) ont leurs propres panneaux, hors du périmètre de l'incident.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from modules import demo_fixture
from modules.projects.crud import create_empty_state

RACINE = Path(__file__).resolve().parents[2]
WEB_SRC = RACINE / "web" / "src"
TYPES_TS = WEB_SRC / "types.ts"

# ---------------------------------------------------------------------------
# Exclusions — couples (étape, clé) qui n'ont légitimement aucun champ de saisie.
#
# Clé de la table : "<étape>.<clé>", ou "*.<clé>" quand l'absence de saisie vaut
# pour toutes les étapes où le nom apparaît. Depuis le 09/09/2026 l'exclusion
# est **nominative par étape** : exclure `date_revue` tout court dispenserait
# aussi bien la SoA que les scénarios EBIOS, alors que seule la première a une
# raison de s'en passer.
#
# Chaque entrée porte la raison pour laquelle l'absence de saisie est normale.
# Sans cette justification écrite, la liste deviendrait la décharge où l'on
# jette les vrais trous — et l'incident du 09/09/2026 a montré ce que coûte un
# champ que personne ne peut remplir. Une exclusion sans raison vérifiable doit
# être refusée en revue.
# ---------------------------------------------------------------------------
EXCLUSIONS: dict[str, str] = {
    # --- Sorties du moteur d'audit technique : produites par le serveur ------
    "evaluation.technical_results": (
        "Résultat du scan technique (modules/auditcraft_grc). Écrit par le "
        "moteur, jamais par le consultant : un champ de saisie ici "
        "permettrait de maquiller un constat technique."
    ),
    "collecte.files": (
        "steps.collecte.files — liste alimentée par le téléversement de "
        "fichiers de configuration (route /collecte). La saisie existe, mais "
        "c'est un sélecteur de fichiers : le nom de la clé n'apparaît jamais "
        "dans un champ de formulaire."
    ),
    # --- Valeurs calculées par le serveur ------------------------------------
    "tprm.score": (
        "Note de criticité d'un tiers, calculée côté serveur (ratio ANSSI, "
        "modules/tprm.py). Le navigateur ne la calcule ni ne la saisit — "
        "commentaire explicite de types.ts:Tiers."
    ),
    "tprm.rating": (
        "Classe de criticité d'un tiers (Critique / Élevé / Moyen / Faible), "
        "déduite de `score` par le serveur. La saisir permettrait de "
        "contredire le calcul affiché juste à côté."
    ),
    "tprm.methode": (
        "Trace la formule ayant produit `score` (ratio_anssi / "
        "moyenne_historique). Métadonnée de calcul, pas une donnée d'audit."
    ),
    # --- Identifiants engendrés par l'interface ------------------------------
    "cadrage.id": (
        "steps.cadrage.assets_metier[].id / assets_support[].id — vérifié le "
        "09/09/2026 : PhaseCadrage.tsx engendre ces identifiants avec "
        "`nextId(\"VM\", …)` / `nextId(\"BS\", …)` (lignes 107, 252, 297, 447) "
        "à l'ajout d'un actif. Le consultant ne les tape pas, et un champ "
        "libre casserait l'unicité sur laquelle s'appuient les liens "
        "actif ↔ scénario. Cas propre à cette phase : dans EBIOS, l'ID *est* "
        "saisi (`ER-05`, `SO-02`…) et doit le rester."
    ),
    # --- Libellés issus des référentiels, jamais de la mission ---------------
    "evaluation.referentiel_name": (
        "steps.evaluation.manual_controls[].referentiel_name — nom du "
        "référentiel d'origine d'un contrôle, écrit par le serveur à la "
        "création de la mission depuis api/frameworks/*.yaml "
        "(modules/projects/crud.py). Correction du 09/09/2026 : ce champ "
        "n'est pas « recopié à la saisie » comme l'affirmait la justification "
        "précédente — le consultant ne le voit jamais, et report_builder.py:838 "
        "retombe sur `referentiel_id` quand il est vide. Le rendre éditable "
        "laisserait renommer un référentiel normatif dans une mission."
    ),
    "evaluation.titre": (
        "steps.evaluation.soa[].titre — intitulé de la mesure de l'Annexe A "
        "d'ISO/IEC 27001:2022, posé par soa.entrees_par_defaut() depuis "
        "api/frameworks/soa_iso27001.yaml. Texte normatif, non modifiable."
    ),
    "evaluation.theme": (
        "steps.evaluation.soa[].theme — thème Annexe A (Organisationnel / "
        "Personnel / Physique / Technologique), même origine que `titre`. "
        "Texte normatif, non modifiable ; SoaPanel s'en sert pour regrouper "
        "les 93 contrôles, pas pour les laisser reclasser."
    ),
    # --- Choisis à la création de la mission, pas dans les phases ------------
    "cadrage.framework_ids": (
        "Référentiels actifs, choisis dans ProjectWizard (cases à cocher "
        "`selectedFrameworks`) au moment de créer la mission. La saisie "
        "existe, mais elle est hors des écrans de la phase Cadrage et le nom "
        "de la clé n'apparaît qu'à l'envoi du formulaire."
    ),
    "cadrage.framework_id": (
        "Référentiel « pivot » — dérivé par le serveur du premier élément de "
        "`framework_ids` (modules/projects/crud.py). Jamais saisi seul."
    ),
    "cadrage.framework_name": (
        "Libellé du référentiel pivot, recopié par le serveur depuis "
        "api/frameworks/*.yaml en même temps que `framework_id`."
    ),
    # --- Champs dormants : déclarés, jamais lus, jamais saisis --------------
    "tprm.preuve": (
        "steps.tprm.tiers[].exigences[].preuve — relevé le 09/09/2026 : "
        "initialisé à \"\" par tprm.exigences_par_defaut(), lu par aucun "
        "rapport ni par revue_export.py, et PhaseTprm n'offre que la case "
        "`satisfait`. Exclu parce qu'il n'est réclamé nulle part : rien ne "
        "sort vide du rapport et le vérificateur ne le demande pas. Le jour "
        "où une exigence tierce devra être justifiée par une preuve, c'est "
        "un champ de saisie qu'il faut ajouter — pas cette ligne à garder."
    ),
    "evaluation.date_revue": (
        "steps.evaluation.soa[].date_revue — trou **révélé** par l'indexation "
        "par étape du 09/09/2026 : SoaPanel.tsx saisit `statut`, "
        "`justification`, `document_reference` et `owner`, mais pas la date "
        "de revue ; l'ancienne version du test le laissait passer grâce au "
        "`date_revue` des scénarios EBIOS. Champ dormant, vérifié ligne à "
        "ligne : initialisé à \"\" par soa.entrees_par_defaut() "
        "(modules/soa.py:43), lu ni par revue_export.py (qui ne regarde que "
        "`applicable` via soa.etat()), ni par report_builder.py, ni par "
        "report_docx.build_soa_docx() (dont le tableau n'imprime que code, "
        "titre, applicabilité, statut et justification). Aucun rapport ne "
        "sort vide, le vérificateur ne le réclame pas. Le jour où le cycle "
        "de revue de la SoA devra être tenu, la correction est un champ date "
        "dans SoaPanel à côté de `owner` — pas le maintien de cette ligne."
    ),
    "restitution.remediation_plan": (
        "steps.restitution.remediation_plan — vérifié le 09/09/2026 : cette "
        "liste est initialisée à [] et n'est lue nulle part (ni "
        "revue_export.py, ni report_builder.py, ni report_docx.py). Le plan "
        "de traitement réel vit dans steps.traitement.remediations. À "
        "supprimer du modèle plutôt qu'à saisir — exclusion à revoir le jour "
        "où ce champ reprend un sens."
    ),
    # --- Marqueur d'état de l'assistant de mission ---------------------------
    "*.validated": (
        "Marqueur « étape validée par le consultant », posé par le bouton de "
        "validation de phase, pas par un champ de formulaire. Vaut pour "
        "toutes les étapes, d'où le joker."
    ),
}


# ---------------------------------------------------------------------------
# 1. Inventaire des clés du modèle de mission, indexé par (étape, clé)
# ---------------------------------------------------------------------------
# Le couple, et non le nom seul : c'est tout le correctif du 09/09/2026. Un
# `owner` saisissable dans PhaseCadrage ne dit rien du `owner` de la SoA, et
# un `statut` saisissable dans PhaseEbios ne dit rien de celui d'un contrôle.
def _cles_depuis_etat(etat: dict, etape: str, prefixe: str,
                      inventaire: dict[tuple[str, str], set[str]]) -> None:
    """Parcours récursif d'un état de mission : chaque clé rencontrée est
    indexée par (étape, nom), avec le(s) chemin(s) où on l'a vue (pour le
    message d'erreur)."""
    if isinstance(etat, dict):
        for cle, valeur in etat.items():
            chemin = f"{prefixe}.{cle}"
            inventaire.setdefault((etape, cle), set()).add(chemin)
            _cles_depuis_etat(valeur, etape, chemin, inventaire)
    elif isinstance(etat, list):
        # Les listes vides d'un état neuf ne révèlent aucune clé d'élément :
        # c'est précisément pourquoi la fixture de démo (peuplée) est la
        # deuxième source de l'inventaire.
        for element in etat[:3]:
            _cles_depuis_etat(element, etape, f"{prefixe}[]", inventaire)


def _blocs_interfaces_ts(source: str) -> dict[str, str]:
    """Corps de chaque `interface X { ... }` de types.ts, par appariement des
    accolades. Les commentaires sont retirés au préalable pour ne pas prendre
    un exemple cité en commentaire pour une propriété."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    source = re.sub(r"//[^\n]*", "", source)
    blocs: dict[str, str] = {}
    for entete in re.finditer(r"\binterface\s+(\w+)[^{]*\{", source):
        debut, profondeur = entete.end() - 1, 0
        for i in range(debut, len(source)):
            if source[i] == "{":
                profondeur += 1
            elif source[i] == "}":
                profondeur -= 1
                if profondeur == 0:
                    blocs[entete.group(1)] = source[debut + 1:i]
                    break
    return blocs


def _bloc_imbrique(corps: str, nom_propriete: str) -> str:
    """Corps de la propriété-objet `nom_propriete` à l'intérieur de `corps`."""
    entete = re.search(r"(?m)^\s*" + re.escape(nom_propriete) + r"\s*\??:\s*\{", corps)
    assert entete, f"propriété objet `{nom_propriete}` introuvable dans types.ts"
    debut, profondeur = entete.end() - 1, 0
    for i in range(debut, len(corps)):
        if corps[i] == "{":
            profondeur += 1
        elif corps[i] == "}":
            profondeur -= 1
            if profondeur == 0:
                return corps[debut + 1:i]
    raise AssertionError(f"bloc `{nom_propriete}` non refermé dans types.ts")


def _sous_blocs_etapes(bloc_steps: str) -> list[tuple[str, str]]:
    """Découpe `steps: { cadrage: {...}, diagnostic: {...} }` en (nom, corps)
    par étape. Le nom d'étape n'est pas un champ à saisir — mais depuis le
    09/09/2026 il est retenu, parce que c'est lui qui rattache chaque clé de
    types.ts à sa phase et permet de chercher la preuve au bon endroit."""
    sous_blocs, i = [], 0
    motif = re.compile(r"(?m)^\s*(\w+)\s*\??:\s*\{")
    while i < len(bloc_steps):
        entete = motif.search(bloc_steps, i)
        if not entete:
            break
        debut, profondeur = entete.end() - 1, 0
        for j in range(debut, len(bloc_steps)):
            if bloc_steps[j] == "{":
                profondeur += 1
            elif bloc_steps[j] == "}":
                profondeur -= 1
                if profondeur == 0:
                    sous_blocs.append((entete.group(1), bloc_steps[debut + 1:j]))
                    i = j + 1
                    break
        else:
            break
    return sous_blocs


# Interfaces décrivant une sortie du moteur d'audit et non l'état saisi par le
# consultant : leurs champs n'ont, par construction, aucun formulaire.
_INTERFACES_MOTEUR = {"AuditResult", "Control"}


def _cles_depuis_types_ts(inventaire: dict[tuple[str, str], set[str]]) -> None:
    """Le contrat partagé back/front, `ProjectState.steps` de web/src/types.ts.

    Troisième source, indispensable : `source` (sur RedouteEvent) n'apparaît
    ni dans l'état neuf — la liste y est vide — ni dans la fixture de démo,
    qui ne le renseigne pas. Sans types.ts, le champ à l'origine de l'incident
    du 09/09/2026 échapperait au test censé le détecter.

    L'exploration des interfaces imbriquées transporte le nom de l'étape
    d'où elle est partie (09/09/2026) : `EntreeSoa` n'est atteignable que
    depuis `evaluation`, `OperationalScenario` que depuis `ebios`, et leurs
    champs homonymes doivent le rester dans l'inventaire. Une interface
    partagée par deux étapes est simplement indexée sous les deux.
    """
    interfaces = _blocs_interfaces_ts(TYPES_TS.read_text(encoding="utf-8"))
    assert "ProjectState" in interfaces, "interface ProjectState introuvable dans types.ts"

    bloc_steps = _bloc_imbrique(interfaces["ProjectState"], "steps")
    a_explorer: list[tuple[str, str]] = []
    for etape, bloc_etape in _sous_blocs_etapes(bloc_steps):
        for propriete in re.finditer(r"(?m)^\s*(\w+)\s*\??:", bloc_etape):
            inventaire.setdefault((etape, propriete.group(1)), set()).add(
                f"types.ts:steps.{etape}.{propriete.group(1)}")
        a_explorer += [(etape, m.group(1)) for m in re.finditer(r"\b([A-Z]\w+)\b", bloc_etape)
                       if m.group(1) in interfaces]

    vues: set[tuple[str, str]] = set()
    while a_explorer:
        etape, nom = a_explorer.pop()
        if (etape, nom) in vues or nom in _INTERFACES_MOTEUR or nom not in interfaces:
            continue
        vues.add((etape, nom))
        corps = interfaces[nom]
        for propriete in re.finditer(r"(?m)^\s*(\w+)\s*\??:", corps):
            inventaire.setdefault((etape, propriete.group(1)), set()).add(
                f"types.ts:{nom}.{propriete.group(1)}")
        a_explorer += [(etape, m.group(1)) for m in re.finditer(r"\b([A-Z]\w+)\b", corps)
                       if m.group(1) in interfaces]


def inventaire_modele() -> dict[tuple[str, str], set[str]]:
    """Clés de `steps.*` indexées par (étape, clé), réunies depuis les trois
    sources disponibles.

    Aucune ne suffit seule : l'état neuf a ses listes vides (donc pas de clés
    d'élément), la fixture de démo ne renseigne pas tout, et types.ts ne dit
    rien des clés ajoutées côté serveur uniquement.
    """
    inventaire: dict[tuple[str, str], set[str]] = {}
    for type_mission in ("grc", "consulting"):
        etat = create_empty_state("test-coherence", "Test", "Client", type_mission)
        for etape, contenu in etat["steps"].items():
            _cles_depuis_etat(contenu, etape, f"steps.{etape}", inventaire)
    for etape, contenu in demo_fixture.construire("test-coherence")["steps"].items():
        _cles_depuis_etat(contenu, etape, f"demo:steps.{etape}", inventaire)
    _cles_depuis_types_ts(inventaire)
    return inventaire


def _exclusion(etape: str, cle: str) -> str | None:
    """Justification d'exclusion applicable au couple, jokers compris."""
    return EXCLUSIONS.get(f"{etape}.{cle}") or EXCLUSIONS.get(f"*.{cle}")


# ---------------------------------------------------------------------------
# 2. Détection d'un moyen de saisie dans web/src, à l'échelle de l'étape
# ---------------------------------------------------------------------------
# Un champ *modifiable*, pas seulement *affiché* : `quick_wins` était bien
# présent à l'écran le 09/09/2026, en lecture seule. Une simple recherche du
# nom de la clé dans les sources n'aurait donc rien signalé.
#
# `onClick` est volontairement absent de cette liste : les boutons « modifier »
# et « supprimer » d'une carte entourent l'affichage en lecture seule d'un
# champ, et les compter comme une saisie rendrait le test aveugle au cas
# `redoute_events[].source`.
_SAISIE = re.compile(r"onChange|onValueChange|e\.target\.(value|checked)")
_FENETRE = 6  # lignes de part et d'autre : la portée d'un élément JSX

# Écrans de saisie de chaque étape (chemins relatifs à web/src).
#
# Ajouté le 09/09/2026 : sans cette table, la preuve était cherchée dans tout
# `web/src/`, si bien qu'une clé sans champ dans sa propre phase passait grâce
# à une homonyme saisie ailleurs — une quinzaine de noms étaient dans ce cas
# (`event` couvert par ConnectorsPanel, `satisfait` par ObligationsAIPD,
# `statut` par IsoPivotView, `owner` par PhaseCadrage…).
#
# Une étape absente de la table retombe volontairement sur l'ensemble de
# `web/src/` (voir `_sources_etape`) : un oubli ici doit rendre le test plus
# permissif, jamais déclencher une avalanche de faux positifs qui pousserait
# la prochaine personne à exclure en masse.
_FICHIERS_PAR_ETAPE: dict[str, tuple[str, ...]] = {
    "cadrage": ("components/phases/PhaseCadrage.tsx",),
    "diagnostic": ("components/phases/PhaseDiagnostic.tsx",
                   "components/ObligationsAIPD.tsx",
                   "components/ViolationsPanel.tsx"),
    "tprm": ("components/phases/PhaseTprm.tsx",),
    "ebios": ("components/phases/PhaseEbios.tsx",),
    "resilience": ("components/phases/PhaseResilience.tsx",),
    # PhaseResilience porte aussi les contrôles manuels et appelle SoaPanel /
    # PreuveLibraryPanel : l'étape « evaluation » est saisie depuis ces trois
    # fichiers (updateStepData("evaluation", …) y est appelé).
    "evaluation": ("components/phases/PhaseResilience.tsx",
                   "components/SoaPanel.tsx",
                   "components/PreuveLibraryPanel.tsx"),
    "traitement": ("components/phases/PhaseTraitement.tsx",),
    "restitution": ("components/phases/PhaseTraitement.tsx",
                    "components/RevueExport.tsx"),
    "collecte": ("pages/CollecteTechnique.tsx",),
}


def _sources_web() -> list[tuple[str, list[str]]]:
    """Sources de l'interface, hors tests et hors types.ts.

    types.ts est exclu à dessein : c'est l'une des sources de l'inventaire.
    S'y trouver ne prouve pas qu'un écran laisse saisir le champ — c'était le
    cas des quatre champs de l'incident.
    """
    fichiers = []
    for chemin in sorted(WEB_SRC.rglob("*.ts*")):
        relatif = chemin.relative_to(WEB_SRC).as_posix()
        if relatif == "types.ts" or ".test." in chemin.name or relatif.startswith("test/"):
            continue
        fichiers.append((relatif, chemin.read_text(encoding="utf-8").splitlines()))
    return fichiers


def _sources_etape(etape: str, toutes: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """Sources où chercher la saisie d'une clé de `etape`.

    Repli assumé sur l'ensemble de `web/src/` pour une étape non répertoriée :
    une étape nouvelle (ou renommée) ne doit pas faire échouer d'un coup tous
    ses champs. On perd la précision pour cette étape-là, on ne perd pas le
    test — et `test_table_des_ecrans_par_etape_a_jour` signale l'oubli.
    """
    attendus = _FICHIERS_PAR_ETAPE.get(etape)
    if attendus is None:
        return toutes
    return [(relatif, lignes) for relatif, lignes in toutes if relatif in attendus]


def _preuve_de_saisie(cle: str, sources: list[tuple[str, list[str]]],
                      etape: str | None = None) -> str | None:
    """Emplacement d'un moyen de saisie pour `cle`, ou None s'il n'en existe pas.

    Quatre formes, toutes relevées dans le code de l'interface :
      1. `updateStepData("etape", "cle", ...)` — écriture directe d'un champ ;
      2. `cle: "..."` dans un descripteur de formulaire générique (SoclePanel,
         PhaseTprm affichent leurs champs depuis un tableau de descripteurs) ;
      3. `objet.cle = ...` — écriture par affectation (PhaseResilience) ;
      4. la clé lue comme propriété (`.cle`, `cle:`, `"cle"`) à portée d'un
         `onChange` / `e.target.value` : le couple habituel value + onChange
         d'un `<input>` React.

    L'occurrence doit avoir la forme d'un accès à une propriété : sans cela un
    mot français d'un commentaire (« source », « preuve », « notes ») suffirait
    à faire passer le test.

    Deux précisions du 09/09/2026, pour que l'emplacement rendu soit **le bon** :
      * quand `etape` est fourni, la forme 1 exige le nom de l'étape en premier
        argument — PhaseTraitement écrit `traitement` *et* `restitution`, et
        PhaseResilience `resilience` *et* `evaluation` : sans cela une écriture
        vers l'autre étape servait de preuve ;
      * les trois formes d'écriture explicite sont cherchées dans **tous** les
        fichiers avant qu'on se rabatte sur la simple proximité d'un `onChange`.
        L'ancienne version rendait la première occurrence du premier fichier
        par ordre alphabétique, quelle que soit sa force : elle citait volontiers
        un `NOUVELLE = { … }` là où l'écriture réelle vivait deux fichiers plus
        loin, et une preuve fausse est ce qui envoie chercher au mauvais endroit.
    """
    echappee = re.escape(cle)
    mot = re.compile(r"\b" + echappee + r"\b")
    etape_attendue = re.escape(etape) if etape else r"[^,]+"
    ecriture_directe = re.compile(
        r'updateStepData\(\s*"?' + etape_attendue + r'"?\s*,\s*"' + echappee + r'"')
    descripteur = re.compile(r'\b(cle|key|champ|field)\s*:\s*"' + echappee + r'"')
    affectation = re.compile(r"\." + echappee + r"\s*=[^=]")
    propriete = re.compile(r"\." + echappee + r"\b|\b" + echappee + r"\s*:|[\"']" + echappee + r"[\"']")

    repli: str | None = None
    for fichier, lignes in sources:
        for i, ligne in enumerate(lignes):
            if not mot.search(ligne):
                continue
            if (ecriture_directe.search(ligne) or descripteur.search(ligne)
                    or affectation.search(ligne)):
                return f"{fichier}:{i + 1}"
            if repli is None and propriete.search(ligne):
                fenetre = "\n".join(lignes[max(0, i - _FENETRE):i + _FENETRE + 1])
                if _SAISIE.search(fenetre):
                    repli = f"{fichier}:{i + 1}"
    return repli


# ---------------------------------------------------------------------------
# 3. Les tests
# ---------------------------------------------------------------------------
def _exige_les_sources_web() -> None:
    """L'interface doit être là, sinon le test principal serait vert sans rien
    vérifier — la panne silencieuse même que ce fichier combat.

    Seule dérogation : l'image serveur seule (`api/Dockerfile`), qui ne
    contient pas `web/`. Un `web/` présent mais amputé de `src/` reste une
    erreur, pas une dérogation.
    """
    if not (RACINE / "web").exists():
        pytest.skip("dépôt sans frontend (image serveur seule) : rien à vérifier")


def test_arborescence_web_presente():
    """Garde-fou : sources de l'interface lisibles et en nombre plausible."""
    _exige_les_sources_web()
    assert WEB_SRC.is_dir(), f"sources de l'interface introuvables : {WEB_SRC}"
    assert TYPES_TS.is_file(), f"contrat de modèle introuvable : {TYPES_TS}"
    assert len(_sources_web()) > 20, "trop peu de sources d'interface lues"


def test_table_des_ecrans_par_etape_a_jour():
    """Garde-fou de `_FICHIERS_PAR_ETAPE` (09/09/2026).

    Un fichier renommé ou déplacé viderait silencieusement la liste de son
    étape, et le test principal réclamerait alors une saisie pour chacun de
    ses champs sans que personne comprenne pourquoi. Autant le dire ici, une
    fois, avec le nom du fichier disparu.

    L'inverse est contrôlé aussi : une étape du modèle absente de la table
    retombe sur tout `web/src/` — c'est le repli voulu, mais il rend le test
    aveugle aux homonymes pour cette étape, donc il doit se voir.
    """
    _exige_les_sources_web()
    connus = {relatif for relatif, _ in _sources_web()}
    introuvables = sorted(
        f"{etape} → {fichier}"
        for etape, fichiers in _FICHIERS_PAR_ETAPE.items()
        for fichier in fichiers
        if fichier not in connus
    )
    assert not introuvables, (
        "Écrans de saisie référencés par `_FICHIERS_PAR_ETAPE` mais introuvables "
        f"dans web/src : {introuvables}.\nUn composant de phase a été renommé ou "
        "déplacé : corriger la table, sinon les champs de cette étape seront "
        "signalés comme non saisissables."
    )
    etapes_du_modele = {etape for etape, _ in inventaire_modele()}
    non_repertoriees = sorted(etapes_du_modele - set(_FICHIERS_PAR_ETAPE))
    assert not non_repertoriees, (
        f"Étapes du modèle absentes de `_FICHIERS_PAR_ETAPE` : {non_repertoriees}.\n"
        "Leurs champs sont cherchés dans tout web/src (repli), donc couverts par "
        "n'importe quelle clé homonyme d'une autre phase — exactement le défaut "
        "corrigé le 09/09/2026. Ajouter leurs écrans de saisie à la table."
    )


def test_inventaire_du_modele_non_vide():
    """Garde-fou : un inventaire vide (refactoring de crud.py, renommage de
    `steps`) rendrait le test principal vert sans rien contrôler."""
    _exige_les_sources_web()
    inventaire = inventaire_modele()
    assert len(inventaire) > 100, f"inventaire anormalement court : {len(inventaire)} couples"
    # Les quatre champs de l'incident du 09/09/2026 doivent être couverts,
    # chacun rattaché à sa phase.
    for couple in (("ebios", "source"), ("ebios", "date_revue"),
                   ("resilience", "eviction"), ("resilience", "eradication"),
                   ("traitement", "quick_wins")):
        assert couple in inventaire, f"le couple `{couple}` a disparu de l'inventaire"
    # Et les homonymes doivent rester distincts : c'est la garantie même du
    # correctif du 09/09/2026. Si ces deux-là fusionnaient, la SoA
    # redeviendrait couverte par les scénarios EBIOS.
    assert ("evaluation", "date_revue") in inventaire
    assert ("ebios", "date_revue") in inventaire


def test_le_detecteur_sait_repondre_non():
    """Un test incapable d'échouer ne vaut rien.

    On vérifie ici que `_preuve_de_saisie` répond bien « pas de saisie » pour
    une clé absente de l'interface — sinon le test principal serait vert quoi
    qu'il arrive.
    """
    _exige_les_sources_web()
    sources = _sources_web()
    assert _preuve_de_saisie("champ_fantome_du_09_09_2026", sources) is None
    # Et qu'il répond « oui » pour un champ dont la saisie est certaine.
    assert _preuve_de_saisie("exec_summary", sources) is not None
    # Le cloisonnement par étape, dans les deux sens (09/09/2026) : le
    # `date_revue` des scénarios EBIOS est saisissable dans PhaseEbios, celui
    # de la SoA ne l'est nulle part dans les écrans de l'étape `evaluation`.
    toutes = _sources_web()
    assert _preuve_de_saisie("date_revue", _sources_etape("ebios", toutes), "ebios") is not None
    assert _preuve_de_saisie("date_revue", _sources_etape("evaluation", toutes), "evaluation") is None


def test_exclusions_toutes_encore_pertinentes():
    """Une exclusion dont le couple a disparu du modèle doit être retirée, sans
    quoi la liste se fossilise et couvre un jour un vrai trou."""
    _exige_les_sources_web()
    inventaire = inventaire_modele()
    couples = set(inventaire)
    noms = {cle for _, cle in couples}

    def encore_utile(entree: str) -> bool:
        etape, cle = entree.split(".", 1)
        # Le joker `*.cle` reste pertinent tant que le nom existe quelque part ;
        # une exclusion nominative doit retrouver son couple exact.
        return cle in noms if etape == "*" else (etape, cle) in couples

    orphelines = sorted(entree for entree in EXCLUSIONS if not encore_utile(entree))
    assert not orphelines, (
        "Ces exclusions ne correspondent plus à aucun couple (étape, clé) du "
        f"modèle — à supprimer de EXCLUSIONS : {orphelines}"
    )


def test_chaque_champ_du_modele_a_un_moyen_de_saisie():
    """Le test de l'incident du 09/09/2026.

    Toute clé de `steps.*` doit soit disposer d'un moyen de saisie **dans les
    écrans de sa propre étape**, soit figurer dans EXCLUSIONS avec sa
    justification.
    """
    _exige_les_sources_web()
    inventaire = inventaire_modele()
    toutes = _sources_web()

    sans_saisie: dict[tuple[str, str], tuple[list[str], str | None]] = {}
    for (etape, cle), chemins in sorted(inventaire.items()):
        if _exclusion(etape, cle):
            continue
        if _preuve_de_saisie(cle, _sources_etape(etape, toutes), etape) is not None:
            continue
        # Où le nom est-il saisissable ailleurs ? C'est l'indication la plus
        # utile du message : elle distingue « champ oublié dans cette phase »
        # de « champ jamais saisi nulle part ».
        sans_saisie[(etape, cle)] = (sorted(chemins), _preuve_de_saisie(cle, toutes))

    if sans_saisie:
        lignes = []
        for (etape, cle), (chemins, ailleurs) in sans_saisie.items():
            indice = (f" — le nom est saisi en {ailleurs}, mais dans une autre "
                      f"phase : cela ne remplit pas {etape}.{cle}"
                      if ailleurs else " — nom saisi nulle part dans web/src")
            lignes.append(f"  - {etape}.{cle}  (vu en : {', '.join(chemins[:3])}){indice}")
        detail = "\n".join(lignes)
        pytest.fail(
            f"{len(sans_saisie)} champ(s) du modèle de mission n'ont aucun moyen de "
            f"saisie dans les écrans de leur étape :\n{detail}\n\n"
            "Un champ sans écran est réclamé indéfiniment par le vérificateur de "
            "complétude et sort vide du rapport client (incident du 09/09/2026).\n"
            "Deux issues, jamais une troisième : ajouter le champ dans le "
            "formulaire de la phase concernée, ou l'inscrire dans EXCLUSIONS "
            "(en haut de ce fichier) sous la forme \"étape.clé\", avec la raison "
            "pour laquelle il n'a légitimement pas à être saisi.\n"
            "Si le message ci-dessus indique que le nom est saisi ailleurs, ce "
            "n'est pas une preuve : c'est un homonyme d'une autre phase — le "
            "piège que ce test a cessé de tendre le 09/09/2026."
        )
