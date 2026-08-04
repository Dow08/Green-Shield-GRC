"""demo_fixture.py — mission de démonstration complète (F16).

Recette du 31/07/2026 : la mission de démo existait mais restait trop pauvre
pour servir de vitrine — `aipd_required` à `False` supprimait le chapitre RGPD
de tous les rapports, la SoA sortait à 0/93 contrôles statués, et les
fonctionnalités les plus récentes (registre des violations, bibliothèque de
preuves, multi-référentiel) n'apparaissaient nulle part.

Ce module construit une mission **entièrement fictive** qui traverse chaque
fonctionnalité livrée, pour trois usages : démonstration commerciale, captures
d'écran de la documentation, et recette manuelle après une évolution.

Deux garde-fous, hérités des règles du projet :

  * **F16** — la mission est explicitement marquée (`is_demo`, « Fictive »
    dans le nom du client). Aucune confusion possible avec une mission réelle.
  * **« Zéro invention »** — la règle interdit d'inventer des faits *sur un
    client réel*. Un jeu de démonstration déclaré comme tel en est l'exception
    assumée depuis F16 : c'est précisément ce qui évite d'ouvrir une vraie
    mission cliente pour faire une démonstration.

Le module vit à part plutôt que dans `projects/crud.py` (déjà ~1400 lignes) :
une responsabilité, un fichier, testable isolément.
"""
from __future__ import annotations

from datetime import date, timedelta

from . import aipd as aipd_module
from . import soa as soa_module
from . import tprm

CLIENT = "Néobanque Fictive SAS"
NOM_MISSION = "DÉMO — Conformité ISO 27001 & DORA"

# Les deux référentiels actifs : une entité financière européenne relève de
# DORA *et* vise la certification ISO 27001 — c'est le cas d'usage qui
# justifie le multi-référentiel.
REFERENTIELS = ["iso27001", "dora"]


def _jour(decalage: int) -> str:
    """Date relative à aujourd'hui, pour que la démo ne périme jamais."""
    return (date.today() + timedelta(days=decalage)).isoformat()


