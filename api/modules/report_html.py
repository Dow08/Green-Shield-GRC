"""report_html.py — rapport de mission au format HTML, prêt à imprimer.

Raison d'être : les exports Markdown embarquaient un en-tête HTML + CSS et un
logo en `data:` URI. Le résultat ne rendait correctement nulle part (constaté le
30/07/2026) — GitHub retire les feuilles de style et bloque les images `data:`,
tandis qu'un navigateur affiche les tableaux Markdown en texte brut, tuyaux
compris. Les maquettes validées le même jour décrivaient pourtant une mise en
page précise : page de garde sombre, sommaire, chapitres numérotés, tableaux
tramés.

Ce module produit cette mise en page. Un seul fichier HTML autonome, sans
ressource externe (contrainte hors-ligne du projet), imprimable en A4 via
`@page` et donc convertible en PDF par le navigateur — sans ajouter de
dépendance native, ce que la règle n°1 du projet interdit.

Aucune donnée n'est inventée : les sections vides sont annoncées comme telles,
exactement comme dans l'export Markdown, dont ce module réutilise les données
sources et non le texte formaté.
"""
from __future__ import annotations

from datetime import datetime
from html import escape

from . import aipd as aipd_module
from . import charte
from . import controles_techniques
from . import couverture
from . import docx_export
from . import soa
from . import tprm

# Même défaut neutre que `report_docx.py` — l'application sert n'importe quel
# consultant, jamais un nom de cabinet écrit en dur (retour utilisateur du
# 30/07/2026).
_CABINET_DEFAUT = "Cabinet non renseigné"

# Bandes de sévérité : mêmes teintes que l'application (web/src/index.css),
# déclinées sur fond papier. Sans underscore : `report_docx.py` la réutilise
# pour que les deux formats classent les mêmes statuts de la même façon.
CLASSE_SEV = {
    "Critique": "crit", "Élevé": "elev", "Moyen": "moy", "Faible": "faib",
    "CONFORME": "ok", "NON_CONFORME": "crit", "PARTIEL": "elev",
    "A_VERIFIER": "faib", "NON_APPLICABLE": "faib",
}


def _t(valeur) -> str:
    """Échappe pour le HTML. Une valeur absente devient un tiret cadratin."""
    texte = "" if valeur is None else str(valeur).strip()
    return escape(texte) if texte else "—"


def _vide(message: str) -> str:
    return f'<p class="vide">{escape(message)}</p>'


def _sev(valeur) -> str:
    """Pastille de sévérité, ou texte simple si la valeur n'en est pas une."""
    brut = "" if valeur is None else str(valeur).strip()
    if not brut:
        return "—"
    classe = CLASSE_SEV.get(brut)
    libelle = docx_export.STATUS_LABELS.get(brut, brut)
    if not classe:
        return escape(libelle)
    return f'<span class="sev sev-{classe}">{escape(libelle)}</span>'


def _table(entetes: tuple, lignes: list[tuple], message_vide: str,
           colonnes_num: tuple[int, ...] = (), colonnes_sev: tuple[int, ...] = ()) -> str:
    """Tableau HTML, ou une phrase explicite quand il n'y a rien à montrer.

    Un tableau à en-têtes sans aucune ligne promet au lecteur un contenu qu'il
    ne livre pas : c'est le défaut que la recette du 29/07/2026 a relevé.
    """
    if not lignes:
        return _vide(message_vide)

    th = "".join(
        f'<th{" class=\'num\'" if i in colonnes_num else ""}>{escape(e)}</th>'
        for i, e in enumerate(entetes)
    )
    corps = ""
    for ligne in lignes:
        cellules = ""
        for i, valeur in enumerate(ligne):
            if i in colonnes_sev:
                cellules += f"<td>{_sev(valeur)}</td>"
            elif i in colonnes_num:
                cellules += f'<td class="num">{_t(valeur)}</td>'
            else:
                cellules += f"<td>{_t(valeur)}</td>"
        corps += f"<tr>{cellules}</tr>"
    return f'<div class="tscroll"><table><thead><tr>{th}</tr></thead><tbody>{corps}</tbody></table></div>'


# --- Chapitres --------------------------------------------------------------

def _synthese(state: dict) -> str:
    resume = ((state.get("steps") or {}).get("restitution") or {}).get("exec_summary") or ""
    if not resume.strip():
        return _vide("Synthèse non rédigée. Elle se saisit en phase 6 et n'est jamais produite "
                     "automatiquement : elle engage le jugement du consultant.")
    paragraphes = "".join(f"<p>{escape(p.strip())}</p>"
                          for p in resume.split("\n") if p.strip())
    return f'<div class="chapeau">{paragraphes}</div>'


def _cadrage(state: dict) -> str:
    socle = state.get("socle") or {}
    q, c, k = (socle.get("qualification") or {}, socle.get("contractualisation") or {},
               socle.get("kickoff") or {})
    champs = (
        ("Déclencheur de la mission", q.get("declencheur")),
        ("Sponsor exécutif", q.get("sponsor_executif")),
        ("Budget vendu", q.get("budget")),
        ("Maturité constatée à l'entrée", q.get("maturite_actuelle")),
        ("Équipe interne mobilisable", q.get("equipe_interne")),
        ("Échéance cible", q.get("echeance_cible")),
        ("Périmètre inclus", c.get("perimetre_inclus")),
        ("Périmètre explicitement exclu", c.get("perimetre_exclu")),
        ("Modalités d'intervention", c.get("modalites")),
        ("Accès au SI consentis", c.get("acces_si")),
        ("Date de réunion de lancement", k.get("date")),
        ("Gouvernance de la mission", k.get("gouvernance")),
    )
    lignes = [(lib, val) for lib, val in champs if str(val or "").strip()]
    for libelle, liste in (("Livrables contractuels", c.get("livrables")),
                           ("Participants au lancement", k.get("participants"))):
        if liste:
            lignes.append((libelle, " · ".join(str(x) for x in liste)))
    return _table(("Élément de cadrage", "Contenu"), lignes,
                  "Le cadrage contractuel de la mission n'a pas été renseigné.")


def _entretiens(state: dict) -> str:
    entretiens = (state.get("socle") or {}).get("entretiens") or []
    return _table(
        ("Rôle rencontré", "Date", "Ce qui a été déclaré"),
        [(e.get("role"), e.get("date"), e.get("synthese")) for e in entretiens],
        "Aucun entretien n'a été consigné : les constats de ce rapport ne sont pas "
        "rattachés à une source déclarative identifiée.",
    )


def _patrimoine(steps: dict, prefixe: str = "3") -> str:
    cadrage = steps.get("cadrage") or {}
    metier = _table(
        ("ID", "Valeur métier", "Description", "Données personnelles"),
        [(a.get("id"), a.get("name"), a.get("description"),
          "Oui" if a.get("is_personal_data") else "Non")
         for a in cadrage.get("assets_metier") or []],
        "Aucune valeur métier n'a été cartographiée.",
    )
    support = _table(
        ("ID", "Bien support", "Type", "Description", "Responsable"),
        [(a.get("id"), a.get("name"), a.get("type"), a.get("description"), a.get("owner"))
         for a in cadrage.get("assets_support") or []],
        "Aucun bien support n'a été inventorié.",
    )
    return (f'<h3>{prefixe}.1 Valeurs métier</h3>{metier}'
            f'<h3>{prefixe}.2 Biens supports</h3>{support}')


def _evaluation(steps: dict) -> str:
    controles = (steps.get("evaluation") or {}).get("manual_controls") or []
    tableau = _table(
        ("ID", "Référentiel", "Exigence organisationnelle", "Statut", "Constat et preuve"),
        [(c.get("id"), c.get("referentiel_name") or c.get("referentiel_id"), c.get("title"),
          c.get("status"), c.get("notes")) for c in controles],
        "Aucune check-list de conformité n'est rattachée à cette mission : "
        "l'évaluation organisationnelle relève ici de l'analyse de risque du chapitre 5.",
        colonnes_sev=(3,),
    )
    soa_donnees = (steps.get("evaluation") or {}).get("soa") or []
    if not soa_donnees:
        return tableau
    soa_tableau = _table(
        ("Thème", "Total", "Applicables", "Exclus", "Non statués"),
        [(t["theme"], t["total"], t["applicables"], t["exclus"], t["non_statues"])
         for t in soa.par_theme(soa_donnees)],
        "", colonnes_num=(1, 2, 3, 4),
    )
    return (tableau + '<h3 class="sans-num">Déclaration d\'Applicabilité (SoA) — synthèse par thème</h3>'
            '<p class="note">Détail des 93 contrôles de l\'Annexe A dans le livrable dédié '
            '« Déclaration d\'Applicabilité ».</p>' + soa_tableau)


