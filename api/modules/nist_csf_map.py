"""nist_csf_map.py — rattachement des contrôles d'une mission aux six fonctions
du NIST Cybersecurity Framework 2.0 (Govern, Identify, Protect, Detect,
Respond, Recover).

Sert la « roue NIST » du tableau de bord, à la manière de CISO Assistant :
une vue d'ensemble de ce que la mission couvre, fonction par fonction.

Deux modes, et la distinction est une question d'honnêteté :

  * **direct** — la mission a NIST CSF parmi ses référentiels actifs. Les
    contrôles évalués SONT des codes NIST (GV.RM-01, PR.AA-03…) ; le
    rattachement est exact et complet.

  * **indicatif** — mission ISO 27001 ou DORA. Le rattachement passe par le
    catalogue de mesures (`mesures_catalogue.yaml`), qui relie chaque mesure à
    la fois à ISO/DORA et à NIST. Ce pont ne couvre qu'une partie des
    contrôles : un segment faible ou vide reflète alors la portée du catalogue,
    pas nécessairement une faiblesse de l'organisation. Le module le dit
    explicitement plutôt que d'afficher un « 0 % » trompeur.

Règle « zéro invention » : aucun score de maturité n'est fabriqué. Le taux
d'une fonction est la part de ses contrôles rattachés qui sont effectivement
couverts (implémentés / conformes). Sans contrôle rattaché, le taux est `None`
et non zéro — l'absence de donnée n'est pas une note de zéro.
"""
from __future__ import annotations

from . import mesures_catalogue

# Ordre canonique du CSF 2.0 : Govern au centre, puis les cinq fonctions
# opérationnelles dans le sens de la roue officielle.
FONCTIONS = [
    ("GV", "Gouverner"),
    ("ID", "Identifier"),
    ("PR", "Protéger"),
    ("DE", "Détecter"),
    ("RS", "Répondre"),
    ("RC", "Rétablir"),
]
_CODES_FONCTIONS = [code for code, _ in FONCTIONS]

# Statuts SoA (mission ISO) considérés comme « couverts ». « Partiel » et
# « Planifié » comptent comme rattachés mais non couverts : la distinction est
# le cœur de l'information.
_SOA_COUVERT = ("Implémenté", "Implemente", "Implémentée")
_SOA_DECIDE = _SOA_COUVERT + ("Partiel", "Planifié", "Planifie")

# Statuts des contrôles manuels (mode direct NIST) considérés couverts.
_CONTROLE_COUVERT = ("CONFORME",)
_CONTROLE_DECIDE = _CONTROLE_COUVERT + ("NON_CONFORME", "A_VERIFIER")


def _fonction_de(code_nist: str) -> str | None:
    """Fonction NIST d'un code : les deux premières lettres (GV.RM-01 -> GV)."""
    prefixe = (code_nist or "")[:2].upper()
    return prefixe if prefixe in _CODES_FONCTIONS else None


def _index_referentiel_vers_nist(referentiel_id: str) -> dict[str, set[str]]:
    """Code du référentiel donné -> ensemble de fonctions NIST, via le catalogue.

    Construit à la demande : le catalogue est petit (19 mesures) et cette table
    ne sert qu'à l'affichage de la roue.
    """
    index: dict[str, set[str]] = {}
    for mesure in mesures_catalogue.list_mesures():
        mappings = mesure.get("mappings") or {}
        fonctions = {f for f in (_fonction_de(c) for c in mappings.get("nist_csf", [])) if f}
        if not fonctions:
            continue
        for code in mappings.get(referentiel_id, []):
            index.setdefault(code, set()).update(fonctions)
    return index


def _referentiels_actifs(state: dict) -> list[str]:
    grc = state.get("grc") or {}
    actifs = grc.get("referentiels_actifs") or []
    if actifs:
        return actifs
    cadrage = (state.get("steps") or {}).get("cadrage") or {}
    return cadrage.get("framework_ids") or ([cadrage["framework_id"]] if cadrage.get("framework_id") else [])