def _controles_statues() -> list[dict]:
    """Check-list des deux référentiels, avec des constats d'audit réalistes.

    Les identifiants proviennent de `api/frameworks/{iso27001,dora}.yaml` :
    ils doivent rester alignés, les preuves ci-dessous s'y rattachent.
    """
    return [
        {"id": "ISO-A.5", "title": "Politiques de securite de l'information",
         "description": "Les politiques de securite de l'information doivent etre redigees, approuvees et diffusees.",
         "status": "CONFORME",
         "notes": "PSSI v3.1 approuvée en comité exécutif, diffusée à l'ensemble du personnel, revue annuelle planifiée.",
         "referentiel_id": "iso27001", "referentiel_name": "ISO/IEC 27001:2022"},
        {"id": "ISO-A.8.2", "title": "Droits d'acces privilégies",
         "description": "L'attribution et l'utilisation des droits d'acces privilégies doivent etre restreintes et controlees.",
         "status": "NON_CONFORME",
         "notes": "14 comptes d'administration de domaine actifs pour 6 administrateurs identifiés. Aucune revue trimestrielle formalisée.",
         "referentiel_id": "iso27001", "referentiel_name": "ISO/IEC 27001:2022"},
        {"id": "ISO-A.8.5", "title": "Authentification securisee",
         "description": "Des pratiques d'authentification forte doivent etre mises en oeuvre pour l'acces aux systemes.",
         "status": "CONFORME",
         "notes": "MFA imposé sur l'accès distant et les consoles d'administration. Constaté sur échantillon de 10 comptes.",
         "referentiel_id": "iso27001", "referentiel_name": "ISO/IEC 27001:2022"},
        {"id": "ISO-A.8.24", "title": "Utilisation de la cryptographie",
         "description": "Une politique sur l'utilisation de la cryptographie pour la protection des donnees doit etre definie.",
         "status": "A_VERIFIER",
         "notes": "Politique cryptographique rédigée mais non encore validée par la Direction — preuve d'approbation à obtenir.",
         "referentiel_id": "iso27001", "referentiel_name": "ISO/IEC 27001:2022"},
        {"id": "DORA-ICT", "title": "Cadre de gestion des risques TIC",
         "description": "Mettre en place un cadre rigoureux pour identifier, classifier et attenuer les risques lies aux technologies de l'information.",
         "status": "CONFORME",
         "notes": "Cadre de gestion des risques TIC formalisé, revu annuellement par le comité des risques.",
         "referentiel_id": "dora", "referentiel_name": "Reglement DORA"},
        {"id": "DORA-INC", "title": "Notification des incidents majeurs",
         "description": "Processus d'enregistrement, classification et declaration obligatoire des incidents de securite.",
         "status": "NON_CONFORME",
         "notes": "Procédure de classification existante, mais le délai de notification à l'autorité compétente n'a jamais été testé en conditions réelles.",
         "referentiel_id": "dora", "referentiel_name": "Reglement DORA"},
        {"id": "DORA-TEST", "title": "Tests de resilience operationnelle",
         "description": "Realisation de tests annuels sur les systemes d'information, y compris des tests de penetration (TLPT).",
         "status": "A_VERIFIER",
         "notes": "Dernier test d'intrusion daté de 14 mois — la cadence annuelle exigée reste à confirmer pour l'exercice en cours.",
         "referentiel_id": "dora", "referentiel_name": "Reglement DORA"},
        {"id": "DORA-3P", "title": "Gestion du risque tiers",
         "description": "Suivi continu de l'exposition aux risques lies aux fournisseurs externes de services TIC.",
         "status": "CONFORME",
         "notes": "Registre des prestataires TIC critiques tenu à jour, revu au comité des risques (cf. phase 3).",
         "referentiel_id": "dora", "referentiel_name": "Reglement DORA"},
    ]


def _soa_partiellement_statuee() -> list[dict]:
    """SoA ISO 27001 avec une partie des 93 contrôles tranchée.

    Volontairement incomplète : un audit réel n'est jamais statué à 100 % en
    cours de mission, et la barre de progression de `SoaPanel` n'aurait aucun
    sens à 0 % comme à 100 %.
    """
    decisions = {
        "A.5.1": (True, "Implémenté", "PSSI v3.1 approuvée en comité exécutif.", "PSSI-v3.1.pdf"),
        "A.5.2": (True, "Implémenté", "Rôles SSI définis dans la charte de gouvernance.", "Charte-gouvernance-SSI.pdf"),
        "A.5.7": (True, "Partiel", "Veille sur les menaces en place, sans corrélation automatisée.", "Procedure-veille.pdf"),
        "A.5.15": (True, "Implémenté", "Politique de contrôle d'accès formalisée.", "PSSI-v3.1.pdf"),
        "A.5.19": (True, "Implémenté", "Exigences de sécurité intégrées aux contrats fournisseurs.", "Clausier-fournisseurs.pdf"),
        "A.5.23": (True, "Partiel", "Services cloud recensés, revue de configuration à formaliser.", ""),
        "A.6.3": (True, "Planifié", "Campagne de sensibilisation programmée au prochain trimestre.", ""),
        "A.7.4": (False, "", "Aucun local technique en propre : hébergement intégralement externalisé.", ""),
        "A.7.11": (False, "", "Services généraux à la charge de l'hébergeur, hors périmètre du SMSI.", ""),
        "A.8.2": (True, "Partiel", "Comptes privilégiés identifiés, revue trimestrielle non formalisée.", ""),
        "A.8.5": (True, "Implémenté", "MFA imposé sur les accès distants et d'administration.", "Capture-config-MFA.png"),
        "A.8.7": (True, "Implémenté", "EDR déployé sur l'ensemble du parc.", "Inventaire-EDR.xlsx"),
        "A.8.13": (True, "Implémenté", "Sauvegardes immuables quotidiennes, restauration testée.", "PV-test-restauration.pdf"),
        "A.8.24": (True, "Partiel", "Politique cryptographique rédigée, validation Direction en attente.", ""),
        "A.8.28": (True, "Planifié", "Revue de code sécurisée à intégrer à la chaîne de livraison.", ""),
    }
    entrees = soa_module.entrees_par_defaut()
    for entree in entrees:
        decision = decisions.get(entree["code"])
        if not decision:
            continue
        applicable, statut, justification, document = decision
        entree["applicable"] = applicable
        entree["statut"] = statut or None
        entree["justification"] = justification
        entree["document_reference"] = document
        entree["owner"] = "RSSI" if applicable else "Direction des Opérations"
        entree["date_revue"] = _jour(90)
    return entrees