def _risque(steps: dict, prefixe: str = "5") -> str:
    ebios = steps.get("ebios") or {}
    redoutes = _table(
        ("ID", "Événement redouté", "Gravité", "Impacts"),
        [(e.get("id"), e.get("event"), f"{e.get('gravity')}/4", e.get("impact"))
         for e in ebios.get("redoute_events") or []],
        "Aucun événement redouté n'a été caractérisé.", colonnes_num=(2,),
    )
    sources = _table(
        ("ID", "Source de risque", "Objectif visé"),
        [(s.get("id"), s.get("name"), s.get("objective")) for s in ebios.get("risk_sources") or []],
        "Aucune source de risque n'a été caractérisée.",
    )
    scenarios = _table(
        ("ID", "Scénario opérationnel", "G", "V", "Mesure d'atténuation"),
        [(s.get("id"), s.get("event"), f"{s.get('gravity')}/4", f"{s.get('likelihood')}/5",
          s.get("mitigation")) for s in ebios.get("operational_scenarios") or []],
        "Aucun scénario opérationnel n'a été construit.", colonnes_num=(2, 3),
    )
    traitement_risques = _table(
        ("ID", "Propriétaire", "Résiduel (G/V)", "Stratégie", "Statut"),
        [(s.get("id"), s.get("owner"),
          f"{s.get('gravite_residuelle')}/{s.get('vraisemblance_residuelle')}"
          if s.get("gravite_residuelle") is not None and s.get("vraisemblance_residuelle") is not None else None,
          s.get("strategie_traitement"), s.get("statut"))
         for s in ebios.get("operational_scenarios") or []],
        "Aucun scénario opérationnel n'a été construit.",
    )
    cas = _table(
        ("Cas réel", "Enseignement retenu pour ce client"),
        [(c.get("case"), c.get("lessons")) for c in ebios.get("case_studies") or []],
        "Aucun cas comparable n'a été versé au dossier.",
    )
    return (f"<h3>{prefixe}.1 Événements redoutés</h3>{redoutes}"
            f"<h3>{prefixe}.2 Sources de risque</h3>{sources}"
            f"<h3>{prefixe}.3 Scénarios opérationnels</h3>{scenarios}"
            f"<h3>{prefixe}.3bis Traitement des risques (propriétaire, résiduel, décision)</h3>{traitement_risques}"
            f"<h3>{prefixe}.4 Cas réels versés au dossier</h3>{cas}")


def _ecosysteme(state: dict) -> str:
    """Tiers restitués selon le volet (§14.1bis) : ratio ANSSI ou exigences."""
    tiers = ((state.get("steps") or {}).get("tprm") or {}).get("tiers") or []

    if state.get("type") == "grc":
        lignes = []
        for t in tiers:
            etat = tprm.conformite(t)
            manquantes = [e["libelle"] for e in (t.get("exigences") or [])
                          if not e.get("satisfait")]
            lignes.append((t.get("name"), f"{etat['satisfaites']}/{etat['total']} ({etat['taux']} %)",
                           "Conforme" if etat["conforme"] else " ; ".join(manquantes) or "—"))
        note = ("<p class=\"note\">Ce volet ne produit aucun score de risque : ni DORA ni NIS2 "
                "ne se réclament d'EBIOS RM. La conformité se démontre par des preuves.</p>")
        return note + _table(("Prestataire", "Exigences satisfaites", "Écarts restants"), lignes,
                             "Aucun prestataire n'a été inscrit au registre.", colonnes_num=(1,))

    classement = sorted(tiers, key=lambda t: t.get("score", 0), reverse=True)
    note = ('<p class="note">Criticité selon la formule ANSSI : '
            "(dépendance × pénétration) / (maturité × confiance).</p>")
    return note + _table(
        ("Tiers", "Criticité", "Ratio", "Dép. / Pén. / Mat. / Conf."),
        [(t.get("name"), t.get("rating"), t.get("score"),
          f"{t.get('dependence')} / {t.get('penetration')} / "
          f"{t.get('maturity')} / {t.get('trust')}") for t in classement],
        "Aucun tiers n'a été évalué.", colonnes_num=(2, 3), colonnes_sev=(1,),
    )


def _resilience(steps: dict) -> str:
    bcp = (steps.get("resilience") or {}).get("bcp_strategy") or {}
    e3r = (steps.get("resilience") or {}).get("e3r") or {}
    strategie = (steps.get("resilience") or {}).get("strategie_remediation") or {}
    cibles = _table(
        ("Cible de continuité", "Valeur retenue"),
        [(lib, val) for lib, val in (
            ("RTO — durée maximale d'interruption admissible", bcp.get("rto")),
            ("RPO — perte de données maximale admissible", bcp.get("rpo")),
            ("Politique de sauvegarde", bcp.get("backup_policy")),
        ) if str(val or "").strip()],
        "Aucune cible de continuité n'a été définie.",
    )
    sequence = _table(
        ("Étape E3R", "Procédure retenue"),
        [(lib, e3r.get(cle)) for lib, cle in (
            ("Endiguement", "endiguement"), ("Éviction", "eviction"),
            ("Éradication", "eradication"), ("Reconstruction", "reconstruction"),
        ) if str(e3r.get(cle) or "").strip()],
        "La séquence de remédiation E3R n'a pas été documentée.",
    )
    strategique = _table(
        ("Critère d'arbitrage", "Position retenue"),
        [(lib, strategie.get(cle)) for lib, cle in (
            ("Urgence de redémarrage", "urgence_redemarrage"),
            ("Coûts et risques d'un redémarrage précipité", "couts_risques_redemarrage"),
            ("Décision retenue et autorité", "decision_direction"),
        ) if str(strategie.get(cle) or "").strip()],
        "Le volet stratégique (arbitrage Direction) n'a pas été documenté.",
    )
    return (f"<h3>7.1 Cibles de continuité</h3>{cibles}"
            f"<h3>7.2 Séquence de remédiation E3R (ANSSI)</h3>{sequence}"
            f"<h3>7.3 Volet stratégique — arbitrage Direction</h3>{strategique}")


def _technique(state: dict) -> str:
    resultat = couverture.couverture_technique(state)
    phrase = f'<p class="encadre">{escape(couverture.phrase(resultat))}</p>'
    technique = ((state.get("steps") or {}).get("evaluation") or {}).get("technical_results") or {}
    if not technique:
        return phrase + _vide("Aucun scan technique de configuration n'a été exécuté "
                              "pour cette mission.")
    return phrase + _table(
        ("Indicateur", "Valeur"),
        [("Score technique", f"{technique.get('score')} % ({technique.get('band')})"),
         ("Failles critiques", technique.get("critical_count"))],
        "Résultats techniques indisponibles.", colonnes_num=(1,),
    )


def _rattachement(state: dict) -> str:
    resultat = controles_techniques.etat(state)
    lignes = [(p["libelle"],
               ", ".join(f"{m['referentiel']} {m['ref']}" for m in p["mappings"]),
               "Couverte" if p["couverte"] else "Non couverte",
               f"{p['justification']} (phase {p['phase']})")
              for p in resultat["pratiques"]]
    tableau = _table(("Pratique", "Contrôles rattachés", "État", "Constaté en"), lignes,
                     "Aucune pratique n'est rattachée.")
    largeur = resultat["taux"]
    jauge = (f'<div class="jauge-lin" role="img" aria-label="'
             f'{resultat["couvertes"]} pratique(s) couverte(s) sur {resultat["total"]}">'
             f'<i style="width:{largeur}%"></i></div>'
             f'<p class="note">{resultat["couvertes"]} pratique(s) couverte(s) sur '
             f'{resultat["total"]} — {largeur} %.</p>')
    return tableau + jauge


