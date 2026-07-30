"""tprm.py — criticité des tiers, scindée selon le volet de la mission (§14.1bis).

Décision tranchée du spec, avec justification chiffrée vérifiée sur les données
pré-remplies :

  * **Consulting** (EBIOS RM atelier 3) — formule ANSSI :
        (dépendance × pénétration) / (maturité × confiance)
    soit *exposition* rapportée à *fiabilité cyber*. Restituée par le radar des
    parties prenantes.

  * **GRC** (DORA / NIS2) — **aucun scoring EBIOS** : ces référentiels ne s'en
    réclament pas. On leur substitue des exigences de conformité vérifiables
    (registre d'information DORA Art. 28.3, clauses contractuelles Art. 30,
    stratégie de sortie, évaluation avant acquisition NIST ID.RA-10).

Pourquoi abandonner la moyenne arithmétique employée jusqu'ici : elle compresse
les écarts et empêche donc de prioriser, ce qui est pourtant l'objet même de
l'atelier. Sur les tiers pré-remplis, elle donne 3,50 à l'hébergeur et 3,75 à
l'ESN — indistinguables. Le ratio ANSSI donne 1,56 et 2,22, un écart de 1,4×
méthodologiquement fondé (l'ESN a plus de pénétration pour moins de maturité et
de confiance), et fait tomber le cabinet comptable de 2,25 à 0,25.

Les notes déjà calculées ne sont **jamais** recalculées en silence : un
consultant a pu présenter une criticité à son client. Chaque tiers porte donc
la méthode qui l'a produit, et le passage au ratio ANSSI est une action
explicite (cf. `recalculer_mission`).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

METHODE_ANSSI = "ratio_anssi"
METHODE_HISTORIQUE = "moyenne_historique"

# Seuils de bande appliqués au ratio. La *formule* est celle de l'ANSSI ; le
# découpage en quatre bandes est une convention produit, pas une norme — d'où
# des repères lisibles plutôt que des décimales arbitraires :
#   ≥ 4  l'exposition vaut au moins 4× la fiabilité cyber du tiers
#   ≥ 2  elle en vaut le double
#   ≥ 1  elle l'égale ou la dépasse
#   < 1  la fiabilité l'emporte
SEUILS_ANSSI = ((4.0, "Critique"), (2.0, "Élevé"), (1.0, "Moyen"))

# Exigences de conformité substituées au scoring sur le volet GRC.
EXIGENCES_GRC = (
    {"id": "DORA-28.3", "libelle": "Inscrit au registre d'information (DORA Art. 28.3)"},
    {"id": "DORA-30", "libelle": "Clauses contractuelles obligatoires signées (DORA Art. 30)"},
    {"id": "SORTIE", "libelle": "Stratégie de sortie documentée et testable"},
    {"id": "NIST-ID.RA-10", "libelle": "Évaluation réalisée avant acquisition (NIST ID.RA-10)"},
)


def _arrondi(valeur: float) -> float:
    """Arrondi au dixième, moitié vers le haut — cohérent avec l'affichage."""
    return float(Decimal(str(valeur)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def ratio_anssi(dependence: int, penetration: int, maturity: int, trust: int) -> dict:
    """Criticité d'un tiers selon la formule ANSSI (volet Consulting)."""
    denominateur = max(1, int(maturity)) * max(1, int(trust))
    score = _arrondi((int(dependence) * int(penetration)) / denominateur)

    rating = "Faible"
    for seuil, libelle in SEUILS_ANSSI:
        if score >= seuil:
            rating = libelle
            break

    return {
        "dependence": int(dependence), "penetration": int(penetration),
        "maturity": int(maturity), "trust": int(trust),
        "score": score, "rating": rating, "methode": METHODE_ANSSI,
    }


def exigences_par_defaut() -> list[dict]:
    """Check-list de conformité d'un tiers sur le volet GRC, non cochée."""
    return [{**e, "satisfait": False, "preuve": ""} for e in EXIGENCES_GRC]


def conformite(tier: dict) -> dict:
    """Avancement de conformité d'un tiers GRC — aucun score de risque."""
    exigences = tier.get("exigences") or []
    satisfaites = sum(1 for e in exigences if e.get("satisfait"))
    total = len(exigences)
    return {
        "satisfaites": satisfaites,
        "total": total,
        "taux": round(satisfaites / total * 100) if total else 0,
        "conforme": total > 0 and satisfaites == total,
    }


def tiers_a_recalculer(state: dict) -> list[str]:
    """Tiers encore notés à l'ancienne méthode, sur une mission Consulting.

    Sert à proposer le recalcul sans l'imposer : la criticité d'un tiers a pu
    être présentée au client sous l'ancienne méthode.
    """
    if state.get("type") == "grc":
        return []
    tiers = ((state.get("steps") or {}).get("tprm") or {}).get("tiers") or []
    return [t.get("name", "") for t in tiers if t.get("methode") != METHODE_ANSSI]


def recalculer_mission(state: dict) -> tuple[dict, int]:
    """Repasse tous les tiers d'une mission au ratio ANSSI. Action explicite."""
    tiers = ((state.get("steps") or {}).get("tprm") or {}).get("tiers") or []
    recalcules = 0
    for tier in tiers:
        if tier.get("methode") == METHODE_ANSSI:
            continue
        tier.update(ratio_anssi(
            tier.get("dependence", 3), tier.get("penetration", 3),
            tier.get("maturity", 3), tier.get("trust", 3),
        ))
        recalcules += 1
    return state, recalcules
