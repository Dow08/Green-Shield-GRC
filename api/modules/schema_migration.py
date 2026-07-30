"""Versionnement du schéma des missions et chaîne de migration.

Le schéma de `project.json` va encore évoluer (volet Consulting au jalon 2,
référentiels complémentaires au jalon 3). Un script de migration unique ne suffit
donc pas : il faut une **chaîne** ordonnée, rejouable, qui amène une mission de
n'importe quelle version passée à la version courante (cf. docs/audit-critique-plan.md, F4).

Règles :
  * une migration n'efface jamais une donnée — elle ajoute ou déplace ;
  * une mission déjà à jour traverse la chaîne sans être modifiée ;
  * une mission sans `schema_version` est réputée en version 1 (état d'avant le jalon 1).
"""
from __future__ import annotations

from typing import Callable

from . import aipd as aipd_module
from . import tprm

CURRENT_SCHEMA_VERSION = 7


def _to_v2(state: dict) -> dict:
    """v1 → v2 : introduction du socle commun et du volet GRC structuré.

    Le socle rassemble ce qui est commun aux deux volets (qualification, cadrage
    contractuel, entretiens). Les données de cadrage déjà saisies restent à leur
    place historique dans `steps.cadrage` : elles sont référencées, pas recopiées,
    pour qu'il n'existe jamais deux vérités pour un même champ.
    """
    socle = state.setdefault("socle", {})
    socle.setdefault("qualification", {
        "declencheur": "",
        "sponsor_executif": "",
        "budget": "",
        "maturite_actuelle": "",
        "equipe_interne": "",
        "echeance_cible": "",
    })
    socle.setdefault("contractualisation", {
        "perimetre_inclus": "",
        "perimetre_exclu": "",
        "livrables": [],
        "modalites": "",
        "acces_si": "",
    })
    socle.setdefault("kickoff", {
        "date": "",
        "participants": [],
        "gouvernance": "",
    })
    socle.setdefault("entretiens", [])

    grc = state.setdefault("grc", {})
    grc.setdefault("active", state.get("type") == "grc")
    fw = (state.get("steps", {}).get("cadrage", {}) or {}).get("framework_id")
    grc.setdefault("referentiels_actifs", [fw] if fw else [])
    # Avancement des parcours référentiels : {referentiel: {etape_id: {...}}}
    grc.setdefault("parcours", {})

    consulting = state.setdefault("consulting", {})
    consulting.setdefault("active", state.get("type") != "grc")

    return state


def _to_v3(state: dict) -> dict:
    """v2 → v3 : suivi du temps consommé par mission (F19).

    Hermes liste « charges consommées vs budget » parmi les indicateurs à
    reporter dès le démarrage d'une mission. Le budget *vendu* existait déjà
    (`socle.qualification.budget`, saisie libre) mais rien ne mesurait le temps
    *réellement* passé — donnée qui alimente à la fois le pilotage client, la
    facturation du consultant et le calcul de ROSI.

    Modèle : un journal d'entrées horodatées (pas un chronomètre live, qui
    perdrait son état à la fermeture de l'application).
    """
    socle = state.setdefault("socle", {})
    socle.setdefault("temps", {"entrees": []})
    return state


def _to_v4(state: dict) -> dict:
    """v3 → v4 : politique de conservation des données personnelles (F17).

    Les grilles d'entretien collectent des noms, fonctions et déclarations de
    personnes physiques. Le consultant en est responsable de traitement : il
    lui faut une durée de conservation définie et une suppression en fin de
    mission. Le délai ne court qu'à partir de `date_fin_mission` — la
    conservation se compte depuis la fin de la relation, pas depuis son début.
    """
    socle = state.setdefault("socle", {})
    socle.setdefault("rgpd_consultant", {
        "duree_conservation_mois": 36,
        "date_fin_mission": "",
        "purge_effectuee_le": "",
    })
    return state


def _to_v5(state: dict) -> dict:
    """v4 → v5 : criticité des tiers scindée selon le volet (§14.1bis).

    Deux ajouts, aucune donnée modifiée :

      * chaque tiers déjà noté reçoit `methode: "moyenne_historique"`. Les notes
        elles-mêmes ne sont **pas** recalculées : un consultant a pu présenter
        une criticité à son client, et une migration silencieuse la changerait
        sous ses pieds. Le passage au ratio ANSSI est une action explicite
        (route `POST /api/projects/{id}/tprm/recalculer`).
      * sur une mission GRC, chaque tiers reçoit la check-list de conformité
        DORA/NIS2 qui remplace le scoring EBIOS, non cochée.
    """
    tiers = ((state.get("steps") or {}).get("tprm") or {}).get("tiers") or []
    est_grc = state.get("type") == "grc"
    for tier in tiers:
        # Ne marquer que ce qui porte réellement une note : étiqueter un tiers
        # jamais scoré (volet GRC) d'une méthode de calcul serait faux.
        if "score" in tier:
            tier.setdefault("methode", tprm.METHODE_HISTORIQUE)
        if est_grc:
            tier.setdefault("exigences", tprm.exigences_par_defaut())
    return state


def _to_v6(state: dict) -> dict:
    """v5 → v6 : obligations organisationnelles de l'AIPD (§14.2.1).

    Les quatre volets d'analyse existaient déjà ; s'y ajoutent les cinq
    obligations de procédure (avis du DPO, avis des personnes concernées,
    listes CNIL, réexamen, consultation préalable Art. 36) et la qualification
    du risque résiduel dont dépend la dernière.

    Le risque résiduel démarre à « non évalué » et non à « acceptable » :
    supposer l'acceptabilité ferait disparaître l'obligation Art. 36 sans que
    personne ne l'ait jugée.
    """
    aipd = state.setdefault("steps", {}).setdefault("diagnostic", {}).setdefault("aipd", {})
    aipd.setdefault("risque_residuel", "non_evalue")
    aipd.setdefault("obligations", aipd_module.obligations_par_defaut())
    return state


def _to_v7(state: dict) -> dict:
    """v6 → v7 : volet stratégique de la remédiation ANSSI (§14.2.3).

    La séquence E3R (endiguement/éviction/éradication/reconstruction) est
    technique et opérationnelle ; il manquait le volet stratégique — les
    critères d'arbitrage Direction entre urgence de redémarrage et coûts ou
    risques induits par un redémarrage précipité.
    """
    resilience = state.setdefault("steps", {}).setdefault("resilience", {})
    resilience.setdefault("strategie_remediation", {
        "urgence_redemarrage": "", "couts_risques_redemarrage": "", "decision_direction": "",
    })
    return state


# Chaîne ordonnée : version cible -> fonction qui y amène.
_MIGRATIONS: list[tuple[int, Callable[[dict], dict]]] = [
    (2, _to_v2),
    (3, _to_v3),
    (4, _to_v4),
    (5, _to_v5),
    (6, _to_v6),
    (7, _to_v7),
]


def migrate(state: dict) -> dict:
    """Amène une mission à la version courante du schéma."""
    version = int(state.get("schema_version", 1))
    for target, migration in _MIGRATIONS:
        if version < target:
            state = migration(state)
            version = target
    state["schema_version"] = version
    return state


def needs_migration(state: dict) -> bool:
    return int(state.get("schema_version", 1)) < CURRENT_SCHEMA_VERSION