def _traitement(steps: dict, prefixe: str = "11") -> str:
    remediations = (steps.get("traitement") or {}).get("remediations") or []
    ordre = {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}
    triees = sorted(remediations, key=lambda r: ordre.get(r.get("priority"), 9))
    plan = _table(
        ("ID", "Priorité", "Axe", "Mesure de traitement"),
        [(r.get("id"), r.get("priority"), r.get("axe"), r.get("measure")) for r in triees],
        "Aucune mesure de traitement n'a été définie à ce stade.", colonnes_sev=(1,),
    )
    pilotage = _table(
        ("ID", "Responsable", "Échéance", "Statut", "Coût estimé"),
        [(r.get("id"), r.get("responsable"), r.get("echeance"), r.get("statut"), r.get("cout_estime"))
         for r in triees],
        "Aucune mesure de traitement n'a été définie à ce stade.",
    )
    wins = (steps.get("traitement") or {}).get("quick_wins") or []
    immediat = ("<ol class=\"actions\">" + "".join(f"<li>{_t(w)}</li>" for w in wins) + "</ol>"
                if wins else _vide("Aucune action immédiate n'a été retenue."))
    # Bug corrigé le 31/07/2026 : « Plan de traitement » est le chapitre 11
    # (voir CHAPITRES), mais ces sous-titres affichaient « 10.1 »/« 10.2 »
    # depuis l'ajout du chapitre AIPD, qui a décalé toute la numérotation sans
    # que ces deux chaînes codées en dur ne suivent.
    return (f"<h3>{prefixe}.1 Mesures priorisées</h3>{plan}"
            f"<h3>{prefixe}.1bis Pilotage (responsable, échéance, statut)</h3>{pilotage}"
            f"<h3>{prefixe}.2 Actions immédiates</h3>{immediat}")


def _charges(state: dict) -> str:
    socle = state.get("socle") or {}
    entrees = ((socle.get("temps") or {}).get("entrees")) or []
    budget = ((socle.get("qualification") or {}).get("budget")) or ""
    if not entrees:
        return _vide("Aucun temps consommé n'a été saisi pour cette mission.")

    from . import report_builder  # noqa: PLC0415 — libellés et format partagés

    par_phase: dict[str, int] = {}
    for e in entrees:
        cle = e.get("phase", "autre")
        par_phase[cle] = par_phase.get(cle, 0) + int(e.get("minutes") or 0)
    lignes = [(libelle, report_builder._duree_lisible(par_phase[cle]))
              for cle, libelle in report_builder.PHASES_LIBELLES.items() if par_phase.get(cle)]
    lignes.append(("Total", report_builder._duree_lisible(sum(par_phase.values()))))
    tableau = _table(("Phase", "Temps consommé"), lignes,
                     "Aucun temps consommé.", colonnes_num=(1,))
    if budget:
        tableau += f'<p class="note">Budget vendu : <strong>{escape(budget)}</strong></p>'
    return tableau


def _aipd_section(steps: dict) -> str:
    """Chapitre RGPD, présent seulement si une AIPD est due."""
    diagnostic = steps.get("diagnostic") or {}
    registre = _table(
        ("ID", "Traitement", "Finalité", "Catégories de données", "Conservation"),
        [(r.get("id"), r.get("name"), r.get("purpose"), r.get("data_categories"),
          r.get("retention")) for r in diagnostic.get("rgpd_register") or []],
        "Aucun traitement n'a été inscrit au registre.",
    )
    violations = ('<h3>4.1bis Registre des violations de données (Art. 33-34)</h3>' + _table(
        ("ID", "Constatée le", "Nature", "CNIL", "Personnes informées"),
        [(v.get("id"), v.get("date_constat"), v.get("nature"),
          f"Notifiée le {v.get('date_notification_cnil')}" if v.get("notifiee_cnil") else "Non notifiée",
          "Oui" if v.get("personnes_informees") else "Non")
         for v in diagnostic.get("violations") or []],
        "Aucune violation de données n'a été constatée sur cette mission.",
    ))
    if not diagnostic.get("aipd_required"):
        return (registre + violations + _vide("Aucune analyse d'impact n'est requise sur ce périmètre."))

    donnees = diagnostic.get("aipd") or {}
    volets = _table(
        ("Volet d'analyse", "Contenu"),
        [(lib, donnees.get(cle)) for lib, cle in (
            ("Description systématique du traitement", "treatment_description"),
            ("Nécessité et proportionnalité", "necessity_eval"),
            ("Risques pour les droits et libertés", "risks_eval"),
            ("Mesures d'atténuation", "mitigation_measures"),
        )],
        "Les volets d'analyse n'ont pas été renseignés.",
    )
    saisies = {o.get("id"): o for o in donnees.get("obligations") or []}
    etat = aipd_module.etat(donnees)
    lignes = []
    for obligation in aipd_module.OBLIGATIONS:
        if obligation["conditionnelle"] and not etat["art36_requise"]:
            lignes.append((obligation["libelle"], obligation["reference"],
                           "Non applicable (risque résiduel non élevé)", ""))
            continue
        saisie = saisies.get(obligation["id"], {})
        lignes.append((obligation["libelle"], obligation["reference"],
                       "Fait" if saisie.get("satisfait") else "Reste à faire",
                       saisie.get("commentaire")))
    obligations = _table(("Obligation", "Référence", "État", "Commentaire"), lignes,
                         "Aucune obligation renseignée.")
    alerte = aipd_module.alerte_bloquante(donnees)
    bandeau = f'<p class="alerte">{escape(alerte)}</p>' if alerte else ""
    return (f"<h3>4.1 Registre des traitements (RGPD Art. 30)</h3>{registre}"
            f"{violations}"
            f"<h3>4.2 Analyse d'impact — les quatre volets</h3>{volets}"
            f"<h3>4.3 Obligations organisationnelles</h3>{bandeau}{obligations}")


# --- Assemblage -------------------------------------------------------------

# Sans underscore : lu par report_docx.py pour que les deux rendus (HTML et
# Word) partagent le même sommaire — titres et ordre garantis identiques,
# plutôt que deux listes tenues à la main qui auraient fini par diverger
# (c'est exactement ce qui est arrivé à l'ancien gabarit Word, resté à 7
# sections génériques pendant que ce module montait à 13).
CHAPITRES = (
    ("Synthèse à destination de la direction", lambda s, st: _synthese(s)),
    ("Cadrage de la mission", lambda s, st: _cadrage(s) + "<h3>2.1 Entretiens conduits</h3>"
     + _entretiens(s)),
    ("Patrimoine évalué", lambda s, st: _patrimoine(st)),
    ("Protection des données personnelles", lambda s, st: _aipd_section(st)),
    ("Analyse de risque", lambda s, st: _risque(st)),
    ("Écosystème et risques tiers", lambda s, st: _ecosysteme(s)),
    ("Résilience et continuité", lambda s, st: _resilience(st)),
    ("Évaluation organisationnelle", lambda s, st: _evaluation(st)),
    ("Évaluation technique des configurations", lambda s, st: _technique(s)),
    ("Rattachement aux référentiels (CIS v8 / NIST CSF 2.0)", lambda s, st: _rattachement(s)),
    ("Plan de traitement", lambda s, st: _traitement(st)),
    ("Charges consommées", lambda s, st: _charges(s)),
    ("Réserves et limites", lambda s, st: f"<p>{escape(docx_export.mention_reserve(datetime.now().strftime('%d/%m/%Y'), str(s.get('client') or '')))}</p>"),
)


def titre_et_meta(state: dict, p_id: str, auditeur: str, cabinet: str) -> tuple[bool, str, list[tuple[str, str]]]:
    """Titre et bandeau méta du rapport de mission (M1).

    Extrait de `build_report` pour que `report_docx.py` calcule exactement le
    même titre — c'est l'absence de ce point de passage unique qui a produit
    le bug constaté le 31/07/2026 : le gabarit Word affichait « Rapport
    d'audit de conformité » même sur une mission de conseil, le titre y étant
    écrit en dur au lieu d'être dérivé du volet de la mission.
    """
    est_grc = state.get("type") == "grc"
    titre = ("Rapport d'audit de conformité & GRC" if est_grc
             else "Rapport d'audit de sécurité et d'analyse de risque")
    cadrage = (state.get("steps") or {}).get("cadrage") or {}
    referentiel = cadrage.get("framework_name") or cadrage.get("framework_id")

    meta = [("Réf. mission", p_id), ("Méthode", "ISO 27001 / DORA" if est_grc else "EBIOS RM · ANSSI")]
    if referentiel:
        meta.append(("Référentiel", referentiel))
    budget = ((state.get("socle") or {}).get("qualification") or {}).get("budget")
    if budget:
        meta.append(("Budget vendu", budget))
    meta += [("Auditeur", auditeur or "—"), ("Cabinet", cabinet or _CABINET_DEFAUT),
             ("Édition", datetime.now().strftime("%d/%m/%Y"))]
    return est_grc, titre, meta