def _preuves() -> list[dict]:
    """Bibliothèque de preuves — dont une preuve **partagée** entre les deux
    référentiels, qui est la raison d'être de la fonctionnalité."""
    return [
        {
            "id": "PRV-01",
            "libelle": "PSSI v3.1 approuvée en comité exécutif",
            "description": "Politique de sécurité de l'information, signée et diffusée.",
            "document_reference": "PSSI-v3.1.pdf",
            "date": _jour(-120),
            # Une seule preuve, deux référentiels : ISO exige la politique,
            # DORA exige le cadre de gestion des risques TIC qu'elle porte.
            "controles_lies": [
                {"referentiel_id": "iso27001", "control_id": "ISO-A.5"},
                {"referentiel_id": "dora", "control_id": "DORA-ICT"},
            ],
        },
        {
            "id": "PRV-02",
            "libelle": "Capture de configuration MFA (console d'administration)",
            "description": "Preuve technique de l'authentification forte sur les accès privilégiés.",
            "document_reference": "Capture-config-MFA.png",
            "date": _jour(-30),
            "controles_lies": [
                {"referentiel_id": "iso27001", "control_id": "ISO-A.8.5"},
            ],
        },
        {
            "id": "PRV-03",
            "libelle": "Registre des prestataires TIC critiques",
            "description": "Recensement des fournisseurs, criticité et clauses contractuelles associées.",
            "document_reference": "Registre-prestataires-TIC.xlsx",
            "date": _jour(-45),
            "controles_lies": [
                {"referentiel_id": "dora", "control_id": "DORA-3P"},
            ],
        },
    ]


def _violations() -> list[dict]:
    """Registre des violations — les deux branches de la règle des 72 h.

    VIO-01 notifiée dans les délais, VIO-02 non notifiée mais justifiée :
    l'article 33 n'impose la notification que si la violation présente un
    risque pour les droits et libertés. Aucune des deux ne doit déclencher
    l'alerte de `revue_export.py`.
    """
    return [
        {
            "id": "VIO-01",
            "date_constat": _jour(-60),
            "date_notification_cnil": _jour(-59),
            "nature": "Envoi d'un courriel de relance à une liste de clients en copie visible",
            "categories_donnees": "Identité, adresse électronique",
            "nb_personnes": "312",
            "consequences": "Divulgation des adresses électroniques des destinataires entre eux.",
            "mesures": "Rappel du message, note de service sur l'usage de la copie cachée, formation ciblée du service concerné.",
            "notifiee_cnil": True,
            "personnes_informees": True,
            "justification": "",
        },
        {
            "id": "VIO-02",
            "date_constat": _jour(-20),
            "date_notification_cnil": "",
            "nature": "Perte d'un ordinateur portable de collaborateur en déplacement",
            "categories_donnees": "Aucune donnée client — poste de développement",
            "nb_personnes": "0",
            "consequences": "Aucune : disque intégralement chiffré, aucune donnée personnelle stockée localement.",
            "mesures": "Effacement à distance confirmé, révocation des certificats, remplacement du poste.",
            "notifiee_cnil": False,
            "personnes_informees": False,
            "justification": "Disque chiffré (AES-256) rendant les données inintelligibles : aucun risque pour les droits et libertés (Art. 33 §1). Violation consignée au registre interne au titre de l'Art. 33 §5.",
        },
    ]


