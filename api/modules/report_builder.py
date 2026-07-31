"""report_builder.py — génération des livrables Markdown d'une mission.

Extrait de `projects.py` le 29/07/2026 : la route HTTP mélangeait le routage,
la lecture du dossier de mission et près de 300 lignes de gabarits documentaires.
Ce module ne connaît ni HTTP ni système de fichiers — il prend l'état d'une
mission et rend un couple (titre de fichier, contenu Markdown), ce qui le rend
testable directement et prépare l'habillage graphique des livrables.
"""
from __future__ import annotations

from datetime import datetime

from . import aipd as aipd_module
from . import charte
from . import controles_techniques
from . import couverture
from . import docx_export
from . import soa as soa_module
from . import tprm

# Mêmes défauts neutres que `report_docx.py`/`report_html.py`/`charte.py` :
# l'application sert n'importe quel consultant, jamais un nom écrit en dur
# (retour utilisateur du 30/07/2026).
_AUDITEUR_DEFAUT = "Consultant"
_CABINET_DEFAUT = "Cabinet non renseigné"


class TypeDocumentInconnu(ValueError):
    """Type de livrable non pris en charge."""

    def __init__(self, doc_type: str):
        super().__init__(f"Type de document inconnu : {doc_type}")
        self.doc_type = doc_type


# Types de livrables proposés par l'interface.
TYPES_DOCUMENTS = ("nda", "ebios", "pssi_pri", "aipd", "soa", "audit_report")



PHASES_LIBELLES = {
    "cadrage": "Cadrage & Patrimoine",
    "diagnostic": "Diagnostic & RGPD",
    "tprm": "Risques Tiers (TPRM)",
    "ebios": "Analyse des Menaces (EBIOS RM)",
    "resilience": "Résilience & E3R",
    "traitement": "Traitement & Livrables",
    "autre": "Coordination, déplacements, rédaction",
}


def _duree_lisible(minutes: int) -> str:
    """Miroir de `formatDuree` côté frontend (web/src/lib/duree.ts)."""
    heures, reste = divmod(minutes, 60)
    if heures == 0:
        return f"{reste} min"
    if reste == 0:
        return f"{heures} h"
    return f"{heures} h {reste:02d}"


def _charges_consommees(state: dict) -> str:
    """Tableau « charges consommées vs budget vendu » pour le rapport d'audit.

    Indicateur exigé par la méthodologie Hermes dès le démarrage d'une mission.
    Il n'était visible que dans l'interface : le client ne le voyait jamais.
    """
    socle = state.get("socle") or {}
    entrees = ((socle.get("temps") or {}).get("entrees")) or []
    budget = ((socle.get("qualification") or {}).get("budget")) or ""

    if not entrees:
        return "_Aucun temps consommé n'a été saisi pour cette mission._"

    par_phase: dict[str, int] = {}
    for e in entrees:
        par_phase[e.get("phase", "autre")] = par_phase.get(e.get("phase", "autre"), 0) + int(e.get("minutes") or 0)

    total = sum(par_phase.values())
    lignes = ["| Phase | Temps consommé |", "| :--- | ---: |"]
    for phase, libelle in PHASES_LIBELLES.items():
        if par_phase.get(phase):
            lignes.append(f"| {libelle} | {_duree_lisible(par_phase[phase])} |")
    lignes.append(f"| **Total** | **{_duree_lisible(total)}** |")

    tableau = "\n".join(lignes)
    if budget:
        tableau += f"\n\n*   **Budget vendu :** {budget}"
    return tableau


def _cellule(valeur) -> str:
    """Neutralise ce qui casserait une cellule Markdown, sans rien inventer.

    Une barre verticale saisie par le consultant scinde la cellule et décale
    toute la ligne ; un retour à la ligne la coupe en deux.
    """
    if valeur is None:
        return "—"
    texte = str(valeur).strip().replace("|", "/").replace("\n", " ")
    return texte or "—"


def _tableau(entetes: tuple[str, ...], lignes: list[tuple], vide: str) -> str:
    """Tableau Markdown, ou une phrase explicite s'il n'y a rien à montrer.

    Un tableau à en-têtes sans aucune ligne est le pire des deux mondes : il
    promet un contenu au lecteur et n'en livre aucun (constaté en recette le
    29/07/2026 sur le rapport d'audit d'une mission Consulting).
    """
    if not lignes:
        return f"_{vide}_"
    sortie = "| " + " | ".join(entetes) + " |\n"
    sortie += "| " + " | ".join(":---" for _ in entetes) + " |\n"
    for ligne in lignes:
        sortie += "| " + " | ".join(_cellule(c) for c in ligne) + " |\n"
    return sortie


def _remediations_md(steps: dict) -> str:
    """Plan de traitement priorisé — le livrable central d'une mission.

    Il n'apparaissait dans aucun export Markdown avant le 29/07/2026 : la
    section « Plan d'Action » n'était qu'un titre suivi d'une phrase générique.
    """
    remediations = (steps.get("traitement") or {}).get("remediations") or []
    # Priorité décroissante : un plan d'action se lit par ce qui est urgent.
    ordre = {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}
    triees = sorted(remediations, key=lambda r: ordre.get(r.get("priority"), 9))
    return _tableau(
        ("ID", "Priorité", "Axe", "Mesure de traitement"),
        [(r.get("id"), r.get("priority"), r.get("axe"), r.get("measure")) for r in triees],
        "Aucune mesure de traitement n'a été définie à ce stade.",
    )