def build_report(state: dict, p_id: str, auditeur: str = "", cabinet: str = "", logo: str = "") -> tuple[str, str]:
    """Rend le rapport de mission complet. Retourne (nom de fichier, HTML)."""
    est_grc, titre, meta = titre_et_meta(state, p_id, auditeur, cabinet)
    client = str(state.get("client") or "")
    empreinte = docx_export.data_fingerprint(state)

    sommaire = "".join(f"<li>{escape(nom)}</li>" for nom, _ in CHAPITRES)
    corps = ""
    for numero, (nom, rendu) in enumerate(CHAPITRES, 1):
        corps += (f'<section class="chapitre"><h2><span class="num-chap">{numero}</span>'
                  f"{escape(nom)}</h2>{rendu(state, state.get('steps') or {})}</section>")

    html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(titre)} — {escape(client)}</title>
<style>{_FEUILLE}</style>
</head>
<body>
<div class="doc">
  <header class="garde">
    <div class="garde-marque">
      <img src="{charte.logo_data_uri(logo)}" alt="" />
      <div><b>GREEN SHIELD</b><span>{escape(cabinet or _CABINET_DEFAUT)}</span></div>
    </div>
    <h1>{escape(titre)}</h1>
    <div class="garde-client">{escape(client)}</div>
    <div class="garde-mission">{escape(str(state.get("name") or ""))}</div>
    <dl class="garde-meta">
      {"".join(f"<div><dt>{escape(k)}</dt><dd>{escape(str(v))}</dd></div>" for k, v in meta)}
    </dl>
    <div class="garde-classe">Document confidentiel — diffusion restreinte</div>
  </header>

  <section class="sommaire-bloc">
    <h2 class="sans-num">Sommaire</h2>
    <ol class="sommaire">{sommaire}</ol>
  </section>

  {corps}

  <section class="chapitre"><h2><span class="num-chap">{len(CHAPITRES) + 1}</span>Certifications et signatures</h2>
    <p>L'auditeur certifie l'exactitude des constats factuels mentionnés dans le présent rapport.</p>
    <div class="tscroll"><table><thead><tr><th>Signature de l'auditeur</th><th>Signature du client audité</th></tr></thead>
    <tbody><tr><td><strong>{escape(auditeur or "—")}</strong><br />{escape(cabinet or _CABINET_DEFAUT)}</td>
    <td><strong>DSI / Responsable de la sécurité</strong><br />{escape(client)}</td></tr></tbody></table></div>
  </section>

  <footer class="pied">
    GREEN SHIELD — {escape(cabinet or _CABINET_DEFAUT)} · Document confidentiel, ne pas diffuser sans autorisation écrite.<br />
    Empreinte SHA-256 de l'état de la mission à l'édition : <code>{empreinte}</code>
    <em>Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.</em>
  </footer>
</div>
</body>
</html>"""
    return f"Rapport_{'GRC' if est_grc else 'Conseil'}_{p_id}.html", html


# --- M2, M3, M4, M5 — les quatre autres formats de restitution --------------
#
# Le rapport de mission (M1, ci-dessus) couvre l'intégralité de la mission.
# Ces quatre exports en restituent une vue ciblée : une page pour un COMEX
# (M2), un écran de clôture (M3), un registre opposable (M4), une
# cartographie du risque (M5). Aucun ne recopie de texte inventé : chaque
# phrase descriptive vient d'un champ saisi (la synthèse exécutive) ou d'un
# calcul sur les données réelles — jamais d'une prose générique.

def _entete_court(titre_page: str, sous_titre: str, meta: list[tuple[str, str]],
                  cabinet: str = "", logo: str = "") -> str:
    """En-tête compact pour un document papier court (M2, M4) : logo, titre
    et méta-données en une bande, sans la page de garde pleine hauteur de M1."""
    lignes_meta = "".join(f"<span>{escape(k)} : <strong>{escape(str(v))}</strong></span>"
                          for k, v in meta)
    return f"""
<header class="entete-court">
  <div class="entete-court-marque">
    <img src="{charte.logo_data_uri(logo)}" alt="" />
    <div><b>GREEN SHIELD</b><span>{escape(cabinet or _CABINET_DEFAUT)}</span></div>
  </div>
  <div class="entete-court-meta">{lignes_meta}</div>
</header>
<h1 class="titre-court">{escape(titre_page)}</h1>
<p class="sous-titre-court">{escape(sous_titre)}</p>
<div class="garde-classe garde-classe-inline">Document confidentiel — diffusion restreinte</div>
"""


def _pied_court(empreinte: str, cabinet: str = "") -> str:
    return f"""
<footer class="pied">
  GREEN SHIELD — {escape(cabinet or _CABINET_DEFAUT)} · Document confidentiel, ne pas diffuser sans autorisation écrite.<br />
  Empreinte SHA-256 de l'état de la mission à l'édition : <code>{empreinte}</code>
  <em>Toute modification ultérieure de la mission, même rétablie, produit une empreinte différente.</em>
</footer>
"""


def _document_court(titre_onglet: str, corps: str) -> str:
    """Coquille HTML commune à M2 et M4 : même feuille de style que M1
    (thème papier), sans la page de garde en pleine hauteur."""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(titre_onglet)}</title>
<style>{_FEUILLE}{_FEUILLE_COURT}</style>
</head>
<body>
<div class="doc doc-court">
{corps}
</div>
</body>
</html>"""


def _meta_commune(state: dict, p_id: str, auditeur: str, cabinet: str) -> list[tuple[str, str]]:
    est_grc = state.get("type") == "grc"
    cadrage = (state.get("steps") or {}).get("cadrage") or {}
    meta = [("Client", state.get("client") or "—"), ("Réf.", p_id)]
    referentiel = cadrage.get("framework_name") or cadrage.get("framework_id")
    if referentiel:
        meta.append(("Référentiel", referentiel))
    meta.append(("Méthode", "ISO 27001 / DORA" if est_grc else "EBIOS RM · ANSSI"))
    meta.append(("Édité le", datetime.now().strftime("%d/%m/%Y")))
    if auditeur:
        meta.append(("Auditeur", auditeur))
    return meta


# --- M2 — Synthèse direction -------------------------------------------------

def _jauge_svg(pourcentage: int, libelle: str) -> str:
    circonference = 2 * 3.14159265 * 50
    decalage = circonference * (1 - pourcentage / 100)
    return f"""<svg class="jauge" viewBox="0 0 120 120" role="img"
     aria-label="{libelle} : {pourcentage} %">
  <circle cx="60" cy="60" r="50" fill="none" stroke="#e4ece9" stroke-width="11" />
  <circle cx="60" cy="60" r="50" fill="none" stroke="#2ee6a0" stroke-width="11"
          stroke-linecap="round" stroke-dasharray="{circonference:.2f}"
          stroke-dashoffset="{decalage:.2f}" transform="rotate(-90 60 60)" />
  <text x="60" y="56" text-anchor="middle" font-size="27" font-weight="700"
        fill="#0c2317">{pourcentage} %</text>
  <text x="60" y="74" text-anchor="middle" font-size="8.5" fill="#6b7f78"
        letter-spacing="1">{escape(libelle.upper())}</text>
</svg>"""


