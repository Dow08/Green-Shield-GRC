"""preuves.py — bibliothèque de preuves multi-référentiels (G3bis).

Une preuve de conformité écrite une fois (ex. une politique de sécurité,
un contrat de sous-traitance conforme) sert souvent plusieurs référentiels
actifs d'une même mission — ISO 27001, DORA et NIS2 peuvent chacun exiger
une trace de la même politique. Jusqu'ici `manual_controls` ne portait qu'un
champ `notes` libre par contrôle, sans lien vers les autres : chaque
référentiel obligeait à ressaisir la même preuve.

Contrairement à `soa.py`, il n'y a pas de catalogue figé ici : les preuves
sont saisies par le consultant au fil de la mission, jamais préchargées
(zéro invention — aucune preuve n'est présumée exister).
"""
from __future__ import annotations


def couverture(preuves: list[dict], manual_controls: list[dict]) -> dict:
    """Combien de contrôles manuels ont au moins une preuve liée.

    Ne juge pas la qualité de la preuve, seulement sa présence — la lecture
    reste au consultant.
    """
    lies = {
        (lien.get("referentiel_id"), lien.get("control_id"))
        for p in preuves for lien in (p.get("controles_lies") or [])
    }
    total = len(manual_controls)
    couverts = sum(1 for c in manual_controls if (c.get("referentiel_id"), c.get("id")) in lies)
    return {
        "total": total,
        "couverts": couverts,
        "non_couverts": total - couverts,
        "taux": round(couverts / total * 100) if total else 0,
    }


import difflib

def preuves_pour_controle(preuves: list[dict], referentiel_id: str, control_id: str) -> list[dict]:
    """Les preuves liées à un contrôle précis, dans l'ordre de saisie."""
    return [
        p for p in preuves
        if any(l.get("referentiel_id") == referentiel_id and l.get("control_id") == control_id
               for l in p.get("controles_lies") or [])
    ]

def suggestions_reutilisation(state: dict) -> list[dict]:
    """Suggère de réutiliser une preuve pour d'autres contrôles par similarité de titre (Lot F).
    
    Ne suggère que des contrôles :
    - Non encore liés à cette preuve
    - Appartenant à un référentiel différent de ceux déjà couverts par la preuve
    - Ayant une similarité sémantique > 0.6 avec l'intitulé du contrôle déjà couvert.
    """
    evaluation = state.get("steps", {}).get("evaluation", {}) or {}
    preuves = evaluation.get("preuves") or []
    controles = evaluation.get("manual_controls") or []
    
    if not preuves or not controles:
        return []

    # Map pour accès rapide : (ref_id, ctrl_id) -> title
    ctrl_titles = {
        (c.get("referentiel_id"), c.get("id")): c.get("title", "")
        for c in controles
    }
    
    suggestions = []
    
    for preuve in preuves:
        lies = preuve.get("controles_lies") or []
        if not lies:
            continue
            
        lies_set = {(l.get("referentiel_id"), l.get("control_id")) for l in lies}
        ref_lies = {l.get("referentiel_id") for l in lies}
        
        # Titres des contrôles déjà couverts par cette preuve
        titres_couverts = [ctrl_titles.get((l.get("referentiel_id"), l.get("control_id")), "") for l in lies]
        
        for c in controles:
            ref_c = c.get("referentiel_id")
            id_c = c.get("id")
            title_c = c.get("title", "")
            
            # Ne pas suggérer si le contrôle est déjà couvert par cette preuve
            if (ref_c, id_c) in lies_set:
                continue
                
            # Pour la suggestion (cross-referentiel), on cherche dans un autre référentiel
            if ref_c in ref_lies:
                continue
                
            # Vérifier la similarité avec l'un des titres déjà couverts
            meilleur_ratio = 0
            for t_couvert in titres_couverts:
                if not t_couvert or not title_c:
                    continue
                ratio = difflib.SequenceMatcher(None, t_couvert.lower(), title_c.lower()).ratio()
                if ratio > meilleur_ratio:
                    meilleur_ratio = ratio
                    
            if meilleur_ratio > 0.55: # Seuil empirique de similarité
                suggestions.append({
                    "preuve_id": preuve.get("id"),
                    "preuve_libelle": preuve.get("libelle"),
                    "controle_suggere": {
                        "referentiel_id": ref_c,
                        "control_id": id_c,
                        "title": title_c,
                        "referentiel_name": c.get("referentiel_name")
                    },
                    "confiance": round(meilleur_ratio * 100)
                })
                
    # Trier par confiance décroissante
    suggestions.sort(key=lambda s: s["confiance"], reverse=True)
    return suggestions

