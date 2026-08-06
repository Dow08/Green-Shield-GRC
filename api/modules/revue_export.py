"""revue_export.py — revue de complétude d'une mission avant génération d'un livrable.

Les exports remplacent silencieusement toute donnée absente par « N/A » ou
« non rédigé » (cf. `projects.py`, génération des documents). Un rapport peut
donc partir chez un client criblé de trous sans que personne ne s'en aperçoive.

Ce module inspecte l'état réel d'une mission et énumère ce qui manque, avec la
phase où le compléter. Il ne remplit rien et n'invente rien : il rend visible
l'incomplétude, ce qui sert directement la promesse « zéro invention » — mieux
vaut un manque signalé qu'un « N/A » noyé dans un livrable.

Deux niveaux :
  * `bloquant`   — le livrable serait manifestement incomplet (périmètre non
                   défini, aucun actif, aucune mesure de traitement) ;
  * `recommande` — le livrable reste exploitable mais perd de sa valeur.
"""
from __future__ import annotations

from datetime import date

from . import aipd as aipd_module
from . import soa as soa_module
from . import demandes_preuves

# Libellés des phases, alignés sur le stepper de l'interface.
PHASES = {
    1: "Cadrage & Patrimoine",
    2: "Diagnostic & RGPD",
    3: "Risques Tiers (TPRM)",
    4: "Analyse des Menaces (EBIOS RM)",
    5: "Résilience & E3R",
    6: "Traitement & Livrables",
}


def _vide(valeur) -> bool:
    """Un champ est vide s'il est absent, nul, ou ne contient que des espaces."""
    if valeur is None:
        return True
    if isinstance(valeur, str):
        return not valeur.strip()
    if isinstance(valeur, (list, dict)):
        return len(valeur) == 0
    return False


def revue(state: dict) -> dict:
    """Énumère les manques d'une mission. Ne modifie rien."""
    steps = state.get("steps", {}) or {}
    manques: list[dict] = []

    def verifier(phase: int, libelle: str, valeur, gravite: str = "bloquant") -> None:
        if _vide(valeur):
            manques.append({"phase": phase, "phase_libelle": PHASES[phase],
                            "champ": libelle, "gravite": gravite})

    cadrage = steps.get("cadrage") or {}
    verifier(1, "Périmètre technique de l'audit", cadrage.get("scope"))
    verifier(1, "Missions & finalités du client", cadrage.get("client_missions"), "recommande")
    verifier(1, "Texte de l'accord de confidentialité (NDA)", cadrage.get("nda_text"))
    verifier(1, "Cartographie des valeurs métier", cadrage.get("assets_metier"))
    verifier(1, "Inventaire des biens supports", cadrage.get("assets_support"))
    if not cadrage.get("nda_signed"):
        manques.append({"phase": 1, "phase_libelle": PHASES[1],
                        "champ": "NDA non signé", "gravite": "recommande"})

    diagnostic = steps.get("diagnostic") or {}
    verifier(2, "Registre des activités de traitement (RGPD art. 30)", diagnostic.get("rgpd_register"))
    if diagnostic.get("aipd_required"):
        aipd = diagnostic.get("aipd") or {}
        verifier(2, "AIPD — description du traitement", aipd.get("treatment_description"))
        verifier(2, "AIPD — évaluation de la nécessité", aipd.get("necessity_eval"))
        verifier(2, "AIPD — évaluation des risques", aipd.get("risks_eval"))
        verifier(2, "AIPD — mesures de protection", aipd.get("mitigation_measures"))

        # Les quatre volets ci-dessus sont le *contenu* de l'analyse ; ceux-ci
        # sont sa conduite. Une AIPD complète sur le fond peut être irrégulière
        # faute d'avis du DPO ou de saisine de la CNIL (§14.2.1).
        etat_obligations = aipd_module.etat(aipd)
        for libelle in etat_obligations["manquantes"]:
            manques.append({"phase": 2, "phase_libelle": PHASES[2],
                            "champ": f"AIPD — {libelle}", "gravite": "bloquant"})
        if aipd.get("risque_residuel") == "non_evalue":
            manques.append({"phase": 2, "phase_libelle": PHASES[2],
                            "champ": "AIPD — risque résiduel après mesures non qualifié",
                            "gravite": "bloquant"})

    # Registre des violations (Art. 33-34) : une violation non notifiée à la
    # CNIL au-delà de 72h sans justification est un manquement réglementaire,
    # pas une simple lacune du livrable.
    for v in diagnostic.get("violations") or []:
        vid = v.get("id") or "?"
        if not v.get("date_constat"):
            continue
        try:
            constat = date.fromisoformat(v["date_constat"])
        except ValueError:
            continue
        if v.get("notifiee_cnil"):
            continue
        jours_ecoules = (date.today() - constat).days
        if jours_ecoules > 3 and not (v.get("justification") or "").strip():
            manques.append({"phase": 2, "phase_libelle": PHASES[2],
                            "champ": f"Violation {vid} — non notifiée à la CNIL 72h après constat, "
                                     "sans justification", "gravite": "bloquant"})

    verifier(3, "Évaluation des tiers (TPRM)", (steps.get("tprm") or {}).get("tiers"), "recommande")

    ebios = steps.get("ebios") or {}
    verifier(4, "Événements redoutés", ebios.get("redoute_events"))
    scenarios = ebios.get("operational_scenarios") or []
    verifier(4, "Scénarios opérationnels", scenarios)
    # Un scénario sans propriétaire ni décision de traitement est une
    # observation, pas un risque géré (Hermes : "un risque sans owner n'est
    # pas géré") — signalé par scénario, pas seulement globalement.
    for s in scenarios:
        sid = s.get("id") or "?"
        if _vide(s.get("owner")):
            manques.append({"phase": 4, "phase_libelle": PHASES[4],
                            "champ": f"Scénario {sid} — sans propriétaire", "gravite": "recommande"})
        if _vide(s.get("strategie_traitement")):
            manques.append({"phase": 4, "phase_libelle": PHASES[4],
                            "champ": f"Scénario {sid} — stratégie de traitement non décidée", "gravite": "recommande"})

    resilience = steps.get("resilience") or {}
    bcp = resilience.get("bcp_strategy") or {}
    verifier(5, "Cible de reprise (RTO)", bcp.get("rto"))
    verifier(5, "Perte de données maximale admissible (RPO)", bcp.get("rpo"))
    verifier(5, "Politique de sauvegarde", bcp.get("backup_policy"), "recommande")
    e3r = resilience.get("e3r") or {}
    for cle, libelle in (("endiguement", "Endiguement"), ("eviction", "Éviction"),
                         ("eradication", "Éradication"), ("reconstruction", "Reconstruction")):
        verifier(5, f"Séquence E3R — {libelle}", e3r.get(cle), "recommande")
    strategie = resilience.get("strategie_remediation") or {}
    verifier(5, "Volet stratégique — décision Direction", strategie.get("decision_direction"), "recommande")

    soa_donnees = (steps.get("evaluation") or {}).get("soa") or []
    if soa_donnees:
        etat_soa = soa_module.etat(soa_donnees)
        if etat_soa["non_statues"] > 0:
            manques.append({"phase": 5, "phase_libelle": PHASES[5],
                            "champ": f"Déclaration d'Applicabilité — {etat_soa['non_statues']}/{etat_soa['total']} "
                                     "contrôle(s) sans décision d'applicabilité", "gravite": "recommande"})

    traitement = steps.get("traitement") or {}
    remediations = traitement.get("remediations") or []
    verifier(6, "Plan d'action de remédiation", remediations)
    verifier(6, "Mesures Cyberdépart", traitement.get("quick_wins"), "recommande")
    # Sans responsable ni échéance, une mesure dit quoi faire, jamais qui ni
    # quand.
    for r in remediations:
        rid = r.get("id") or "?"
        if _vide(r.get("responsable")):
            manques.append({"phase": 6, "phase_libelle": PHASES[6],
                            "champ": f"Mesure {rid} — sans responsable", "gravite": "recommande"})
        if _vide(r.get("echeance")):
            manques.append({"phase": 6, "phase_libelle": PHASES[6],
                            "champ": f"Mesure {rid} — sans échéance", "gravite": "recommande"})

    manques += _sections_vides(state)
    # Documents réclamés au client et jamais reçus : un manque de conduite de
    # mission, signalé sans bloquer l'export (cf. demandes_preuves.py).
    manques += demandes_preuves.manques_pour_revue(state)

    bloquants = [m for m in manques if m["gravite"] == "bloquant"]
    return {
        "complet": not manques,
        "pret_pour_export": not bloquants,
        "total": len(manques),
        "bloquants": len(bloquants),
        "manques": manques,
    }