def _stats_diagnostic(state: dict) -> list[tuple[str, str, str]]:
    """Ce qui a été instruit — des comptages réels, jamais une appréciation
    qualitative inventée."""
    steps = state.get("steps") or {}
    cadrage, ebios = steps.get("cadrage") or {}, steps.get("ebios") or {}
    est_grc = state.get("type") == "grc"
    tiers = ((steps.get("tprm") or {}).get("tiers")) or []
    lignes = []

    patrimoine = len(cadrage.get("assets_metier") or []) + len(cadrage.get("assets_support") or [])
    if patrimoine:
        lignes.append(("Éléments de patrimoine cartographiés", str(patrimoine),
                       f"{len(cadrage.get('assets_metier') or [])} valeur(s) métier, "
                       f"{len(cadrage.get('assets_support') or [])} bien(s) support"))

    if ebios.get("redoute_events"):
        graves = sum(1 for e in ebios["redoute_events"] if int(e.get("gravity") or 0) >= 4)
        lignes.append(("Événements redoutés", str(len(ebios["redoute_events"])),
                       f"dont {graves} de gravité maximale" if graves else "—"))

    if ebios.get("operational_scenarios"):
        lignes.append(("Scénarios opérationnels construits",
                       str(len(ebios["operational_scenarios"])), "—"))

    if tiers:
        if est_grc:
            conformes = sum(1 for t in tiers if tprm.conformite(t)["conforme"])
            lignes.append(("Prestataires évalués", str(len(tiers)),
                           f"{conformes} sans écart"))
        else:
            critiques = sum(1 for t in tiers if t.get("rating") == "Critique")
            lignes.append(("Tiers évalués", str(len(tiers)),
                           f"{critiques} coté(s) critique(s)" if critiques else "aucun critique"))

    controles = (steps.get("evaluation") or {}).get("manual_controls") or []
    if controles:
        non_conformes = sum(1 for c in controles if c.get("status") == "NON_CONFORME")
        lignes.append(("Exigences organisationnelles évaluées", str(len(controles)),
                       f"{non_conformes} écart(s)" if non_conformes else "aucun écart"))

    entretiens = (state.get("socle") or {}).get("entretiens") or []
    if entretiens:
        lignes.append(("Entretiens conduits", str(len(entretiens)), "—"))

    return lignes


def _ecarts_prioritaires(steps: dict, plafond: int = 3) -> list[tuple[str, str, str]]:
    """Les mesures les plus urgentes du plan de traitement, sans reformulation."""
    remediations = (steps.get("traitement") or {}).get("remediations") or []
    ordre = {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}
    triees = sorted(remediations, key=lambda r: ordre.get(r.get("priority"), 9))
    return [(r.get("id"), r.get("priority"), r.get("measure")) for r in triees[:plafond]]


def build_synthese(state: dict, p_id: str, auditeur: str = "", cabinet: str = "", logo: str = "") -> tuple[str, str]:
    """M2 — une page pour une direction : verdict, écarts prioritaires,
    ce qui a été diagnostiqué, ce qu'il reste à faire, charges."""
    est_grc = state.get("type") == "grc"
    steps = state.get("steps") or {}
    client = str(state.get("client") or "")
    progress = int(state.get("progress") or 0)
    empreinte = docx_export.data_fingerprint(state)

    synthese_html = _synthese(state)  # réutilise le texte saisi par le consultant
    ecarts = _ecarts_prioritaires(steps)
    ecarts_html = _table(("ID", "Priorité", "Mesure"), ecarts,
                         "Aucune mesure de traitement n'a été définie à ce stade.",
                         colonnes_sev=(1,))

    diagnostic_html = _table(("Objet", "Volume", "Constat"), _stats_diagnostic(state),
                             "Aucun élément n'a encore été instruit sur cette mission.")

    remediations = (steps.get("traitement") or {}).get("remediations") or []
    par_priorite: dict[str, int] = {}
    for r in remediations:
        par_priorite[r.get("priority", "?")] = par_priorite.get(r.get("priority", "?"), 0) + 1
    reste_html = _table(
        ("Priorité", "Mesures"),
        [(p, str(par_priorite[p])) for p in ("Critique", "Élevé", "Moyen", "Faible") if par_priorite.get(p)],
        "Le plan de traitement n'a pas encore été priorisé.", colonnes_num=(1,), colonnes_sev=(0,),
    )

    socle = state.get("socle") or {}
    entrees = ((socle.get("temps") or {}).get("entrees")) or []
    from . import report_builder  # noqa: PLC0415 — libellés de durée partagés
    total_min = sum(int(e.get("minutes") or 0) for e in entrees)
    budget = ((socle.get("qualification") or {}).get("budget")) or "—"
    couv = controles_techniques.etat(state)
    bandeau = [
        ("Charges consommées", report_builder._duree_lisible(total_min) if entrees else "—"),
        ("Budget vendu", budget),
        ("Entretiens conduits", str(len((socle.get("entretiens")) or []))),
        ("Rattachement aux référentiels", f"{couv['taux']} %"),
    ]
    bandeau_html = "".join(f'<div><span>{escape(k)}</span><b>{escape(str(v))}</b></div>'
                           for k, v in bandeau)

    corps = f"""
{_entete_court("Synthèse de fin de mission",
              f"{escape(client)} — {'audit de conformité' if est_grc else 'audit de sécurité et analyse de risque'}",
              _meta_commune(state, p_id, auditeur, cabinet), cabinet=cabinet, logo=logo)}
<div class="verdict">
  {_jauge_svg(progress, "Avancement")}
  <div>{synthese_html}</div>
</div>
<h2 class="sans-num">Écarts prioritaires</h2>
{ecarts_html}
<h2 class="sans-num">Ce qui a été diagnostiqué</h2>
{diagnostic_html}
<h2 class="sans-num">Ce qu'il reste à faire</h2>
{reste_html}
<div class="bandeau-charges">{bandeau_html}</div>
{_pied_court(empreinte, cabinet=cabinet)}
"""
    nom = f"Synthese_Direction_{'GRC' if est_grc else 'Conseil'}_{p_id}.html"
    return nom, _document_court(f"Synthèse — {client}", corps)


# --- M4 — Registre de conformité --------------------------------------------

def build_registre_conformite(state: dict, p_id: str, auditeur: str = "", cabinet: str = "", logo: str = "") -> tuple[str, str]:
    """M4 — écarts organisationnels avec preuve, registre des tiers, plan de
    remédiation. Volet GRC : c'est le livrable opposable au régulateur. Volet
    Consulting : les sections organisationnelles restent honnêtement vides,
    ce volet n'en produit pas — voir §14.1bis."""
    est_grc = state.get("type") == "grc"
    steps = state.get("steps") or {}
    client = str(state.get("client") or "")
    empreinte = docx_export.data_fingerprint(state)

    exigences_html = _evaluation(steps)
    ecosysteme_html = _ecosysteme(state)
    rattachement_html = _rattachement(state)
    steps_traitement = (steps.get("traitement") or {}).get("remediations") or []
    ordre = {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}
    triees = sorted(steps_traitement, key=lambda r: ordre.get(r.get("priority"), 9))
    plan_html = _table(("ID", "Priorité", "Mesure"),
                       [(r.get("id"), r.get("priority"), r.get("measure")) for r in triees],
                       "Aucune mesure de remédiation n'a été définie.", colonnes_sev=(1,))

    corps = f"""
{_entete_court("Registre de conformité et écarts constatés",
              f"{escape(client)} — {'ISO/IEC 27001 & DORA' if est_grc else 'analyse de risque, sans référentiel de conformité'}",
              _meta_commune(state, p_id, auditeur, cabinet), cabinet=cabinet, logo=logo)}
<h2 class="sans-num">1. Exigences organisationnelles</h2>
{exigences_html}
<h2 class="sans-num">2. Écosystème et registre des tiers</h2>
{ecosysteme_html}
<h2 class="sans-num">3. Rattachement aux référentiels de contrôles</h2>
{rattachement_html}
<h2 class="sans-num">4. Plan de remédiation</h2>
{plan_html}
{_pied_court(empreinte, cabinet=cabinet)}
"""
    nom = f"Registre_Conformite_{'GRC' if est_grc else 'Conseil'}_{p_id}.html"
    return nom, _document_court(f"Registre de conformité — {client}", corps)


# --- Coquille commune à M3 et M5 (écran, thème sombre) ----------------------

def _entete_ecran(titre: str, sous_titre: str, pastille: str, classe_pastille: str) -> str:
    return f"""
<div class="glass board-tete">
  <div>
    <h3>{escape(titre)}</h3>
    <div class="sous">{escape(sous_titre)}</div>
  </div>
  <span class="puce {classe_pastille}">{escape(pastille)}</span>
</div>
"""