def _pilotage_remediations_md(steps: dict) -> str:
    """Sans responsable ni échéance, un plan de traitement dit quoi faire,
    jamais qui ni quand (chaîne risque -> traitement, chantier ③)."""
    remediations = (steps.get("traitement") or {}).get("remediations") or []
    ordre = {"Critique": 0, "Élevé": 1, "Moyen": 2, "Faible": 3}
    triees = sorted(remediations, key=lambda r: ordre.get(r.get("priority"), 9))
    return _tableau(
        ("ID", "Responsable", "Échéance", "Statut", "Coût estimé"),
        [(r.get("id"), r.get("responsable"), r.get("echeance"), r.get("statut"), r.get("cout_estime"))
         for r in triees],
        "Aucune mesure de traitement n'a été définie à ce stade.",
    )


def _quick_wins_md(steps: dict) -> str:
    wins = (steps.get("traitement") or {}).get("quick_wins") or []
    if not wins:
        return "_Aucune action immédiate n'a été retenue._"
    return "\n".join(f"{i}. {_cellule(w)}" for i, w in enumerate(wins, 1))


def _sources_risque_md(steps: dict) -> str:
    sources = (steps.get("ebios") or {}).get("risk_sources") or []
    return _tableau(
        ("ID", "Source de risque", "Objectif visé"),
        [(s.get("id"), s.get("name"), s.get("objective")) for s in sources],
        "Aucune source de risque n'a été caractérisée.",
    )


def _cas_reels_md(steps: dict) -> str:
    cas = (steps.get("ebios") or {}).get("case_studies") or []
    return _tableau(
        ("Cas réel", "Enseignement retenu pour ce client"),
        [(c.get("case"), c.get("lessons")) for c in cas],
        "Aucun cas comparable n'a été versé au dossier.",
    )


def _tprm_md(state: dict) -> str:
    """Écosystème de tiers, restitué selon le volet (§14.1bis).

    Consulting : classement par ratio ANSSI. GRC : avancement des exigences
    DORA/NIS2, sans score — ces référentiels n'en réclament pas.
    """
    tiers = ((state.get("steps") or {}).get("tprm") or {}).get("tiers") or []

    if state.get("type") == "grc":
        lignes = []
        for t in tiers:
            etat = tprm.conformite(t)
            manquantes = [e["libelle"] for e in (t.get("exigences") or []) if not e.get("satisfait")]
            lignes.append((
                t.get("name"),
                f"{etat['satisfaites']}/{etat['total']} ({etat['taux']} %)",
                # Typographie française : le point-virgule prend une espace avant.
                "Conforme" if etat["conforme"] else " ; ".join(manquantes) or "—",
            ))
        return _tableau(
            ("Prestataire", "Exigences satisfaites", "Écarts restants"), lignes,
            "Aucun prestataire n'a été inscrit au registre.",
        )

    classement = sorted(tiers, key=lambda t: t.get("score", 0), reverse=True)
    return _tableau(
        ("Tiers", "Criticité", "Ratio", "Dép. / Pén. / Mat. / Conf."),
        [(t.get("name"), t.get("rating"), t.get("score"),
          f"{t.get('dependence')} / {t.get('penetration')} / {t.get('maturity')} / {t.get('trust')}")
         for t in classement],
        "Aucun tiers n'a été évalué.",
    )


def _e3r_md(steps: dict) -> str:
    e3r = (steps.get("resilience") or {}).get("e3r") or {}
    etapes = (("Endiguement", "endiguement"), ("Éviction", "eviction"),
              ("Éradication", "eradication"), ("Reconstruction", "reconstruction"))
    return _tableau(
        ("Étape E3R", "Procédure retenue"),
        [(libelle, e3r.get(cle)) for libelle, cle in etapes if (e3r.get(cle) or "").strip()],
        "La séquence de remédiation E3R n'a pas été documentée.",
    )


def _strategie_remediation_md(steps: dict) -> str:
    """Volet stratégique de la remédiation ANSSI (§14.2.3) : la séquence E3R
    ci-dessus est technique/opérationnelle ; ceci documente l'arbitrage rendu
    par la Direction entre urgence de redémarrage et coûts/risques induits."""
    strategie = (steps.get("resilience") or {}).get("strategie_remediation") or {}
    criteres = (("Urgence de redémarrage", "urgence_redemarrage"),
                ("Coûts et risques d'un redémarrage précipité", "couts_risques_redemarrage"),
                ("Décision retenue et autorité", "decision_direction"))
    return _tableau(
        ("Critère d'arbitrage", "Position retenue"),
        [(libelle, strategie.get(cle)) for libelle, cle in criteres if (strategie.get(cle) or "").strip()],
        "Le volet stratégique (arbitrage Direction) n'a pas été documenté.",
    )