def _aipd() -> dict:
    """AIPD requise et conduite — sans quoi le chapitre RGPD est absent des
    rapports, ce qui masquait tout le module en démonstration."""
    obligations = aipd_module.obligations_par_defaut()
    commentaires = {
        "DPO": "Avis favorable avec réserve du DPO interne, rendu le " + _jour(-75) + " : maintien d'une vigilance sur le risque de discrimination indirecte.",
        "PERSONNES": "Panel de 12 clients consulté ; incompréhension majoritaire des motifs de refus, à l'origine de la mesure de motivation en langage clair.",
        "LISTES_CNIL": "Traitement figurant sur la liste CNIL des traitements soumis (décision automatisée avec effet juridique) — AIPD obligatoire.",
        "REEXAMEN": "Réexamen déclenché à chaque réentraînement du modèle de score, et au minimum une fois par an.",
        "ART36": "Risque résiduel qualifié d'acceptable après mesures : la consultation préalable de la CNIL n'est pas due.",
    }
    for obligation in obligations:
        obligation["satisfait"] = True
        obligation["commentaire"] = commentaires.get(obligation["id"], "")
    return {
        "treatment_description": (
            "Score automatisé d'octroi de crédit à la consommation, appliqué à l'ensemble des "
            "demandes de clients particuliers. Combine données déclaratives, historique interne "
            "et fichiers d'incidents de paiement."
        ),
        "necessity_eval": (
            "L'évaluation de solvabilité répond à une obligation prudentielle. L'automatisation est "
            "proportionnée au volume traité (environ 2 800 demandes par mois) ; les variables du "
            "modèle ont été ramenées de 47 à 31 après revue de pertinence."
        ),
        "risks_eval": (
            "Risque principal : discrimination indirecte par des variables corrélées à l'origine "
            "géographique. Gravité élevée (effet juridique et économique durable), vraisemblance "
            "moyenne. Risque secondaire : opacité de la décision pour la personne concernée."
        ),
        "mitigation_measures": (
            "Retrait du code postal et des quatre variables les plus corrélées, test de disparité "
            "annuel par cohortes, motivation systématique du refus en langage clair, droit à une "
            "intervention humaine sous 15 jours, journalisation des décisions pendant 5 ans."
        ),
        "risque_residuel": "acceptable",
        "obligations": obligations,
    }


def _scenarios() -> list[dict]:
    """Scénarios EBIOS RM avec la chaîne de traitement complète (Lot A) :
    propriétaire, risque résiduel, stratégie et statut."""
    return [
        {"id": "SO-01",
         "event": "Hameçonnage d'un poste du support, pivot vers l'annuaire, élévation de privilèges puis chiffrement des serveurs de production.",
         "gravity": 4, "likelihood": 3,
         "mitigation": "MFA généralisé, cloisonnement réseau des postes, bastion d'administration.",
         "actif_concerne": "Annuaire d'entreprise et serveurs de production",
         "gravite_residuelle": 3, "vraisemblance_residuelle": 2,
         "strategie_traitement": "Réduire", "owner": "RSSI",
         "date_revue": _jour(60), "statut": "En traitement"},
        {"id": "SO-02",
         "event": "Compromission de la console d'administration de l'infogéreur, rebond vers le système d'information.",
         "gravity": 4, "likelihood": 2,
         "mitigation": "Accès tiers par VPN nominatif dédié, revue trimestrielle des comptes prestataires.",
         "actif_concerne": "Console d'administration tierce",
         "gravite_residuelle": 3, "vraisemblance_residuelle": 1,
         "strategie_traitement": "Réduire", "owner": "DSI",
         "date_revue": _jour(60), "statut": "En traitement"},
        {"id": "SO-03",
         "event": "Indisponibilité prolongée du service de paiement instantané à la suite d'une panne de l'hébergeur.",
         "gravity": 3, "likelihood": 2,
         "mitigation": "Bascule sur site de repli testée semestriellement, clause de réversibilité contractuelle.",
         "actif_concerne": "Plateforme de paiement instantané",
         "gravite_residuelle": 2, "vraisemblance_residuelle": 1,
         "strategie_traitement": "Transférer", "owner": "Directeur des Opérations",
         "date_revue": _jour(120), "statut": "Ouvert"},
        {"id": "SO-04",
         "event": "Contestation d'une décision de refus de crédit automatisée, faute de motivation intelligible.",
         "gravity": 2, "likelihood": 3,
         "mitigation": "Motivation en langage clair, droit à l'intervention humaine sous 15 jours.",
         "actif_concerne": "Modèle de score d'octroi",
         "gravite_residuelle": 1, "vraisemblance_residuelle": 2,
         "strategie_traitement": "Accepter", "owner": "DPO",
         "date_revue": _jour(180), "statut": "Clos"},
    ]