def _document_ecran(titre_onglet: str, corps: str) -> str:
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(titre_onglet)}</title>
<style>{_FEUILLE_ECRAN}</style>
</head>
<body>
<div class="board">
{corps}
</div>
</body>
</html>"""


# --- M3 — Tableau de restitution ---------------------------------------------

def _puce_priorite(priorite) -> str:
    classe = {"Critique": "p-crit", "Élevé": "p-elev", "Moyen": "p-moy", "Faible": "p-faib"}.get(priorite, "p-faib")
    return f'<span class="puce {classe}">{escape(str(priorite or "—"))}</span>'


def build_tableau_restitution(state: dict, p_id: str) -> tuple[str, str]:
    """M3 — écran de clôture : ce qui a été diagnostiqué face à ce qui reste
    à faire, colonne contre colonne, plus le rattachement aux référentiels."""
    est_grc = state.get("type") == "grc"
    steps = state.get("steps") or {}
    client = str(state.get("client") or "")
    ebios = steps.get("ebios") or {}
    tiers = ((steps.get("tprm") or {}).get("tiers")) or []
    remediations = sorted((steps.get("traitement") or {}).get("remediations") or [],
                          key=lambda r: {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}
                          .get(r.get("priority"), 9))

    # Colonne « diagnostiqué » : événements redoutés + scénarios + (tiers
    # critiques ou écarts organisationnels selon le volet).
    diagnostique = []
    for e in ebios.get("redoute_events") or []:
        diagnostique.append((e.get("id"), e.get("event"), e.get("impact"), f"G {e.get('gravity')}/4", "p-crit"))
    for s in ebios.get("operational_scenarios") or []:
        diagnostique.append((s.get("id"), s.get("event"), s.get("mitigation"),
                             f"G{s.get('gravity')} V{s.get('likelihood')}", "p-elev"))
    if est_grc:
        for c in (steps.get("evaluation") or {}).get("manual_controls") or []:
            if c.get("status") == "NON_CONFORME":
                diagnostique.append((c.get("id"), c.get("title"), c.get("notes"), "Écart", "p-crit"))
    else:
        for t in tiers:
            if t.get("rating") in ("Critique", "Élevé"):
                diagnostique.append((t.get("name"), f"Ratio {t.get('score')}",
                                     f"D{t.get('dependence')}/P{t.get('penetration')}/"
                                     f"M{t.get('maturity')}/C{t.get('trust')}",
                                     t.get("rating"), "p-crit" if t.get("rating") == "Critique" else "p-elev"))

    lignes_diag = "".join(
        f'<div class="ligne"><span class="id">{_t(id_)}</span>'
        f'<span class="txt"><b>{_t(titre)}</b><small>{_t(sous)}</small></span>'
        f'<span class="puce {classe}">{_t(pastille)}</span></div>'
        for id_, titre, sous, pastille, classe in diagnostique
    ) or _vide("Rien n'a encore été diagnostiqué sur cette mission.")

    lignes_faire = "".join(
        f'<div class="ligne"><span class="id">{_t(r.get("id"))}</span>'
        f'<span class="txt"><b>{_t(r.get("measure"))}</b><small>{_t(r.get("axe"))}</small></span>'
        f'{_puce_priorite(r.get("priority"))}</div>'
        for r in remediations
    ) or _vide("Aucune mesure de traitement n'a été définie à ce stade.")

    couv = controles_techniques.etat(state)
    barre = "".join(f'<i style="width:{couv["taux"]}%;background:var(--vert)"></i>'
                    f'<i style="width:{100 - couv["taux"]}%;background:rgba(255,255,255,.06)"></i>')

    kpis = [("Événements redoutés", str(len(ebios.get("redoute_events") or []))),
            ("Scénarios construits", str(len(ebios.get("operational_scenarios") or []))),
            ("Tiers évalués" if not est_grc else "Prestataires évalués", str(len(tiers))),
            ("Mesures au plan", str(len(remediations)))]
    kpis_html = "".join(f'<div class="kpi"><span>{escape(k)}</span><b>{escape(v)}</b></div>'
                        for k, v in kpis)

    corps = f"""
{_entete_ecran(f"Restitution de fin de mission — {client}",
              "Volet GRC" if est_grc else "Volet Conseil — EBIOS RM",
              f"{state.get('progress', 0)} % du périmètre",
              "p-ok")}
<div class="glass kpis">{kpis_html}</div>
<div class="duo-col">
  <div class="glass"><div class="col-tete">◂ <b>Ce qui a été diagnostiqué</b></div>{lignes_diag}</div>
  <div class="glass"><div class="col-tete"><b>Ce qui reste à faire</b> ▸</div>{lignes_faire}</div>
</div>
<div class="glass">
  <div class="col-tete"><b>Rattachement aux référentiels de contrôles</b> · CIS v8 / NIST CSF 2.0</div>
  <div class="barre">{barre}</div>
  <div class="note">{couv['couvertes']} pratique(s) couverte(s) sur {couv['total']} — {couv['taux']} %.</div>
</div>
"""
    nom = f"Tableau_Restitution_{'GRC' if est_grc else 'Conseil'}_{p_id}.html"
    return nom, _document_ecran(f"Restitution — {client}", corps)


# --- M5 — Cartographie du risque ---------------------------------------------

def _matrice_gravite_vraisemblance(scenarios: list[dict]) -> str:
    """4 lignes (gravité 4→1) × 5 colonnes (vraisemblance 1→5), mêmes seuils
    de couleur que la matrice déjà affichée en Phase 4 de l'application
    (web/src/components/phases/PhaseEbios.tsx) — reproduite ici à l'identique
    plutôt que réinventée, pour que les deux vues concordent."""
    cases = ""
    for gravite in (4, 3, 2, 1):
        cases += f'<div class="axe-y">G{gravite}</div>'
        for vraisemblance in (1, 2, 3, 4, 5):
            correspondants = [s for s in scenarios
                              if int(s.get("gravity") or 0) == gravite
                              and int(s.get("likelihood") or 0) == vraisemblance]
            produit = gravite * vraisemblance
            fond = "rgba(255,111,145,.22)" if produit >= 12 else \
                   "rgba(255,207,107,.16)" if produit >= 6 else "rgba(46,230,160,.06)"
            jetons = "".join(f'<span class="jeton">{escape(str(s.get("id") or ""))}</span>'
                             for s in correspondants)
            cases += f'<div class="case" style="background:{fond}">{jetons}</div>'
    axes_x = '<div></div>' + "".join(f'<div class="axe-x">V{v}</div>' for v in (1, 2, 3, 4, 5))
    return (f'<div class="matrice-hote"><div class="axe-titre-y">Gravité →</div>'
            f'<div class="matrice">{cases}{axes_x}</div></div>'
            f'<div class="axe-titre-x">Vraisemblance →</div>')


def build_cartographie_risque(state: dict, p_id: str) -> tuple[str, str]:
    """M5 — la matrice gravité × vraisemblance des scénarios EBIOS, et le
    classement des tiers : par ratio ANSSI en Conseil, par conformité en
    GRC (§14.1bis — ce volet ne produit aucun score de risque)."""
    est_grc = state.get("type") == "grc"
    steps = state.get("steps") or {}
    client = str(state.get("client") or "")
    ebios = steps.get("ebios") or {}
    scenarios = ebios.get("operational_scenarios") or []
    tiers = ((steps.get("tprm") or {}).get("tiers")) or []

    matrice_html = (_matrice_gravite_vraisemblance(scenarios) if scenarios
                    else _vide("Aucun scénario opérationnel n'a été construit."))

    if est_grc:
        note_tiers = ('<p class="note">Ce volet ne produit aucun score de risque : ni DORA ni '
                      "NIS2 ne se réclament d'EBIOS RM. Classement par taux de conformité.</p>")
        classement = sorted(
            ({"nom": t.get("name"), "valeur": tprm.conformite(t)["taux"],
              "libelle": f"{tprm.conformite(t)['taux']} %"} for t in tiers),
            key=lambda x: x["valeur"], reverse=True,
        )
        maximum = 100
    else:
        note_tiers = '<p class="note">Criticité selon la formule ANSSI : (dépendance × pénétration) / (maturité × confiance).</p>'
        classement = sorted(
            ({"nom": t.get("name"), "valeur": t.get("score") or 0,
              "libelle": str(t.get("score"))} for t in tiers),
            key=lambda x: x["valeur"], reverse=True,
        )
        maximum = max((c["valeur"] for c in classement), default=1) or 1

    rangs_html = "".join(
        f'<div class="rang"><div class="nom"><b>{_t(c["nom"])}</b>'
        f'<div class="piste"><i style="width:{min(100, c["valeur"] / maximum * 100):.0f}%"></i></div></div>'
        f'<div class="val">{_t(c["libelle"])}</div></div>'
        for c in classement
    ) or _vide("Aucun tiers n'a été évalué.")

    redoutes = ebios.get("redoute_events") or []
    redoutes_html = "".join(
        f'<div class="ligne"><span class="id">{_t(e.get("id"))}</span>'
        f'<span class="txt"><b>{_t(e.get("event"))}</b><small>{_t(e.get("impact"))}</small></span>'
        f'<span class="puce {"p-crit" if int(e.get("gravity") or 0) >= 4 else "p-elev"}">'
        f'{_t(e.get("gravity"))}/4</span></div>'
        for e in redoutes
    ) or _vide("Aucun événement redouté n'a été caractérisé.")

    corps = f"""
{_entete_ecran(f"Cartographie du risque — {client}",
              f"{len(scenarios)} scénario(s) opérationnel(s) · {len(tiers)} tiers évalué(s)",
              "Volet GRC" if est_grc else "Volet Conseil", "p-info")}