def _identite_md(name: str, client: str, fw_name: str | None, scope: str, now: str,
                 auditeur: str = "", cabinet: str = "") -> str:
    """Bloc d'identification du livrable, rendu en tableau.

    Une suite de lignes « **Champ :** valeur » exige deux espaces en fin de ligne
    pour produire un saut ; sans eux, Markdown les agglomère en un seul
    paragraphe illisible — c'est ce qui est arrivé au 30/07/2026. Un tableau
    n'a pas cette fragilité et s'aligne proprement partout, y compris sur les
    rendus Markdown qui ignorent les sauts de ligne implicites.
    """
    lignes = [("Projet", name), ("Client", client)]
    if fw_name:
        lignes.append(("Référentiel principal", fw_name))
    lignes += [("Périmètre de l'audit", scope), ("Date d'édition", now),
               ("Auditeur", f"{auditeur or _AUDITEUR_DEFAUT}, {cabinet or _CABINET_DEFAUT}")]
    return _tableau((" ", " "), [(f"**{cle}**", valeur) for cle, valeur in lignes],
                    "Identification du livrable indisponible.")


def _synthese_md(state: dict) -> str:
    """Synthèse pour la direction — le premier chapitre lu, jamais inventé."""
    resume = ((state.get("steps") or {}).get("restitution") or {}).get("exec_summary") or ""
    if resume.strip():
        return resume.strip()
    return ("_Synthèse non rédigée. Elle se saisit en phase 6 (Traitement & Livrables) "
            "et n'est jamais produite automatiquement : elle engage le jugement du consultant._")


def _valeurs_metier_md(steps: dict) -> str:
    actifs = (steps.get("cadrage") or {}).get("assets_metier") or []
    return _tableau(
        ("ID", "Valeur métier", "Description", "Données personnelles"),
        [(a.get("id"), a.get("name"), a.get("description"),
          "Oui" if a.get("is_personal_data") else "Non") for a in actifs],
        "Aucune valeur métier n'a été cartographiée.",
    )


def _biens_supports_md(steps: dict) -> str:
    actifs = (steps.get("cadrage") or {}).get("assets_support") or []
    return _tableau(
        ("ID", "Bien support", "Type", "Description", "Responsable"),
        [(a.get("id"), a.get("name"), a.get("type"), a.get("description"), a.get("owner"))
         for a in actifs],
        "Aucun bien support n'a été inventorié.",
    )


def _redoutes_md(steps: dict) -> str:
    evenements = (steps.get("ebios") or {}).get("redoute_events") or []
    return _tableau(
        ("ID", "Événement redouté", "Gravité", "Impacts"),
        [(e.get("id"), e.get("event"), f"{e.get('gravity')}/4", e.get("impact"))
         for e in evenements],
        "Aucun événement redouté n'a été caractérisé.",
    )


def _scenarios_md(steps: dict) -> str:
    scenarios = (steps.get("ebios") or {}).get("operational_scenarios") or []
    return _tableau(
        ("ID", "Scénario opérationnel", "Gravité", "Vraisemblance", "Mesure d'atténuation"),
        [(s.get("id"), s.get("event"), f"{s.get('gravity')}/4", f"{s.get('likelihood')}/5",
          s.get("mitigation")) for s in scenarios],
        "Aucun scénario opérationnel n'a été construit.",
    )


def _traitement_risques_md(steps: dict) -> str:
    """Propriétaire, résiduel et décision — sans quoi un scénario est une
    observation, pas un risque géré (chantier ②)."""
    scenarios = (steps.get("ebios") or {}).get("operational_scenarios") or []
    return _tableau(
        ("ID", "Propriétaire", "Résiduel (G/V)", "Stratégie", "Statut"),
        [(s.get("id"), s.get("owner"),
          f"{s.get('gravite_residuelle')}/{s.get('vraisemblance_residuelle')}"
          if s.get("gravite_residuelle") is not None and s.get("vraisemblance_residuelle") is not None else None,
          s.get("strategie_traitement"), s.get("statut"))
         for s in scenarios],
        "Aucun scénario opérationnel n'a été construit.",
    )


def _cadrage_mission_md(state: dict) -> str:
    """Cadrage contractuel — rend le périmètre opposable.

    Ce qui n'a pas été saisi n'apparaît pas : mieux vaut un cadrage court qu'un
    cadrage rempli de valeurs de repli.
    """
    socle = state.get("socle") or {}
    qualif = socle.get("qualification") or {}
    contrat = socle.get("contractualisation") or {}
    kickoff = socle.get("kickoff") or {}

    champs = (
        ("Déclencheur de la mission", qualif.get("declencheur")),
        ("Sponsor exécutif", qualif.get("sponsor_executif")),
        ("Budget vendu", qualif.get("budget")),
        ("Maturité constatée à l'entrée", qualif.get("maturite_actuelle")),
        ("Échéance cible", qualif.get("echeance_cible")),
        ("Périmètre inclus", contrat.get("perimetre_inclus")),
        ("Périmètre explicitement exclu", contrat.get("perimetre_exclu")),
        ("Modalités d'intervention", contrat.get("modalites")),
        ("Accès au SI consentis", contrat.get("acces_si")),
        ("Date de réunion de lancement", kickoff.get("date")),
        ("Gouvernance de la mission", kickoff.get("gouvernance")),
    )
    lignes = [(libelle, valeur) for libelle, valeur in champs if str(valeur or "").strip()]

    livrables = contrat.get("livrables") or []
    participants = kickoff.get("participants") or []
    if livrables:
        lignes.append(("Livrables contractuels", " · ".join(str(l) for l in livrables)))
    if participants:
        lignes.append(("Participants au lancement", " · ".join(str(p) for p in participants)))

    return _tableau(("Élément de cadrage", "Contenu"), lignes,
                    "Le cadrage contractuel de la mission n'a pas été renseigné.")