def _remediations() -> list[dict]:
    """Plan de traitement piloté — chaque mesure porte un responsable, une
    échéance et le scénario qu'elle traite (`risque_lie` → `_scenarios`)."""
    return [
        {"id": "REM-01", "axe": "Protection",
         "measure": "Ramener les comptes d'administration de domaine au strict nécessaire et instaurer une revue trimestrielle.",
         "priority": "Critique", "responsable": "RSSI", "echeance": _jour(30),
         "statut": "En cours", "cout_estime": "Négligeable", "risque_lie": "SO-01"},
        {"id": "REM-02", "axe": "Détection",
         "measure": "Tester en conditions réelles la chaîne de notification d'incident majeur à l'autorité compétente (DORA).",
         "priority": "Élevé", "responsable": "Responsable Conformité", "echeance": _jour(45),
         "statut": "À faire", "cout_estime": "Léger", "risque_lie": "SO-02"},
        {"id": "REM-03", "axe": "Gouvernance",
         "measure": "Faire valider la politique cryptographique par la Direction et en conserver la preuve d'approbation.",
         "priority": "Moyen", "responsable": "RSSI", "echeance": _jour(60),
         "statut": "À faire", "cout_estime": "Négligeable", "risque_lie": "SO-01"},
        {"id": "REM-04", "axe": "Résilience",
         "measure": "Planifier le test d'intrusion annuel exigé par DORA et en formaliser le périmètre.",
         "priority": "Élevé", "responsable": "DSI", "echeance": _jour(90),
         "statut": "À faire", "cout_estime": "Élevé", "risque_lie": "SO-03"},
        {"id": "REM-05", "axe": "Protection",
         "measure": "Généraliser les sauvegardes immuables et rejouer un test de restauration complet.",
         "priority": "Critique", "responsable": "DSI", "echeance": _jour(-10),
         "statut": "Fait", "cout_estime": "Moyen", "risque_lie": "SO-01"},
    ]