<div class="carto">
  <div class="glass">
    <div class="col-tete"><b>Scénarios opérationnels</b> · gravité × vraisemblance</div>
    {matrice_html}
  </div>
  <div class="glass">
    <div class="col-tete"><b>{"Conformité des prestataires" if est_grc else "Écosystème de tiers"}</b></div>
    {note_tiers}
    <div class="rangs">{rangs_html}</div>
  </div>
</div>
<div class="glass">
  <div class="col-tete"><b>Événements redoutés</b></div>
  {redoutes_html}
</div>
"""
    nom = f"Cartographie_Risque_{'GRC' if est_grc else 'Conseil'}_{p_id}.html"
    return nom, _document_ecran(f"Cartographie du risque — {client}", corps)


# Feuille de style unique et embarquée : le projet doit rester utilisable
# hors-ligne, aucune ressource externe n'est donc chargée.
_FEUILLE = """
:root{
  --vert:#2ee6a0; --vert-clair:#7bf3c8; --sombre:#04150e;
  --encre:#0c2317; --corps:#33403b; --doux:#6b7f78; --trait:#dfe7e3; --teinte:#f2fbf7;
  --rose:#a3243c; --rose-f:#fdeaed; --ambre:#8a5b00; --ambre-f:#fdf3e0;
  --ciel:#1d5f88; --ciel-f:#e8f4fd; --ok:#12694a; --ok-f:#e6f8f0;
  --neutre:#62726d; --neutre-f:#eef2f1;
  --sans:"Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,Arial,sans-serif;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
  --mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box}
body{margin:0;background:#e8ecea;color:var(--corps);font-family:var(--sans);
     font-size:10.5pt;line-height:1.55;-webkit-font-smoothing:antialiased}
.doc{max-width:21cm;margin:0 auto;background:#fff;padding:0 2.2cm 2cm;
     box-shadow:0 0 40px -14px rgba(0,0,0,.3)}
@media (max-width:46rem){.doc{padding:0 1.1rem 1.5rem}}