def _entretiens_md(state: dict) -> str:
    """Entretiens conduits — ce qui rend chaque constat attribuable (ISO 19011).

    Volontairement par **rôle** et non par nom : le champ nominatif n'est pas
    collecté, et la politique de conservation (F17) purge ces déclarations en fin
    de mission. Un rapport déjà exporté échappe à cette purge — c'est pourquoi
    l'interface invite à saisir une fonction plutôt qu'une identité.
    """
    entretiens = (state.get("socle") or {}).get("entretiens") or []
    return _tableau(
        ("Rôle rencontré", "Date", "Ce qui a été déclaré"),
        [(e.get("role"), e.get("date"), e.get("synthese")) for e in entretiens],
        "Aucun entretien n'a été consigné : les constats de ce rapport ne sont "
        "pas rattachés à une source déclarative identifiée.",
    )


def _continuite_md(steps: dict) -> str:
    bcp = (steps.get("resilience") or {}).get("bcp_strategy") or {}
    champs = (("RTO — durée maximale d'interruption admissible", bcp.get("rto")),
              ("RPO — perte de données maximale admissible", bcp.get("rpo")),
              ("Politique de sauvegarde", bcp.get("backup_policy")))
    return _tableau(
        ("Cible de continuité", "Valeur retenue"),
        [(libelle, valeur) for libelle, valeur in champs if str(valeur or "").strip()],
        "Aucune cible de continuité n'a été définie.",
    )


def _reserve_md(state: dict, date_emission: str) -> str:
    """Réserve nominative et datée — c'est elle qui borne la responsabilité.

    Réutilise la formulation du rapport Word pour qu'un même client ne reçoive
    pas deux délimitations de responsabilité différentes selon le format.
    """
    return docx_export.mention_reserve(date_emission, str(state.get("client") or ""))


_ETAT_OBLIGATION = {True: "Fait", False: "**Reste à faire**"}


def _obligations_aipd_md(aipd: dict) -> str:
    """Tableau des obligations de procédure de l'AIPD (§14.2.1).

    Rendu tel quel, y compris les manques : le livrable doit montrer ce qui
    reste dû, pas laisser croire la démarche achevée.
    """
    saisies = {o.get("id"): o for o in (aipd.get("obligations") or [])}
    etat = aipd_module.etat(aipd)

    lignes = "| Obligation | Référence | État | Commentaire |\n| :--- | :--- | :--- | :--- |\n"
    for obligation in aipd_module.OBLIGATIONS:
        if obligation["conditionnelle"] and not etat["art36_requise"]:
            lignes += (f"| {obligation['libelle']} | {obligation['reference']} "
                       f"| Non applicable (risque résiduel non élevé) | |\n")
            continue
        saisie = saisies.get(obligation["id"], {})
        commentaire = (saisie.get("commentaire") or "").replace("\n", " ").replace("|", "/")
        lignes += (f"| {obligation['libelle']} | {obligation['reference']} "
                   f"| {_ETAT_OBLIGATION[bool(saisie.get('satisfait'))]} | {commentaire} |\n")

    alerte = aipd_module.alerte_bloquante(aipd)
    if alerte:
        lignes += f"\n> ⚠️ **{alerte}**\n"
    return lignes


def _protection_donnees_md(steps: dict) -> str:
    """Chapitre RGPD du rapport de mission (registre + violations + AIPD).

    Absent du rapport Markdown jusqu'ici — seuls les rendus Word (`_ch_aipd`)
    et HTML (`_aipd_section`) le portaient, décalant leur numérotation de
    chapitres d'un cran par rapport au Markdown. Reproduit ici le même
    contenu et la même numérotation (4.1/4.1bis/4.2/4.3) pour que les trois
    formats restent alignés.
    """
    diagnostic = steps.get("diagnostic") or {}
    rgpd_reg = diagnostic.get("rgpd_register") or []
    registre_md = "| ID | Traitement | Finalité | Catégories de données | Conservation |\n| :--- | :--- | :--- | :--- | :--- |\n"
    for r in rgpd_reg:
        registre_md += f"| {r.get('id')} | {r.get('name')} | {r.get('purpose')} | {r.get('data_categories')} | {r.get('retention')} |\n"
    if not rgpd_reg:
        registre_md = "_Aucun traitement n'a été inscrit au registre._\n"

    violations = diagnostic.get("violations") or []
    violations_md = "| ID | Constatée le | Nature | CNIL | Personnes informées |\n| :--- | :--- | :--- | :--- | :--- |\n"
    for v in violations:
        cnil = f"Notifiée le {v.get('date_notification_cnil')}" if v.get("notifiee_cnil") else "Non notifiée"
        informees = "Oui" if v.get("personnes_informees") else "Non"
        violations_md += f"| {v.get('id')} | {v.get('date_constat')} | {v.get('nature')} | {cnil} | {informees} |\n"
    if not violations:
        violations_md = "_Aucune violation de données n'a été constatée sur cette mission._\n"

    contenu = (f"### 4.1 Registre des traitements (RGPD Art. 30)\n{registre_md}\n"
               f"### 4.1bis Registre des violations de données (RGPD Art. 33-34)\n{violations_md}\n")

    if not diagnostic.get("aipd_required"):
        return contenu + "\n_Aucune analyse d'impact n'est requise sur ce périmètre._\n"

    aipd = diagnostic.get("aipd") or {}
    volets_md = ("| Volet d'analyse | Contenu |\n| :--- | :--- |\n"
                 f"| Description systématique du traitement | {aipd.get('treatment_description') or 'N/A'} |\n"
                 f"| Nécessité et proportionnalité | {aipd.get('necessity_eval') or 'N/A'} |\n"
                 f"| Risques pour les droits et libertés | {aipd.get('risks_eval') or 'N/A'} |\n"
                 f"| Mesures d'atténuation | {aipd.get('mitigation_measures') or 'N/A'} |\n")

    return (contenu + f"\n### 4.2 Analyse d'impact — les quatre volets\n{volets_md}\n"
            f"\n### 4.3 Obligations organisationnelles\n{_obligations_aipd_md(aipd)}")