def _socle() -> dict:
    """Socle de mission : ce qui alimente le chapitre « Cadrage » du rapport."""
    return {
        "qualification": {
            "declencheur": "Échéance réglementaire DORA et objectif de certification ISO 27001 sous 12 mois.",
            "sponsor_executif": "Directeur Général",
            "budget": "24 jours",
            "maturite_actuelle": "Politiques écrites mais inégalement appliquées ; aucune revue d'accès formalisée.",
            "equipe_interne": "RSSI (0,5 ETP), DSI (0,3 ETP), DPO (0,2 ETP)",
            "echeance_cible": _jour(300),
        },
        "contractualisation": {
            "perimetre_inclus": "Système d'information de production, service de paiement instantané, modèle de score d'octroi.",
            "perimetre_exclu": "Réseau d'agences physiques et filiale étrangère (entités juridiques distinctes).",
            "livrables": ["Rapport d'audit", "Déclaration d'Applicabilité", "AIPD", "PSSI / PRI", "Analyse EBIOS RM"],
            "modalites": "Audit sur pièces et entretiens, deux comités de suivi mensuels.",
            "acces_si": "Lecture seule sur les configurations, accompagné par l'équipe système.",
        },
        "kickoff": {
            "date": _jour(-90),
            "participants": ["Directeur Général", "DSI", "RSSI", "DPO", "Responsable Conformité"],
            "gouvernance": "Comité de suivi bimensuel, arbitrages en comité exécutif.",
        },
        "entretiens": [
            {"role": "RSSI", "date": _jour(-85),
             "synthese": "Politiques rédigées et diffusées ; revue des accès privilégiés reconnue comme non formalisée."},
            {"role": "DSI", "date": _jour(-84),
             "synthese": "Infrastructure intégralement externalisée ; bascule sur site de repli testée deux fois par an."},
            {"role": "DPO", "date": _jour(-80),
             "synthese": "AIPD du score d'octroi conduite ; avis favorable avec réserve sur le risque de discrimination indirecte."},
            {"role": "Responsable Conformité", "date": _jour(-78),
             "synthese": "Chaîne de notification d'incident DORA documentée mais jamais éprouvée en conditions réelles."},
            {"role": "Responsable Production", "date": _jour(-76),
             "synthese": "Sauvegardes immuables quotidiennes ; dernière restauration complète testée avec succès."},
        ],
        "temps": {"entrees": [
            {"id": "T-001", "phase": "cadrage", "minutes": 960, "date": _jour(-88), "note": "Cadrage, réunion de lancement et 5 entretiens"},
            {"id": "T-002", "phase": "diagnostic", "minutes": 1200, "date": _jour(-70), "note": "Diagnostic ISO/DORA, registre RGPD et AIPD"},
            {"id": "T-003", "phase": "tprm", "minutes": 720, "date": _jour(-55), "note": "Registre des prestataires TIC critiques"},
            {"id": "T-004", "phase": "ebios", "minutes": 600, "date": _jour(-40), "note": "Ateliers EBIOS RM et scénarios opérationnels"},
            {"id": "T-005", "phase": "resilience", "minutes": 480, "date": _jour(-25), "note": "Revue de continuité et séquence E3R"},
            {"id": "T-006", "phase": "traitement", "minutes": 540, "date": _jour(-10), "note": "Plan de remédiation et restitution"},
        ]},
        "rgpd_consultant": {
            "duree_conservation_mois": 36,
            "date_fin_mission": _jour(210),
            "purge_effectuee_le": "",
        },
    }