def _roue_vide() -> dict:
    return {code: {"rattaches": 0, "couverts": 0, "codes": []} for code, _ in FONCTIONS}


def _rattacher_direct(state: dict) -> dict:
    """Mission NIST : les contrôles portent directement un code de fonction."""
    roue = _roue_vide()
    controles = ((state.get("steps") or {}).get("evaluation") or {}).get("manual_controls") or []
    for controle in controles:
        if controle.get("referentiel_id") != "nist_csf":
            continue
        fonction = _fonction_de(controle.get("id", ""))
        if not fonction or controle.get("status") not in _CONTROLE_DECIDE:
            continue
        roue[fonction]["rattaches"] += 1
        roue[fonction]["codes"].append(controle.get("id"))
        if controle.get("status") in _CONTROLE_COUVERT:
            roue[fonction]["couverts"] += 1
    return roue


def _rattacher_indicatif(state: dict, referentiels: list[str]) -> dict:
    """Mission ISO/DORA : rattachement via le catalogue de mesures.

    Source privilégiée : la SoA (codes fins concordant avec le catalogue). À
    défaut, les contrôles manuels — mais leurs identifiants thématiques
    (« ISO-A.5 ») concordent rarement, d'où une roue plus pauvre.
    """
    roue = _roue_vide()
    evaluation = (state.get("steps") or {}).get("evaluation") or {}

    if "iso27001" in referentiels:
        index = _index_referentiel_vers_nist("iso27001")
        for entree in evaluation.get("soa") or []:
            statut = entree.get("statut")
            if statut not in _SOA_DECIDE:
                continue
            for fonction in index.get(entree.get("code"), set()):
                roue[fonction]["rattaches"] += 1
                roue[fonction]["codes"].append(entree.get("code"))
                if statut in _SOA_COUVERT:
                    roue[fonction]["couverts"] += 1

    for ref in ("dora", "nis2"):
        if ref not in referentiels:
            continue
        index = _index_referentiel_vers_nist(ref)
        for controle in evaluation.get("manual_controls") or []:
            if controle.get("referentiel_id") != ref or controle.get("status") not in _CONTROLE_DECIDE:
                continue
            for fonction in index.get(controle.get("id"), set()):
                roue[fonction]["rattaches"] += 1
                roue[fonction]["codes"].append(controle.get("id"))
                if controle.get("status") in _CONTROLE_COUVERT:
                    roue[fonction]["couverts"] += 1
    return roue


def carte(state: dict) -> dict:
    """Construit la roue NIST d'une mission.

    Retourne le mode, les six fonctions (chacune avec son taux de couverture ou
    `None`), et une note d'honnêteté sur la portée du rattachement.
    """
    referentiels = _referentiels_actifs(state)
    direct = "nist_csf" in referentiels

    roue = _rattacher_direct(state) if direct else _rattacher_indicatif(state, referentiels)

    fonctions = []
    for code, libelle in FONCTIONS:
        r = roue[code]
        rattaches = r["rattaches"]
        # Taux = part couverte des rattachés ; None si rien n'est rattaché, pour
        # ne pas confondre « non mesuré » avec « 0 % couvert ».
        taux = round(100 * r["couverts"] / rattaches) if rattaches else None
        fonctions.append({
            "code": code,
            "libelle": libelle,
            "rattaches": rattaches,
            "couverts": r["couverts"],
            "taux": taux,
            # Dédoublonnés et triés : un même code peut être atteint par
            # plusieurs mesures du catalogue.
            "codes": sorted(set(r["codes"])),
        })

    if direct:
        note = ("Rattachement direct : cette mission évalue le NIST CSF, la roue "
                "reflète l'état réel de ses contrôles.")
    else:
        note = ("Rattachement indicatif via le catalogue de mesures. Il ne couvre "
                "qu'une partie des contrôles : une fonction peu ou pas remplie "
                "traduit la portée de ce pont, pas forcément une faiblesse.")

    return {
        "mode": "direct" if direct else "indicatif",
        "referentiels": referentiels,
        "fonctions": fonctions,
        "total_rattaches": sum(f["rattaches"] for f in fonctions),
        "note": note,
    }
