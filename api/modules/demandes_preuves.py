"""demandes_preuves.py — registre des documents réclamés au client.

Le point noir d'un audit réel n'est pas d'analyser les preuves, c'est de les
obtenir : réclamer un document, identifier le bon interlocuteur, relancer,
constater à la restitution qu'il n'est jamais arrivé. Faute d'outil, le
consultant tient ce suivi dans un tableur à côté — donc l'application ne
remplace pas son tableur.

Ce module vit dans le **socle de mission** (et non dans les phases) : il
relève de la conduite de mission, pas du contenu de l'audit. Une demande sans
réponse est un fait de gestion, pas un constat de conformité.

Règle « zéro invention » : une demande non satisfaite reste visible comme
telle. Elle ne devient jamais une preuve tant que le document n'est pas reçu,
et le module ne suppose jamais qu'un document « a dû » arriver.

Aucun verdict de conformité n'est produit ici : le registre dit qui doit quoi
et depuis quand, rien de plus.
"""
from __future__ import annotations

from datetime import date, datetime

# Cycle de vie d'une demande. `refusee` couvre le cas réel où le client
# indique qu'il ne fournira pas le document (confidentialité, inexistence) :
# c'est une réponse, pas une absence, et le livrable doit les distinguer.
STATUTS = ("demandee", "relancee", "recue", "refusee")

LIBELLES_STATUT = {
    "demandee": "Demandée",
    "relancee": "Relancée",
    "recue": "Reçue",
    "refusee": "Refusée par le client",
}

# Au-delà, une demande sans réponse mérite d'être signalée au consultant.
# Valeur retenue avec les praticiens : en dessous d'une semaine, un silence
# n'a rien d'anormal.
DELAI_RELANCE_JOURS = 7

_STATUTS_OUVERTS = ("demandee", "relancee")


def _aujourdhui() -> date:
    return date.today()


def _en_date(valeur: str | None) -> date | None:
    if not valeur:
        return None
    try:
        return datetime.strptime(valeur[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def liste(state: dict) -> list[dict]:
    """Demandes enregistrées sur la mission, dans l'ordre de saisie."""
    socle = state.get("socle") or {}
    demandes = socle.get("demandes_preuves") or []
    return [d for d in demandes if isinstance(d, dict)]


def jours_depuis_demande(demande: dict, aujourdhui: date | None = None) -> int | None:
    """Ancienneté en jours, ou None si la date est absente ou illisible.

    On compte depuis la dernière relance quand il y en a eu une : c'est le
    délai que le client a réellement laissé passer depuis le dernier signal.
    """
    reference = _en_date(demande.get("date_relance")) or _en_date(demande.get("date_demande"))
    if reference is None:
        return None
    return ((aujourdhui or _aujourdhui()) - reference).days


def est_en_attente(demande: dict) -> bool:
    return demande.get("statut") in _STATUTS_OUVERTS


def a_relancer(demande: dict, aujourdhui: date | None = None) -> bool:
    """Demande ouverte, sans nouvelle depuis plus que le délai admis."""
    if not est_en_attente(demande):
        return False
    jours = jours_depuis_demande(demande, aujourdhui)
    return jours is not None and jours >= DELAI_RELANCE_JOURS


def synthese(state: dict, aujourdhui: date | None = None) -> dict:
    """Vue d'ensemble pour l'écran de mission et la revue avant export."""
    demandes = liste(state)
    en_attente = [d for d in demandes if est_en_attente(d)]
    relances = [d for d in en_attente if a_relancer(d, aujourdhui)]

    # La plus ancienne demande ouverte : c'est elle qui met la restitution en
    # danger, pas le volume total.
    anciennetes = [j for j in (jours_depuis_demande(d, aujourdhui) for d in en_attente) if j is not None]

    return {
        "total": len(demandes),
        "en_attente": len(en_attente),
        "recues": sum(1 for d in demandes if d.get("statut") == "recue"),
        "refusees": sum(1 for d in demandes if d.get("statut") == "refusee"),
        "a_relancer": len(relances),
        "plus_ancienne_jours": max(anciennetes) if anciennetes else None,
        "delai_relance_jours": DELAI_RELANCE_JOURS,
    }


def manques_pour_revue(state: dict, aujourdhui: date | None = None) -> list[dict]:
    """Alimente la revue avant export.

    Une demande en attente est signalée en « recommandé » et non en
    « bloquant » : le consultant peut légitimement livrer un rapport en
    mentionnant qu'une pièce n'a jamais été fournie. Le bloquer serait lui
    imposer une exhaustivité que le client seul peut lui accorder.
    """
    en_attente = [d for d in liste(state) if est_en_attente(d)]
    if not en_attente:
        return []

    libelles = ", ".join(d.get("libelle", "sans libellé") for d in en_attente[:3])
    if len(en_attente) > 3:
        libelles += f" (+{len(en_attente) - 3})"

    return [{
        "phase": 0,
        "phase_libelle": "Socle de mission",
        "champ": f"{len(en_attente)} demande(s) de preuve sans réponse : {libelles}",
        "gravite": "recommande",
    }]


def controles_sans_preuve_ni_demande(state: dict) -> list[dict]:
    """Contrôles évalués qui n'ont ni preuve rattachée, ni demande en cours.

    C'est l'angle mort que le registre sert à fermer : un contrôle jugé
    conforme sans preuve et sans document réclamé signale soit un oubli de
    saisie, soit un jugement sur déclaratif. Le module se contente de le
    remonter — l'interprétation appartient au consultant.
    """
    evaluation = (state.get("steps") or {}).get("evaluation") or {}
    controles = evaluation.get("manual_controls") or []
    preuves = evaluation.get("preuves") or []

    couverts = {
        (lien.get("referentiel_id"), lien.get("control_id"))
        for preuve in preuves
        for lien in (preuve.get("controles_lies") or [])
    }
    demandes_ouvertes = {
        (lien.get("referentiel_id"), lien.get("control_id"))
        for demande in liste(state)
        if est_en_attente(demande)
        for lien in (demande.get("controles_lies") or [])
    }

    orphelins = []
    for controle in controles:
        # Un contrôle non conforme n'a pas besoin de preuve : c'est l'absence
        # qui est constatée. Seul un verdict positif appelle une pièce.
        if controle.get("status") != "CONFORME":
            continue
        cle = (controle.get("referentiel_id"), controle.get("id"))
        if cle in couverts or cle in demandes_ouvertes:
            continue
        orphelins.append({
            "referentiel_id": controle.get("referentiel_id"),
            "control_id": controle.get("id"),
            "titre": controle.get("title", ""),
        })
    return orphelins