h1,h2,h3{color:var(--encre);margin:0;text-wrap:balance}
h1{font-family:var(--serif);font-size:24pt;line-height:1.12;font-weight:600;color:#fff}
h2{font-size:13pt;margin:0 0 .5rem;padding-bottom:.3rem;font-weight:700;
   border-bottom:2px solid var(--vert);display:flex;align-items:baseline;gap:.6rem}
h2.sans-num{display:block}
h3{font-size:10.5pt;font-weight:700;margin:1.4rem 0 .1rem}
.num-chap{font-family:var(--mono);font-size:9pt;color:var(--vert);
          background:var(--sombre);border-radius:3px;padding:.1rem .42rem;flex-shrink:0}
p{margin:.45rem 0 0}
.note{font-size:9pt;color:var(--doux);margin-top:.45rem}
.vide{font-size:9.5pt;color:var(--doux);font-style:italic;
      background:var(--neutre-f);border-left:3px solid var(--trait);padding:.5rem .75rem;margin-top:.5rem}
.chapeau p{font-size:11pt;line-height:1.6}
.encadre{background:var(--teinte);border-left:3px solid var(--vert);
         padding:.55rem .8rem;font-size:9.5pt;color:var(--encre);margin-top:.5rem}
.alerte{background:var(--rose-f);border-left:3px solid var(--rose);color:var(--rose);
        font-weight:600;padding:.55rem .8rem;font-size:9.5pt;margin-top:.5rem}
.chapitre{margin-top:2rem}
ol.actions{margin:.5rem 0 0;padding-left:1.4rem;font-size:10pt}
ol.actions li{margin-bottom:.22rem}

/* Page de garde */
.garde{background:linear-gradient(160deg,var(--sombre) 0%,#08251a 55%,#0c3325 100%);
       color:#eaf4f0;margin:0 -2.2cm;padding:2.6cm 2.2cm 2.2cm;position:relative;overflow:hidden}
@media (max-width:46rem){.garde{margin:0 -1.1rem;padding:2rem 1.1rem}}
.garde::after{content:"";position:absolute;right:-70px;top:-70px;width:280px;height:280px;
              background:radial-gradient(circle,rgba(46,230,160,.2),transparent 68%)}
.garde-marque{display:flex;align-items:center;gap:.8rem;position:relative}
.garde-marque img{width:44px;height:44px}
.garde-marque b{letter-spacing:.2em;text-transform:uppercase;font-size:10pt;display:block}
.garde-marque span{font-size:8pt;color:var(--vert-clair);letter-spacing:.1em}
.garde h1{margin-top:1.8cm;position:relative}
.garde-client{color:var(--vert);font-size:13pt;font-weight:700;margin-top:.4rem;position:relative}
.garde-mission{color:#a8c6bc;font-size:10pt;margin-top:.15rem;position:relative}
.garde-meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(4.6cm,1fr));
            gap:.9rem 1.4rem;margin:1.8cm 0 0;position:relative}
.garde-meta dt{font-size:7.5pt;text-transform:uppercase;letter-spacing:.1em;color:#8fb3a8}
.garde-meta dd{margin:.1rem 0 0;font-size:9.5pt;color:#eaf4f0;font-weight:600;
               word-break:break-word}
.garde-classe{position:relative;margin-top:1.4cm;display:inline-block;
              border:1px solid rgba(46,230,160,.4);color:var(--vert-clair);font-family:var(--mono);
              font-size:8pt;letter-spacing:.12em;text-transform:uppercase;padding:.3rem .7rem;border-radius:3px}

/* Sommaire */
.sommaire-bloc{margin-top:1.6rem}
.sommaire{columns:2;column-gap:1.6cm;font-size:9.5pt;margin:.6rem 0 0;padding-left:1.2rem}
@media (max-width:40rem){.sommaire{columns:1}}
.sommaire li{margin-bottom:.24rem;break-inside:avoid}

/* Tableaux */
.tscroll{overflow-x:auto;margin-top:.5rem}
table{border-collapse:collapse;width:100%;font-size:9pt}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid var(--trait);vertical-align:top}
thead th{background:var(--teinte);color:var(--encre);font-size:8pt;text-transform:uppercase;
         letter-spacing:.05em;border-bottom:1px solid #c9dbd3}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono);
              white-space:nowrap}
tbody tr:last-child td{border-bottom:none}

/* Pastilles */
.sev{font-family:var(--mono);font-size:7.5pt;font-weight:700;padding:.1rem .4rem;
     border-radius:3px;white-space:nowrap;display:inline-block}
.sev-crit{background:var(--rose-f);color:var(--rose)}
.sev-elev{background:var(--ambre-f);color:var(--ambre)}
.sev-moy{background:var(--ciel-f);color:var(--ciel)}
.sev-faib{background:var(--neutre-f);color:var(--neutre)}
.sev-ok{background:var(--ok-f);color:var(--ok)}

.jauge-lin{height:7px;border-radius:999px;background:var(--neutre-f);overflow:hidden;margin-top:.6rem}
.jauge-lin i{display:block;height:100%;background:var(--vert);border-radius:999px}

.pied{margin-top:2.4rem;padding-top:.7rem;border-top:1px solid var(--trait);
      font-size:7.5pt;color:var(--doux);text-align:center}
.pied code{font-family:var(--mono);word-break:break-all}
.pied em{display:block;font-size:7pt;color:#97a5a0;margin-top:.15rem}

@page{size:A4;margin:1.4cm}
@media print{
  body{background:#fff}
  .doc{max-width:none;box-shadow:none;padding:0}
  .garde{margin:0;padding:2.2cm 1.6cm;break-after:page}
  .chapitre{break-inside:auto}
  h2,h3{break-after:avoid}
  tr,.vide,.encadre,.alerte{break-inside:avoid}
  a{text-decoration:none;color:inherit}
}
"""

# Complément de _FEUILLE pour les documents courts (M2, M4) : même thème
# papier, en-tête compact au lieu de la page de garde pleine hauteur de M1.
_FEUILLE_COURT = """
.doc-court{padding-top:1.6cm}
.entete-court{display:flex;justify-content:space-between;align-items:flex-start;
              gap:1.2rem;border-bottom:3px solid var(--vert);padding-bottom:.7rem;flex-wrap:wrap}
.entete-court-marque{display:flex;align-items:center;gap:.6rem}
.entete-court-marque img{width:32px;height:32px}
.entete-court-marque b{color:var(--sombre);font-size:9.5pt;letter-spacing:.14em;
                       text-transform:uppercase;display:block}
.entete-court-marque span{font-size:7.5pt;color:var(--doux);letter-spacing:.06em}
.entete-court-meta{display:flex;flex-direction:column;gap:.15rem;text-align:right;
                   font-size:8pt;color:var(--doux)}
.titre-court{font-size:17pt;margin-top:1.1rem}
.sous-titre-court{font-size:9.5pt;color:var(--doux);margin-top:.2rem}
.garde-classe-inline{background:var(--teinte);border:1px solid var(--vert);color:var(--encre);
                     margin-top:.7rem;display:inline-block}
.verdict{display:grid;grid-template-columns:minmax(0,9rem) minmax(0,1fr);gap:1.6rem;
         align-items:center;background:var(--teinte);border-radius:5px;
         padding:1.2rem 1.4rem;margin-top:1.1rem}
@media (max-width:42rem){.verdict{grid-template-columns:1fr}}
.jauge{width:100%;max-width:8.5rem}
.bandeau-charges{display:flex;flex-wrap:wrap;gap:.55rem 1.8rem;margin-top:1rem;
                 padding:.75rem 1rem;border:1px solid var(--trait);border-radius:4px;font-size:9pt}
.bandeau-charges span{color:var(--doux);font-size:7.5pt;text-transform:uppercase;
                      letter-spacing:.06em;display:block}
.bandeau-charges b{color:var(--encre);font-variant-numeric:tabular-nums}
@media print{.doc-court{padding-top:0}.entete-court{break-after:avoid}}
"""

# Thème écran (sombre, cartes vitrées) pour M3 et M5 — restitution projetée
# en réunion de clôture, pas un document imprimé. Palette identique à
# l'application (web/src/index.css).
_FEUILLE_ECRAN = """
:root{
  --bg:#070f14;--panel:rgba(255,255,255,.03);--stroke:rgba(255,255,255,.09);
  --ink:#eaf4f0;--soft:#8ea6a0;--faint:#5d746e;
  --vert:#2ee6a0;--rose:#ff6f91;--ambre:#ffcf6b;--ciel:#5cc8ff;
  --sans:"Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,Arial,sans-serif;
  --mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,"Liberation Mono",monospace;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
     font-size:10.5pt;line-height:1.55}
.board{max-width:64rem;margin:0 auto;padding:1.6rem 1.1rem 3rem;display:flex;
       flex-direction:column;gap:1.1rem}
.glass{background:var(--panel);border:1px solid var(--stroke);border-radius:16px;
       padding:1.1rem 1.25rem}
.board-tete{display:flex;flex-wrap:wrap;justify-content:space-between;gap:1rem;align-items:flex-start}
.board-tete h3{margin:0;font-size:1.1rem;font-family:var(--serif);font-weight:600}
.board-tete .sous{color:var(--soft);font-size:.85rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:.8rem}
.kpi span{font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:var(--faint);display:block}
.kpi b{font-size:1.65rem;font-weight:700;font-variant-numeric:tabular-nums;display:block}
.duo-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));gap:1.1rem}
.col-tete{display:flex;align-items:center;gap:.5rem;font-size:.64rem;text-transform:uppercase;
          letter-spacing:.11em;color:var(--faint);margin-bottom:.75rem}
.col-tete b{color:var(--ink);letter-spacing:.11em}
.ligne{display:flex;gap:.7rem;padding:.6rem 0;border-bottom:1px solid rgba(255,255,255,.05);
       font-size:.8rem;align-items:flex-start}
.ligne:last-child{border-bottom:none}
.ligne .id{font-family:var(--mono);font-size:.66rem;color:var(--faint);flex-shrink:0;
           width:3.8rem;padding-top:.12rem}
.ligne .txt{flex:1;min-width:0}
.ligne .txt b{display:block;color:var(--ink);font-weight:600}
.ligne .txt small{color:var(--soft);font-size:.72rem}
.puce{font-family:var(--mono);font-size:.6rem;font-weight:700;padding:.12rem .42rem;
      border-radius:999px;white-space:nowrap;flex-shrink:0}
.p-crit{background:rgba(255,111,145,.16);color:var(--rose)}
.p-elev{background:rgba(255,207,107,.16);color:var(--ambre)}
.p-moy{background:rgba(92,200,255,.16);color:var(--ciel)}
.p-faib{background:rgba(255,255,255,.08);color:var(--soft)}
.p-ok{background:rgba(46,230,160,.16);color:var(--vert)}
.p-info{background:rgba(92,200,255,.16);color:var(--ciel)}
.barre{height:7px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden;display:flex}
.note{font-size:.74rem;color:var(--soft);margin-top:.6rem}
.vide{font-size:.8rem;color:var(--faint);font-style:italic;padding:.6rem 0}
.carto{display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1.1rem}
.matrice-hote{display:grid;grid-template-columns:auto 1fr;gap:.4rem;align-items:center}
.axe-titre-y{writing-mode:vertical-rl;transform:rotate(180deg);font-size:.6rem;
             letter-spacing:.12em;text-transform:uppercase;color:var(--faint);
             justify-self:center;white-space:nowrap}
.axe-titre-x{font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
             color:var(--faint);text-align:center;margin-top:.25rem}
.matrice{display:grid;grid-template-columns:auto repeat(5,1fr);gap:3px;font-size:.62rem}
.matrice .axe-y,.matrice .axe-x{color:var(--faint);font-family:var(--mono);
                                display:flex;align-items:center;justify-content:center}
.matrice .case{aspect-ratio:1;border-radius:4px;display:flex;align-items:center;
               justify-content:center;gap:2px;flex-wrap:wrap;padding:2px;
               border:1px solid rgba(255,255,255,.05)}
.matrice .jeton{font-family:var(--mono);font-size:.56rem;font-weight:700;padding:.1rem .28rem;
                border-radius:3px;background:rgba(0,0,0,.35);color:#fff}
.rangs{display:flex;flex-direction:column;gap:.55rem}
.rang{display:grid;grid-template-columns:minmax(0,1fr) 3.4rem;gap:.7rem;align-items:center;font-size:.78rem}
.rang .nom b{display:block;color:var(--ink);font-weight:600;font-size:.78rem}
.rang .piste{height:6px;border-radius:999px;background:rgba(255,255,255,.07);
             margin-top:.3rem;overflow:hidden}
.rang .piste i{display:block;height:100%;border-radius:999px;background:var(--rose)}
.rang .val{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right;
           font-size:.82rem;font-weight:700}
@media print{@page{size:A4 landscape;margin:1cm}body{background:#fff}}
"""