def construire(project_id: str) -> dict:
    """Mission de démonstration complète, prête à être exportée."""
    maintenant = date.today().strftime("%Y-%m-%d %H:%M")
    controles = _controles_statues()

    return {
        "id": project_id,
        "name": NOM_MISSION,
        "client": CLIENT,
        "type": "grc",
        "status": "en_cours",
        "progress": 0,  # recalculé par l'appelant
        "created_at": maintenant,
        "updated_at": maintenant,
        "is_demo": True,
        "socle": _socle(),
        "grc": {"active": True, "referentiels_actifs": list(REFERENTIELS), "parcours": {}},
        "consulting": {"active": False},
        "steps": {
            "cadrage": {
                "scope": "Système d'information de production, service de paiement instantané et modèle de score d'octroi de crédit.",
                "client_missions": "Établissement de paiement fictif, 180 collaborateurs, 95 000 clients particuliers. Soumis à DORA et engagé dans une démarche de certification ISO 27001.",
                "nda_signed": True,
                "nda_text": (
                    "ACCORD DE CONFIDENTIALITÉ & DE NON-DIVULGATION (NDA)\n\n"
                    "Document de DÉMONSTRATION — aucune valeur contractuelle.\n\n"
                    "Objet : encadrement des échanges d'informations confidentielles dans le cadre "
                    f"de la mission d'audit de sécurité et de conformité de {CLIENT}.\n\n"
                    "Engagements : les parties s'engagent à ne divulguer aucun document technique, "
                    "secret de fabrique, identifiant, schéma d'architecture ou donnée personnelle."
                ),
                "assets_metier": [
                    {"id": "VM-01", "name": "Comptes et soldes clients", "description": "Registre des positions clients, cœur du système.", "is_personal_data": True},
                    {"id": "VM-02", "name": "Service de paiement instantané", "description": "Fonction critique au sens DORA — indisponibilité immédiatement visible du client.", "is_personal_data": True},
                    {"id": "VM-03", "name": "Modèle de score d'octroi de crédit", "description": "Décision partiellement automatisée avec effet juridique (RGPD Art. 22).", "is_personal_data": True},
                ],
                "assets_support": [
                    {"id": "BS-01", "name": "Cœur bancaire (éditeur externe)", "type": "Logiciel", "description": "Progiciel hébergé chez l'éditeur, version N-1.", "owner": "DSI"},
                    {"id": "BS-02", "name": "Plateforme de paiement instantané", "type": "Logiciel", "description": "Disponibilité 24/7 exigée.", "owner": "Directeur des Opérations"},
                    {"id": "BS-03", "name": "Annuaire d'entreprise", "type": "Logiciel", "description": "Contrôle d'accès et annuaire d'identité.", "owner": "DSI"},
                    {"id": "BS-04", "name": "Collecte et corrélation des journaux", "type": "Logiciel", "description": "Rétention 12 mois.", "owner": "RSSI"},
                ],
                "framework_id": REFERENTIELS[0],
                "framework_name": "ISO/IEC 27001:2022",
                "framework_ids": list(REFERENTIELS),
                "validated": True,
            },
            "diagnostic": {
                "pssi_active": True,
                "governance_active": True,
                "vulnerabilities_active": True,
                "rgpd_register": [
                    {"id": "RGPD-01", "name": "Gestion des comptes et opérations", "purpose": "Exécution du contrat de services de paiement.",
                     "data_categories": "Identité, coordonnées, données financières, historiques d'opérations", "retention": "Durée de la relation + 5 ans"},
                    {"id": "RGPD-02", "name": "Lutte contre le blanchiment", "purpose": "Obligation légale de vigilance et de déclaration.",
                     "data_categories": "Identité, origine des fonds, alertes de profilage", "retention": "5 ans après la fin de la relation"},
                    {"id": "RGPD-03", "name": "Score d'octroi de crédit", "purpose": "Évaluation de la solvabilité — décision partiellement automatisée.",
                     "data_categories": "Revenus, charges, historique d'incidents, score calculé", "retention": "Durée du crédit + 5 ans"},
                ],
                "aipd_required": True,
                "aipd": _aipd(),
                "violations": _violations(),
                "validated": True,
            },
            "tprm": {"tiers": [
                {"name": "Hébergeur du cœur bancaire", "dependence": 5, "penetration": 4, "maturity": 4, "trust": 4,
                 "exigences": tprm.exigences_par_defaut()},
                {"name": "Prestataire d'infogérance", "dependence": 4, "penetration": 5, "maturity": 3, "trust": 3,
                 "exigences": tprm.exigences_par_defaut()},
                {"name": "Éditeur du moteur de score", "dependence": 3, "penetration": 2, "maturity": 4, "trust": 4,
                 "exigences": tprm.exigences_par_defaut()},
            ], "validated": True},
            "ebios": {
                "redoute_events": [
                    {"id": "ER-01", "event": "Indisponibilité totale du service de paiement instantané", "gravity": 4,
                     "impact": "Interruption immédiate du service client, exposition réglementaire au titre de DORA."},
                    {"id": "ER-02", "event": "Divulgation massive de données de comptes clients", "gravity": 4,
                     "impact": "Atteinte grave aux personnes concernées, notification CNIL, perte de confiance durable."},
                    {"id": "ER-03", "event": "Décision de crédit automatisée jugée discriminatoire", "gravity": 3,
                     "impact": "Sanction de l'autorité de contrôle et contentieux individuels."},
                ],
                "risk_sources": [
                    {"id": "SR-01", "name": "Cybercriminel motivé par le gain", "objective": "Extorsion par rançongiciel."},
                    {"id": "SR-02", "name": "Prestataire compromis", "objective": "Rebond vers le système d'information du client."},
                    {"id": "SR-03", "name": "Autorité de contrôle", "objective": "Sanction administrative en cas de manquement."},
                ],
                "operational_scenarios": _scenarios(),
                "case_studies": [
                    {"case": "Fuite de données d'un grand groupe hôtelier",
                     "lessons": "Chiffrement des bases et contrôle strict des privilèges : deux mesures qui auraient contenu l'incident."},
                    {"case": "Panne majeure d'un hébergeur européen",
                     "lessons": "Une clause de réversibilité sans test de bascule réel n'offre aucune garantie de reprise."},
                ],
                "validated": True,
            },
            "resilience": {
                "logging_active": True,
                "bcp_strategy": {
                    "rto": "4 heures",
                    "rpo": "15 minutes",
                    "backup_policy": "Sauvegardes immuables quotidiennes, conservation 35 jours, restauration testée semestriellement.",
                },
                "e3r": {
                    "endiguement": "Isolement automatique des segments réseau concernés sur alerte de l'EDR.",
                    "eviction": "Réinitialisation des comptes d'administration et des secrets d'infrastructure.",
                    "eradication": "Reconstruction des serveurs compromis à partir de gabarits durcis, jamais de restauration en l'état.",
                    "reconstruction": "Remise en service progressive, service de paiement en dernier après validation de l'intégrité.",
                },
                "strategie_remediation": {
                    "urgence_redemarrage": "Le service de paiement instantané est une fonction critique au sens DORA : chaque heure d'interruption est directement visible du client et déclarable à l'autorité.",
                    "couts_risques_redemarrage": "Un redémarrage avant éradication complète expose à une ré-infection et à la perte des traces d'investigation.",
                    "decision_direction": "Direction Générale : éradication complète avant toute remise en service, délai maximal accepté de 48 heures, communication client dès la 4ᵉ heure.",
                },
                "validated": True,
            },
            "evaluation": {
                "manual_controls": controles,
                "technical_results": None,
                "soa": _soa_partiellement_statuee(),
                "preuves": _preuves(),
            },
            "traitement": {
                "remediations": _remediations(),
                "quick_wins": [
                    "Désactiver les comptes d'administration dormants",
                    "Formaliser la revue trimestrielle des accès privilégiés",
                    "Faire approuver la politique cryptographique",
                    "Planifier le test d'intrusion annuel DORA",
                    "Rejouer un test de notification d'incident de bout en bout",
                ],
                "validated": True,
            },
            "restitution": {
                "exec_summary": (
                    "L'audit conjoint ISO 27001 / DORA de la Néobanque Fictive met en évidence un socle de "
                    "gouvernance solide — politiques approuvées, authentification forte généralisée, sauvegardes "
                    "immuables éprouvées — et deux écarts majeurs à traiter en priorité.\n\n"
                    "Le premier porte sur les accès privilégiés : quatorze comptes d'administration de domaine "
                    "restent actifs pour six administrateurs identifiés, sans revue formalisée. C'est le chemin "
                    "d'attaque du scénario le plus grave retenu en analyse de risque.\n\n"
                    "Le second relève de DORA : la chaîne de notification d'un incident majeur est documentée "
                    "mais n'a jamais été éprouvée en conditions réelles, ce qui ne permet pas de démontrer le "
                    "respect des délais réglementaires.\n\n"
                    "Aucun écart ne remet en cause la trajectoire de certification, sous réserve de la clôture "
                    "des deux mesures critiques du plan de traitement."
                ),
                "remediation_plan": [],
                "validated": True,
            },
        },
    }
