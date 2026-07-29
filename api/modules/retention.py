"""retention.py — conservation et purge des données personnelles (F17).

GREEN SHIELD vend du registre Art. 30 à ses clients ; il doit tenir le même
standard sur ses propres traitements. Les grilles d'entretien collectent des
**noms, fonctions et déclarations de personnes physiques** : le consultant est
responsable de traitement pour ces données, avec les obligations qui vont avec
— durée de conservation définie, et suppression ou restitution en fin de
mission (souvent une obligation contractuelle en plus d'une obligation légale).

Principe de la purge : **minimisation, pas destruction**. On efface les données
identifiantes des personnes interrogées ; on garde les constats d'audit, qui ne
sont pas des données personnelles et constituent la valeur du travail. Une
mission purgée reste exploitable, elle ne désigne simplement plus personne.
"""
from __future__ import annotations

from datetime import date, timedelta

# 36 mois : ordre de grandeur usuel pour une mission d'audit (durée de la
# relation contractuelle + délai de prescription courant). Reste modifiable
# mission par mission — c'est au consultant de fixer sa politique.
DUREE_CONSERVATION_DEFAUT_MOIS = 36

# Champs porteurs de données personnelles, avec la clé à neutraliser.
# `None` signifie « vider entièrement la collection ».
CHAMPS_PERSONNELS = (
    ("socle", "entretiens", None),
    ("socle", "kickoff", "participants"),
)


def _ajouter_mois(depart: date, mois: int) -> date:
    """Ajoute des mois à une date sans dépendance externe.

    Ramène au dernier jour du mois cible quand le jour n'existe pas
    (31 janvier + 1 mois -> 28 ou 29 février).
    """
    total = depart.month - 1 + mois
    annee = depart.year + total // 12
    mois_cible = total % 12 + 1
    jour = min(depart.day, _jours_dans_le_mois(annee, mois_cible))
    return date(annee, mois_cible, jour)


def _jours_dans_le_mois(annee: int, mois: int) -> int:
    if mois == 12:
        suivant = date(annee + 1, 1, 1)
    else:
        suivant = date(annee, mois + 1, 1)
    return (suivant - timedelta(days=1)).day


def politique(state: dict) -> dict:
    """Politique de conservation d'une mission, valeurs par défaut comprises."""
    rgpd = (state.get("socle") or {}).get("rgpd_consultant") or {}
    return {
        "duree_conservation_mois": int(rgpd.get("duree_conservation_mois") or DUREE_CONSERVATION_DEFAUT_MOIS),
        "date_fin_mission": rgpd.get("date_fin_mission") or "",
        "purge_effectuee_le": rgpd.get("purge_effectuee_le") or "",
    }


def echeance(state: dict) -> dict:
    """Situation de la mission au regard de sa politique de conservation.

    Tant que la fin de mission n'est pas déclarée, aucune échéance ne court :
    le délai de conservation part de la fin de la relation, pas de son début.
    """
    p = politique(state)

    if p["purge_effectuee_le"]:
        return {**p, "date_purge_prevue": "", "statut": "purgee", "jours_restants": None}

    if not p["date_fin_mission"]:
        return {**p, "date_purge_prevue": "", "statut": "mission_en_cours", "jours_restants": None}

    try:
        fin = date.fromisoformat(p["date_fin_mission"])
    except ValueError:
        return {**p, "date_purge_prevue": "", "statut": "date_invalide", "jours_restants": None}

    prevue = _ajouter_mois(fin, p["duree_conservation_mois"])
    restants = (prevue - date.today()).days
    return {
        **p,
        "date_purge_prevue": prevue.isoformat(),
        "statut": "echue" if restants <= 0 else "en_conservation",
        "jours_restants": restants,
    }


def compter_donnees_personnelles(state: dict) -> int:
    """Nombre d'enregistrements identifiants encore présents dans la mission."""
    total = 0
    for racine, cle, sous_cle in CHAMPS_PERSONNELS:
        conteneur = (state.get(racine) or {}).get(cle)
        if sous_cle is None:
            total += len(conteneur or [])
        elif isinstance(conteneur, dict):
            total += len(conteneur.get(sous_cle) or [])
    return total


def purger(state: dict) -> tuple[dict, int]:
    """Efface les données personnelles de la mission. Renvoie (état, nombre effacé).

    Les constats d'audit, l'inventaire et le plan de traitement sont conservés :
    ce ne sont pas des données personnelles et ils portent la valeur du travail.
    """
    efface = compter_donnees_personnelles(state)

    for racine, cle, sous_cle in CHAMPS_PERSONNELS:
        conteneur = state.setdefault(racine, {})
        if sous_cle is None:
            conteneur[cle] = []
        else:
            sous = conteneur.setdefault(cle, {})
            if isinstance(sous, dict):
                sous[sous_cle] = []

    rgpd = state.setdefault("socle", {}).setdefault("rgpd_consultant", {})
    rgpd["purge_effectuee_le"] = date.today().isoformat()
    return state, efface