def _controles_techniques_md(state: dict) -> str:
    """Rattachement des pratiques relevées aux contrôles CIS / NIST (§14.2.4).

    Restitue l'état tel qu'il est saisi dans les phases, sans le rejuger : ce
    tableau dit à quelle exigence chaque case cochée répond, et cite la phase
    d'où vient l'information pour qu'elle reste vérifiable.
    """
    resultat = controles_techniques.etat(state)

    lignes = "| Pratique | Contrôles rattachés | État | Constaté en |\n| :--- | :--- | :--- | :--- |\n"
    for pratique in resultat["pratiques"]:
        refs = ", ".join(f"{m['referentiel']} {m['ref']}" for m in pratique["mappings"])
        etat = "Couverte" if pratique["couverte"] else "**Non couverte**"
        lignes += (f"| {pratique['libelle']} | {refs} | {etat} — {pratique['justification']} "
                   f"| Phase {pratique['phase']} ({pratique['phase_libelle']}) |\n")

    return (f"{lignes}\n{resultat['couvertes']} pratique(s) couverte(s) sur "
            f"{resultat['total']} ({resultat['taux']} %).\n")


def build_document(state: dict, p_id: str, doc_type: str,
                   auditeur: str = "", cabinet: str = "") -> tuple[str, str]:
    """Rend (nom de fichier, contenu Markdown) pour un livrable de mission."""
    client = state.get("client", "Client")
    name = state.get("name", "Projet")
    steps = state.get("steps", {})
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    title = ""
    markdown_content = ""
    
    empreinte = docx_export.data_fingerprint(state)


    if doc_type == "nda":
        title = f"Accord_Confidentialite_{p_id}.md"
        nda_text = steps.get("cadrage", {}).get("nda_text") or "NDA non rédigé."
        markdown_content = f"""{charte.entete_markdown("ACCORD DE CONFIDENTIALITÉ", client, now, p_id, cabinet=cabinet)}
# ACCORD DE CONFIDENTIALITÉ & PROTECTION DES DONNÉES (NDA)

**Projet :** {name}  
**Client :** {client}  
**Date d'édition :** {now}  
**Classification :** **CONFIDENTIEL AFFAIRES**  

---

{nda_text}

---

### SIGNATURES

En foi de quoi, les parties s'engagent et signent électroniquement ou de manière manuscrite :

| Pour {cabinet or _CABINET_DEFAUT} | Pour {client} |
| :--- | :--- |
| **{auditeur or _AUDITEUR_DEFAUT}, Consultant Cyber** | **Mandataire habilité** |
| Signature cryptographique locale : `SHA256:{docx_export.data_fingerprint(state)}` | Signature : |
| Date : {now} | Date : |
"""
    elif doc_type == "ebios":
        title = f"Analyse_Risques_EBIOS_{p_id}.md"
        redoutes = steps.get("ebios", {}).get("redoute_events", [])
        scenarios = steps.get("ebios", {}).get("operational_scenarios", [])
        assets_metier = steps.get("cadrage", {}).get("assets_metier", [])
        assets_support = steps.get("cadrage", {}).get("assets_support", [])
        
        metier_md = "| ID | Valeur Métier | Description | Données Perso (RGPD) |\n| :--- | :--- | :--- | :--- |\n"
        for m in assets_metier:
            rgpd_status = "OUI (Registre actif)" if m.get("is_personal_data") else "Non"
            metier_md += f"| {m.get('id')} | {m.get('name')} | {m.get('description')} | {rgpd_status} |\n"
            
        support_md = "| ID | Bien Support | Type | Description | Responsable |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for s in assets_support:
            support_md += f"| {s.get('id')} | {s.get('name')} | {s.get('type')} | {s.get('description')} | {s.get('owner')} |\n"
            
        redoutes_md = "| ID | Événement Redouté | Gravité | Impacts (Financier, Juridique, Image) |\n| :--- | :--- | :--- | :--- |\n"
        for r in redoutes:
            redoutes_md += f"| {r.get('id')} | {r.get('event')} | {r.get('gravity')}/4 | {r.get('impact')} |\n"
            
        scenarios_md = "| ID | Scénario Opérationnel (Connaître -> Intrusion -> Pivot -> Exploiter) | Gravité | Vraisemblance | Mesure d'Atténuation |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for s in scenarios:
            scenarios_md += f"| {s.get('id')} | {s.get('event')} | {s.get('gravity')}/4 | {s.get('likelihood')}/5 | {s.get('mitigation')} |\n"
            
        markdown_content = f"""{charte.entete_markdown("ANALYSE DE RISQUES EBIOS RM", client, now, p_id, cabinet=cabinet)}
# RAPPORT D'ANALYSE DE RISQUES CYBER (ORIENTATION EBIOS RM)

**Projet :** {name}  
**Client :** {client}  
**Date d'édition :** {now}  
**Consultant :** {auditeur or _AUDITEUR_DEFAUT}, {cabinet or _CABINET_DEFAUT}  
**Classification :** CONFIDENTIEL  

---

## 1. Cadrage et Identification du Patrimoine (Périmètre)
Ce chapitre identifie le périmètre d'évaluation, les missions fondamentales de l'entreprise et cartographie le patrimoine d'actifs.

### 1.1 Valeurs Métier (Patrimoine à forte valeur ajoutée)
{metier_md}

### 1.2 Biens Supports (Actifs de l'infrastructure)
{support_md}

---

## 2. Cartographie des Menaces & Scénarios EBIOS RM

### 2.1 Événements Redoutés
{redoutes_md}

### 2.2 Sources de Risque et Objectifs Visés
{_sources_risque_md(steps)}

### 2.3 Scénarios Opérationnels d'Attaque (Analyse Factuelle)
{scenarios_md}

### 2.3bis Traitement des risques (propriétaire, résiduel, décision)
{_traitement_risques_md(steps)}

### 2.4 Cas Réels Versés au Dossier
{_cas_reels_md(steps)}

---

## 3. Écosystème et Risques Tiers
{_tprm_md(state)}

---

## 4. Plan d'Action & Traitement
Chaque mesure ci-dessous répond à un scénario ou à un écart constaté au chapitre 2.

### 4.1 Mesures de Traitement Priorisées
{_remediations_md(steps)}

### 4.1bis Pilotage (responsable, échéance, statut)
{_pilotage_remediations_md(steps)}

### 4.2 Actions Immédiates
{_quick_wins_md(steps)}
"""
    elif doc_type == "pssi_pri":
        title = f"PSSI_PRI_{p_id}.md"
        pssi_sects = steps.get("pssi_pri", {}).get("pssi_sections", [])
        sections_md = ""
        for s in pssi_sects:
            sections_md += f"### {s.get('title')}\n\n{s.get('content')}\n\n"
            
        rto = steps.get("resilience", {}).get("bcp_strategy", {}).get("rto", "N/A")
        rpo = steps.get("resilience", {}).get("bcp_strategy", {}).get("rpo", "N/A")
        bcp = steps.get("resilience", {}).get("bcp_strategy", {}).get("backup_policy", "N/A")
        e3r = steps.get("resilience", {}).get("e3r", {})
        strategie = steps.get("resilience", {}).get("strategie_remediation", {})

        markdown_content = f"""{charte.entete_markdown("PSSI & PLAN DE REPRISE", client, now, p_id, cabinet=cabinet)}
# POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI) & PLAN DE REPRISE (PRI)

**Client :** {client}  
**Projet :** {name}  
**Date :** {now}  
**Auteur :** {auditeur or _AUDITEUR_DEFAUT}, {cabinet or _CABINET_DEFAUT}  

---

## I. POLITIQUE DE SÉCURITÉ DE L'INFORMATION (PSSI)

{sections_md}

---

## II. PLAN DE REPRISE INFORMATIQUE & RÉSILIENCE (PRI)

### 2.1 Indicateurs Temporels de Continuité
*   **RTO (Recovery Time Objective / Temps de reprise max) :** `{rto}`
*   **RPO (Recovery Point Objective / Perte de données max) :** `{rpo}`

### 2.2 Politique de Sauvegarde et d'Immuabilité
{bcp}

### 2.3 Séquence de Remédiation en Gestion de Crise (E3R de l'ANSSI)
En cas de compromission majeure de l'Active Directory ou de l'infrastructure Cloud :

1.  **Endiguement (Contenir l'attaquant) :**  
    {e3r.get('endiguement', 'N/A')}
2.  **Éviction (Reprendre le contrôle du cœur de confiance) :**  
    {e3r.get('eviction', 'N/A')}
3.  **Éradication (Nettoyage en profondeur des emprises) :**  
    {e3r.get('eradication', 'N/A')}
4.  **Reconstruction (Rebâtir de façon durcie dès la conception) :**
    {e3r.get('reconstruction', 'N/A')}

### 2.4 Volet Stratégique — Arbitrage Direction
*   **Urgence de redémarrage :** {strategie.get('urgence_redemarrage', 'N/A')}
*   **Coûts et risques d'un redémarrage précipité :** {strategie.get('couts_risques_redemarrage', 'N/A')}
*   **Décision retenue et autorité :** {strategie.get('decision_direction', 'N/A')}

---

### SIGNATURES POUR HOMOLOGATION DE SÉCURITÉ

| Pour {cabinet or _CABINET_DEFAUT} | Pour la Direction de {client} |
| :--- | :--- |
| **{auditeur or _AUDITEUR_DEFAUT}** | **Directeur Général / RSSI** |
| Signature : | Signature : |
"""
    elif doc_type == "aipd":
        title = f"AIPD_RGPD_{p_id}.md"
        diagnostic = steps.get("diagnostic", {})
        rgpd_reg = diagnostic.get("rgpd_register", [])
        aipd = diagnostic.get("aipd", {})
        
        register_md = "| ID | Activité de Traitement | Finalité | Catégories de Données | Durée de conservation |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for r in rgpd_reg:
            register_md += f"| {r.get('id')} | {r.get('name')} | {r.get('purpose')} | {r.get('data_categories')} | {r.get('retention')} |\n"

        violations = diagnostic.get("violations", [])
        violations_md = "| ID | Constatée le | Nature | CNIL | Personnes informées |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for v in violations:
            cnil = f"Notifiée le {v.get('date_notification_cnil')}" if v.get("notifiee_cnil") else "Non notifiée"
            informees = "Oui" if v.get("personnes_informees") else "Non"
            violations_md += f"| {v.get('id')} | {v.get('date_constat')} | {v.get('nature')} | {cnil} | {informees} |\n"
        if not violations:
            violations_md = "_Aucune violation de données n'a été constatée sur cette mission._\n"

        markdown_content = f"""{charte.entete_markdown("AIPD / PIA (RGPD)", client, now, p_id, cabinet=cabinet)}
# ANALYSE D'IMPACT RELATIVE À LA PROTECTION DES DONNÉES (AIPD / PIA)

**Client :** {client}  
**Projet :** {name}  
**Date :** {now}  
**Délégué à la Protection des Données (DPO) :** Enregistré au registre  

---

## 1. Registre des Activités de Traitement (Inventaire)
{register_md}

### 1.bis Registre des Violations de Données (RGPD Art. 33-34)
{violations_md}

---

## 2. Analyse d'Impact Systématique (PIA)

### 2.1 Description Systématique du Traitement
{aipd.get('treatment_description', 'N/A')}

### 2.2 Évaluation de la Nécessité et de la Proportionnalité
{aipd.get('necessity_eval', 'N/A')}

### 2.3 Évaluation des Risques sur les Droits et Libertés des Personnes
{aipd.get('risks_eval', 'N/A')}

### 2.4 Mesures de Traitement & de Sécurité envisagées (Atténuation)
{aipd.get('mitigation_measures', 'N/A')}

---

## 3. Obligations Organisationnelles (Conduite de l'AIPD)
{_obligations_aipd_md(aipd)}

---

### SIGNATURE DE VALIDATION CONFORMITÉ CNIL

| Avis du Délégué à la Protection des Données (DPO) | Validation du Responsable du Traitement |
| :--- | :--- |
| **Avis Favorable / Non Favorable** | **Validé pour mise en œuvre** |
| Signature : | Signature : |
"""
    elif doc_type == "soa":
        title = f"Declaration_Applicabilite_SoA_{p_id}.md"
        donnees = steps.get("evaluation", {}).get("soa", [])
        resume = soa_module.etat(donnees)

        def _tableau_theme(theme: str) -> str:
            entrees = [e for e in donnees if e.get("theme") == theme]
            return _tableau(
                ("Code", "Contrôle", "Applicabilité", "Statut", "Justification"),
                [(e.get("code"), e.get("titre"),
                  "Applicable" if e.get("applicable") is True else "Exclu" if e.get("applicable") is False else "Non statué",
                  e.get("statut") or "—", e.get("justification")) for e in entrees],
                f"Aucun contrôle du thème {theme}.",
            )

        markdown_content = f"""{charte.entete_markdown("DÉCLARATION D'APPLICABILITÉ (SoA)", client, now, p_id, cabinet=cabinet)}
# DÉCLARATION D'APPLICABILITÉ (SoA) — ISO/IEC 27001:2022 ANNEXE A

**Client :** {client}  
**Projet :** {name}  
**Date d'édition :** {now}  
**Auteur :** {auditeur or _AUDITEUR_DEFAUT}, {cabinet or _CABINET_DEFAUT}  

**{resume['statues']}/{resume['total']} contrôle(s) statué(s) ({resume['taux']} %)** — {resume['applicables']} applicable(s), {resume['exclus']} exclu(s).

---

## 1. Organisationnel
{_tableau_theme("Organisationnel")}

---

## 2. Personnel
{_tableau_theme("Personnel")}

---

## 3. Physique
{_tableau_theme("Physique")}

---

## 4. Technologique
{_tableau_theme("Technologique")}
"""
    elif doc_type == "audit_report":
        est_grc = state.get("type") == "grc"
        title = f"Rapport_Audit_{'GRC' if est_grc else 'Conseil'}_{p_id}.md"
        cadrage = steps.get("cadrage", {})
        scope = cadrage.get("scope") or "_Périmètre non défini._"

        # Ligne omise plutôt que remplie d'un « Standard GRC » qui n'existe
        # nulle part : une mission Conseil ne se réclame d'aucun référentiel, et
        # l'affirmer était une invention (constat de recette du 29/07/2026).
        fw_name = cadrage.get("framework_name")

        controls = steps.get("evaluation", {}).get("manual_controls", [])
        manual_md = _tableau(
            ("ID", "Exigence Organisationnelle", "Statut de Conformité", "Notes du Consultant"),
            [(c.get("id"), c.get("title"),
              # STATUS_LABELS existait déjà mais n'était branché que sur le DOCX :
              # le Markdown affichait « NON_CONFORME » brut au client.
              docx_export.STATUS_LABELS.get(c.get("status"), c.get("status")),
              c.get("notes")) for c in controls],
            "Aucune check-list de conformité n'est rattachée à cette mission : "
            "l'évaluation organisationnelle relève ici de l'analyse de risque du chapitre 2.",
        )

        tech_results = steps.get("evaluation", {}).get("technical_results", {})
        tech_md = ""
        if tech_results:
            tech_md = f"### Résultats Scan Technique (AuditCraft-GRC)\n\n*   **Score technique :** {tech_results.get('score')}% ({tech_results.get('band')})\n*   **Failles critiques :** {tech_results.get('critical_count')}\n\n{tech_results.get('report_markdown', '_Pas de rapport généré_')}"
        else:
            tech_md = "_Aucun scan technique d'audit de configuration n'a été exécuté pour ce projet._"

        soa_donnees = steps.get("evaluation", {}).get("soa", [])
        soa_md = ""
        if soa_donnees:
            soa_md = ("\n### Déclaration d'Applicabilité (SoA) — synthèse par thème\n"
                      "_Détail des 93 contrôles de l'Annexe A dans le livrable dédié "
                      "« Déclaration d'Applicabilité »._\n\n" +
                      _tableau(("Thème", "Total", "Applicables", "Exclus", "Non statués"),
                               [(t["theme"], t["total"], t["applicables"], t["exclus"], t["non_statues"])
                                for t in soa_module.par_theme(soa_donnees)], ""))

        charges_md = _charges_consommees(state)
        couverture_md = couverture.phrase(couverture.couverture_technique(state))
        titre = ("RAPPORT D'AUDIT DE CONFORMITÉ & GRC" if est_grc
                 else "RAPPORT D'AUDIT DE SÉCURITÉ & D'ANALYSE DE RISQUE")

        markdown_content = f"""{charte.entete_markdown(titre, client, now, p_id, cabinet=cabinet)}
# {titre}

{_identite_md(name, client, fw_name, scope, now, auditeur=auditeur, cabinet=cabinet)}

---

## 1. Synthèse à destination de la direction
{_synthese_md(state)}

---

## 2. Cadrage de la mission
{_cadrage_mission_md(state)}

### 2.1 Entretiens conduits
{_entretiens_md(state)}

---

## 3. Patrimoine évalué
### 3.1 Valeurs métier
{_valeurs_metier_md(steps)}

### 3.2 Biens supports
{_biens_supports_md(steps)}

---

## 4. Protection des données personnelles
{_protection_donnees_md(steps)}

---

## 5. Analyse de risque
### 5.1 Événements redoutés
{_redoutes_md(steps)}

### 5.2 Scénarios opérationnels
{_scenarios_md(steps)}

### 5.2bis Traitement des risques (propriétaire, résiduel, décision)
{_traitement_risques_md(steps)}

---

## 6. Écosystème et risques tiers
{_tprm_md(state)}

---

## 7. Résilience et continuité
{_continuite_md(steps)}

### 7.1 Séquence de remédiation E3R
{_e3r_md(steps)}

### 7.2 Volet stratégique — arbitrage Direction
{_strategie_remediation_md(steps)}

---

## 8. Évaluation organisationnelle
{manual_md}
{soa_md}
---

## 9. Évaluation technique des configurations

> **Couverture technique de cet audit.** {couverture_md}

{tech_md}

---

## 10. Rattachement aux référentiels de contrôles (CIS v8 / NIST CSF 2.0)
{_controles_techniques_md(state)}

---

## 11. Plan de traitement
### 11.1 Mesures priorisées
{_remediations_md(steps)}

### 11.1bis Pilotage (responsable, échéance, statut)
{_pilotage_remediations_md(steps)}

### 11.2 Actions immédiates
{_quick_wins_md(steps)}

---

## 12. Charges consommées
{charges_md}

---

## 13. Réserves et limites
{_reserve_md(state, now)}

---

## 14. Certifications et signatures d'audit
L'auditeur certifie l'exactitude des constats factuels mentionnés ci-dessus.

| Signature de l'Auditeur Cyber | Signature du Client Audité |
| :--- | :--- |
| **{auditeur or _AUDITEUR_DEFAUT}** | **DSI / Responsable de la sécurité** |
| Signature cryptographique locale : `SHA256:{docx_export.data_fingerprint(state)}` | Signature : |
"""
    else:
        raise TypeDocumentInconnu(doc_type)
        

    markdown_content += charte.pied_markdown(empreinte, cabinet=cabinet)
    return title, markdown_content