# Sections du rapport d'audit dont le contenu vient d'une phase précise. Le
# libellé est celui du chapitre, pour que le manque désigne ce que le client
# verra manquer plutôt qu'un nom de champ interne.
_SECTIONS_RAPPORT = (
    (1, 6, "Synthèse à destination de la direction"),
    (2, 1, "Cadrage de la mission"),
    (3, 1, "Patrimoine évalué"),
    (5, 4, "Analyse de risque"),
    (6, 3, "Écosystème et risques tiers"),
    (7, 5, "Résilience et continuité"),
    (11, 6, "Plan de traitement"),
)


def _sections_vides(state: dict) -> list[dict]:
    """Chapitres du rapport d'audit qui sortiraient sans contenu.

    Complète les vérifications champ par champ ci-dessus par une vérification du
    **rendu**. Sans elle, la revue annonçait « prêt pour export, 0 manque » sur
    une mission dont le rapport sortait quasi vide — constaté en recette le
    29/07/2026, le filet de sécurité ne voyait pas le plus gros trou.

    L'import est local : `report_builder` importe déjà `couverture` et
    `docx_export`, et une dépendance de module à module en sens inverse créerait
    un cycle à l'import.
    """
    from . import report_builder

    steps = state.get("steps") or {}
    rendus = {
        1: report_builder._synthese_md(state),
        2: report_builder._cadrage_mission_md(state),
        3: report_builder._valeurs_metier_md(steps) + report_builder._biens_supports_md(steps),
        5: report_builder._redoutes_md(steps) + report_builder._scenarios_md(steps),
        6: report_builder._tprm_md(state),
        7: report_builder._continuite_md(steps),
        11: report_builder._remediations_md(steps),
    }

    manques = []
    for chapitre, phase, libelle in _SECTIONS_RAPPORT:
        rendu = rendus[chapitre]
        # Un rendu sans aucune ligne de tableau est une section vide : les
        # constructeurs renvoient alors une phrase en italique à la place.
        if "|" not in rendu and rendu.strip().startswith("_"):
            manques.append({
                "phase": phase, "phase_libelle": PHASES[phase],
                "champ": f"Rapport d'audit, chapitre {chapitre} « {libelle} » sortirait vide",
                "gravite": "bloquant",
            })
    return manques
