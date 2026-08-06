"""maturite_nist.py — radar de maturité NIST CSF 2.0, auto-déclaré par le
consultant, fonction par fonction (Govern, Identify, Protect, Detect,
Respond, Recover).

Orthogonal à la roue de rattachement (`nist_csf_map.py`) : la roue mesure une
**couverture calculée** (contrôles réellement rattachés/implémentés) ; ce
module restitue un **jugement professionnel déclaré**, qu'aucune donnée de
mission ne peut deviner. Les deux ne doivent jamais être fusionnés ni
confondus à l'écran.

Échelle des 4 Tiers — citée verbatim depuis `references/nist-csf.md` (skill
`grc-agent-hermes` de l'utilisateur, matière hors de ce dépôt) :

    1 Partial        Pratiques ad hoc, réactives, peu de partage d'information
    2 Risk Informed   Conscience du risque, mais pas de processus formel à
                       l'échelle de l'organisation
    3 Repeatable      Politiques formelles, application cohérente, processus
                       de gestion des risques formalisé
    4 Adaptive        Apprend de l'expérience, partage info, adaptation continue

Règle « zéro invention » : une fonction non déclarée par le consultant reste
`tier: None` — jamais un Tier 1 par défaut, qui laisserait croire à une
évaluation faite alors qu'aucune ne l'a été.
"""
from __future__ import annotations

from . import nist_csf_map

TIERS: dict[int, tuple[str, str]] = {
    1: ("Partial", "Pratiques ad hoc, réactives, peu de partage d'information"),
    2: ("Risk Informed", "Conscience du risque, mais pas de processus formel à l'échelle de l'organisation"),
    3: ("Repeatable", "Politiques formelles, application cohérente, processus de gestion des risques formalisé"),
    4: ("Adaptive", "Apprend de l'expérience, partage info, adaptation continue"),
}


def radar(state: dict) -> dict:
    """Profil de maturité déclaré de la mission : six fonctions, jamais inventé.

    Disponible quelle que soit la mission — le NIST CSF sert ici d'outil de
    pilotage/communication transverse, pas d'une exigence propre au parcours
    NIST CSF (cf. `api/frameworks/nist_csf.yaml` : « cadre agnostique »).
    """
    declare = ((state.get("grc") or {}).get("maturite_nist")) or {}

    fonctions = []
    nb_evaluees = 0
    for code, libelle in nist_csf_map.FONCTIONS:
        entree = declare.get(code) or {}
        tier = entree.get("tier")
        # Une valeur corrompue ou hors barème (0, 5, texte...) n'est jamais
        # affichée comme un tier réel : elle retombe silencieusement sur
        # « non évalué ».
        nom, description = TIERS.get(tier, (None, None)) if isinstance(tier, int) else (None, None)
        if nom is None:
            tier = None
        else:
            nb_evaluees += 1
        fonctions.append({
            "code": code,
            "libelle": libelle,
            "tier": tier,
            "tier_nom": nom,
            "tier_description": description,
            "justification": entree.get("justification") or "",
        })

    return {
        "fonctions": fonctions,
        "nb_evaluees": nb_evaluees,
        "note": ("Auto-évaluation déclarative du consultant, distincte du rattachement de "
                 "contrôles (roue NIST CSF) : ce radar reflète un jugement professionnel, "
                 "pas une mesure de couverture."),
    }
