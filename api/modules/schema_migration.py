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
from . import soa as soa_module
from . import tprm

CURRENT_SCHEMA_VERSION = 13


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
    cadrage = state.get("steps", {}).get("cadrage", {}) or {}
    fw = cadrage.get("framework_id")
    # `framework_ids` (pluriel, missions multi-référentiel depuis le
    # 31/07/2026) prime sur le singulier historique quand il est présent.
    grc.setdefault("referentiels_actifs", cadrage.get("framework_ids") or ([fw] if fw else []))
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


def _to_v8(state: dict) -> dict:
    """v7 → v8 : chaîne risque -> traitement (audit critique, chantiers ②/③).

    Un scénario opérationnel sans propriétaire ni décision de traitement est
    une observation, pas un risque géré ; une mesure de remédiation sans
    responsable ni échéance dit quoi faire, jamais qui ni quand. Les champs
    démarrent tous vides — jamais de propriétaire ou d'échéance présumés à la
    place du consultant.
    """
    ebios = state.setdefault("steps", {}).setdefault("ebios", {})
    for scenario in ebios.get("operational_scenarios") or []:
        scenario.setdefault("actif_concerne", "")
        scenario.setdefault("gravite_residuelle", None)
        scenario.setdefault("vraisemblance_residuelle", None)
        scenario.setdefault("strategie_traitement", "")
        scenario.setdefault("owner", "")
        scenario.setdefault("date_revue", "")
        scenario.setdefault("statut", "")

    traitement = state.setdefault("steps", {}).setdefault("traitement", {})
    for remediation in traitement.get("remediations") or []:
        remediation.setdefault("responsable", "")
        remediation.setdefault("echeance", "")
        remediation.setdefault("statut", "")
        remediation.setdefault("cout_estime", "")
        remediation.setdefault("risque_lie", "")
    return state


def _to_v9(state: dict) -> dict:
    """v8 → v9 : Déclaration d'Applicabilité ISO 27001 Annexe A (chantier ①).

    Sans SoA, une mission ISO 27001 ne peut pas passer un audit de
    certification — c'est le premier document qu'un auditeur externe demande.
    Ne concerne que les missions dont le référentiel choisi est ISO 27001 :
    une mission DORA ou NIS2 n'a pas à porter 93 contrôles hors sujet.

    `applicable` démarre à `None` (non statué) sur les 93 contrôles, jamais à
    une valeur présumée — un consultant qui n'a pas encore tranché ne doit
    jamais voir 93 décisions qu'il n'a pas prises s'afficher comme actées.
    """
    cadrage = state.get("steps", {}).get("cadrage", {})
    if cadrage.get("framework_id") == "iso27001":
        evaluation = state.setdefault("steps", {}).setdefault("evaluation", {})
        evaluation.setdefault("soa", soa_module.entrees_par_defaut())
    return state


def _to_v10(state: dict) -> dict:
    """v9 → v10 : registre interne des violations de données (RGPD Art.
    33-34, G5).

    « Toujours documenter toute violation, même non notifiable, dans un
    registre interne » — obligation distincte de la simple notification à la
    CNIL : une violation jugée non notifiable reste une violation à tracer.
    """
    diagnostic = state.setdefault("steps", {}).setdefault("diagnostic", {})
    diagnostic.setdefault("violations", [])
    return state


def _to_v11(state: dict) -> dict:
    """v10 → v11 : bibliothèque de preuves multi-référentiels (G3bis).

    Une preuve de conformité écrite une fois (ex. une politique de sécurité)
    sert souvent plusieurs référentiels sur une même mission (ISO 27001 +
    DORA + NIS2), mais `manual_controls` ne portait qu'un champ `notes` libre
    par contrôle, sans lien vers les autres. Liste vide par défaut — aucune
    preuve n'est présumée exister.
    """
    evaluation = state.setdefault("steps", {}).setdefault("evaluation", {})
    evaluation.setdefault("preuves", [])
    return state


def _to_v12(state: dict) -> dict:
    """v11 → v12 : une mission GRC peut porter plusieurs référentiels actifs.

    Jusqu'ici une mission n'avait qu'un `framework_id` singulier, et
    `manual_controls` n'était jamais tagué de son référentiel d'origine —
    inutile tant qu'il n'y en avait qu'un. Les missions déjà existantes
    reçoivent ce tag rétroactivement (valeur = leur unique référentiel déjà
    connu), sans toucher au statut ni aux notes déjà saisis.
    """
    cadrage = state.get("steps", {}).get("cadrage", {}) or {}
    fw_id = cadrage.get("framework_id")
    fw_name = cadrage.get("framework_name")
    evaluation = state.get("steps", {}).get("evaluation", {}) or {}
    for controle in evaluation.get("manual_controls") or []:
        controle.setdefault("referentiel_id", fw_id)
        controle.setdefault("referentiel_name", fw_name)
    return state


def _to_v13(state: dict) -> dict:
    """v12 → v13 : registre des demandes de preuves dans le socle de mission.

    Le suivi des documents réclamés au client relève de la conduite de mission,
    pas du contenu de l'audit : il rejoint donc `socle` aux côtés des entretiens
    et du temps consommé, et non les phases.

    Les missions existantes reçoivent un registre vide. Rien n'est déduit des
    preuves déjà présentes : une preuve enregistrée ne prouve pas qu'une demande
    a été formulée, et inventer un historique de relances contredirait la règle
    « zéro invention ».
    """
    socle = state.setdefault("socle", {})
    socle.setdefault("demandes_preuves", [])
    return state


# Chaîne ordonnée : version cible -> fonction qui y amène.
_MIGRATIONS: list[tuple[int, Callable[[dict], dict]]] = [
    (2, _to_v2),
    (3, _to_v3),
    (4, _to_v4),
    (5, _to_v5),
    (6, _to_v6),
    (7, _to_v7),
    (8, _to_v8),
    (9, _to_v9),
    (10, _to_v10),
    (11, _to_v11),
    (12, _to_v12),
    (13, _to_v13),
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
