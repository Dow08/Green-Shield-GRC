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

    verifier(3, "Évaluation des tiers (TPRM)", (steps.get("tprm") or {}).get("tiers"), "recommande")

    ebios = steps.get("ebios") or {}
    verifier(4, "Événements redoutés", ebios.get("redoute_events"))
    verifier(4, "Scénarios opérationnels", ebios.get("operational_scenarios"))

    resilience = steps.get("resilience") or {}
    bcp = resilience.get("bcp_strategy") or {}
    verifier(5, "Cible de reprise (RTO)", bcp.get("rto"))
    verifier(5, "Perte de données maximale admissible (RPO)", bcp.get("rpo"))
    verifier(5, "Politique de sauvegarde", bcp.get("backup_policy"), "recommande")
    e3r = resilience.get("e3r") or {}
    for cle, libelle in (("endiguement", "Endiguement"), ("eviction", "Éviction"),
                         ("eradication", "Éradication"), ("reconstruction", "Reconstruction")):
        verifier(5, f"Séquence E3R — {libelle}", e3r.get(cle), "recommande")

    traitement = steps.get("traitement") or {}
    verifier(6, "Plan d'action de remédiation", traitement.get("remediations"))
    verifier(6, "Mesures Cyberdépart", traitement.get("quick_wins"), "recommande")

    bloquants = [m for m in manques if m["gravite"] == "bloquant"]
    return {
        "complet": not manques,
        "pret_pour_export": not bloquants,
        "total": len(manques),
        "bloquants": len(bloquants),
        "manques": manques,
    }
