from __future__ import annotations
import os
import json
import re
import shutil
import unicodedata
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, Depends
import yaml
from ..database.models import User
from ..auth import get_current_user
from .. import aipd
from .. import archive
from .. import auditcraft_grc
from .. import ai_gateway
from .. import controles_techniques
from .. import audit_log
from .. import couverture
from .. import data_paths
from .. import docx_export
from .. import schema_migration
from .. import workflow_loader
from .. import mesures_catalogue
from .. import path_safety
from .. import report_builder
from .. import report_docx
from .. import report_html
from .. import retention
from .. import revue_export
from .. import snapshots
from .. import soa
from .. import tprm

router = APIRouter(prefix="/api")

from . import PROJECTS_DIR, _write_json_atomic, _read_state, calculate_progress, get_framework_by_id, _rempli, _tprm_rate, _chiffrer, _dechiffrer

def _nda_template(client: str) -> str:
    """Gabarit de NDA à compléter — un modèle, pas un constat sur le client."""
    return f"""ACCORD DE CONFIDENTIALITÉ & DE NON-DIVULGATION (NDA)

Entre :
La société DP Cyber Consulting, représentée par Dorian, Consultant en Cybersécurité,
Et :
La société {client}, représentée par son DSI/Représentant légal.

Objet : Encadrement des échanges d'informations hautement confidentielles dans le cadre de la mission d'accompagnement, d'audit de sécurité et de GRC de {client}.

Engagements : Les parties s'engagent à ne divulguer aucun document technique, secret de fabrique, mot de passe, schéma d'architecture ou donnée personnelle sous peine de poursuites civiles et pénales."""


def create_empty_state(project_id: str, name: str, client: str, project_type: str,
                       framework_id: str = "iso27001", framework_ids: list[str] | None = None) -> dict:
    """Mission neuve : la structure complète, **aucune donnée d'exemple**.

    Les missions étaient jusqu'ici pré-remplies d'actifs, de tiers, d'événements
    redoutés et de mesures fictifs. Constaté en recette le 29/07/2026 : une
    mission créée pour un fabricant de composites contenait d'emblée « Hébergeur
    Cloud (AWS) », « Prestataire Infogérance (ESN) » et « Cabinet Comptable »,
    **déjà notés**. Un consultant qui ne les remarque pas livre un registre de
    tiers partiellement fictif, criticités comprises — c'était le scénario
    d'invention le plus probable de l'application.

    Ces exemples vivent désormais dans la seule mission de démonstration, qui
    porte le marqueur `is_demo` (F16).

    Seules exceptions conservées, parce qu'elles ne prétendent rien sur le
    client : le gabarit de NDA (un modèle à compléter) et, sur le volet GRC, la
    check-list du référentiel choisi (c'est le référentiel, pas une donnée
    client).
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    state = {
        "id": project_id, "name": name, "client": client, "type": project_type,
        "status": "en_cours", "progress": 0, "created_at": now, "updated_at": now,
        "steps": {
            "cadrage": {
                "scope": "", "client_missions": "",
                "nda_signed": False, "nda_text": _nda_template(client),
                "assets_metier": [], "assets_support": [],
            },
            "diagnostic": {
                "pssi_active": False, "governance_active": False,
                "vulnerabilities_active": False, "rgpd_register": [],
                "aipd_required": False,
                "aipd": {"treatment_description": "", "necessity_eval": "",
                         "risks_eval": "", "mitigation_measures": ""},
                "violations": [],
            },
            "tprm": {"tiers": []},
            "ebios": {"redoute_events": [], "risk_sources": [],
                      "operational_scenarios": [], "case_studies": []},
            "resilience": {
                "logging_active": False,
                "bcp_strategy": {"rto": "", "rpo": "", "backup_policy": ""},
                "e3r": {"endiguement": "", "eviction": "",
                        "eradication": "", "reconstruction": ""},
                "strategie_remediation": {"urgence_redemarrage": "",
                                          "couts_risques_redemarrage": "",
                                          "decision_direction": ""},
            },
            "traitement": {"remediations": [], "quick_wins": []},
            "restitution": {"exec_summary": "", "remediation_plan": []},
        },
    }

    if project_type == "grc":
        # `framework_ids` (pluriel) porte la liste complète des référentiels
        # actifs — un client réel peut être soumis à ISO 27001 *et* DORA *et*
        # NIS2 à la fois (31/07/2026). Le premier élément reste le référentiel
        # « pivot » (framework_id/name singuliers, compat avec le workflow
        # guidé ISO 27001 et l'affichage existants).
        ids = framework_ids or [framework_id]
        fw = get_framework_by_id(ids[0]) or {}
        state["steps"]["cadrage"]["framework_id"] = ids[0]
        state["steps"]["cadrage"]["framework_name"] = fw.get("name", ids[0])
        state["steps"]["cadrage"]["framework_ids"] = ids

        manual_controls = []
        for fw_id in ids:
            referentiel = get_framework_by_id(fw_id) or {}
            manual_controls += [
                {"id": req.get("id"), "title": req.get("title"),
                 "description": req.get("description", ""),
                 "status": "A_VERIFIER", "notes": "",
                 "referentiel_id": fw_id, "referentiel_name": referentiel.get("name", fw_id)}
                for req in referentiel.get("requirements", [])
            ]
        state["steps"]["evaluation"] = {
            "manual_controls": manual_controls,
            "technical_results": None,
        }
        # Déclaration d'Applicabilité (SoA) : uniquement si ISO 27001 fait
        # partie des référentiels actifs, dont c'est une exigence de
        # certification (clause 6.1.3 d) — une mission DORA/NIS2 seule n'a
        # pas à porter 93 contrôles hors sujet.
        if "iso27001" in ids:
            state["steps"]["evaluation"]["soa"] = soa.entrees_par_defaut()

    return state


def create_default_state(project_id: str, name: str, client: str, project_type: str,
                         framework_id: str = "iso27001", framework_ids: list[str] | None = None) -> dict:
    """État **garni de données d'exemple** — réservé à la mission de démonstration.

    Ne pas appeler pour une mission réelle : voir `create_empty_state`.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    state = {
        "id": project_id,
        "name": name,
        "client": client,
        "type": project_type,
        "status": "en_cours",
        "progress": 0,
        "created_at": now,
        "updated_at": now,
        "steps": {}
    }
    
    # Template NDA
    nda_text = f"""ACCORD DE CONFIDENTIALITÉ & DE NON-DIVULGATION (NDA)

Entre :
La société DP Cyber Consulting, représentée par Dorian, Consultant en Cybersécurité,
Et :
La société {client}, représentée par son DSI/Représentant légal.

Objet : Encadrement des échanges d'informations hautement confidentielles dans le cadre de la mission d'accompagnement, d'audit de sécurité et de GRC de {client}.

Engagements : Les parties s'engagent à ne divulguer aucun document technique, secret de fabrique, mot de passe, schéma d'architecture ou donnée personnelle sous peine de poursuites civiles et pénales."""

    # Base common structures
    assets_metier_consulting = [
        {"id": "VM-01", "name": "Fichier Clients & Prospects", "description": "Contient les coordonnées, contrats et historiques d'achats.", "is_personal_data": True},
        {"id": "VM-02", "name": "Algorithmes de R&D", "description": "Savoir-faire clé de l'entreprise pour la fabrication des produits.", "is_personal_data": False}
    ]
    assets_support_consulting = [
        {"id": "BS-01", "name": "Active Directory (AD)", "type": "Logiciel", "description": "Contrôle d'accès et annuaire d'identité.", "owner": "Équipe Système"},
        {"id": "BS-02", "name": "Serveurs Cloud AWS (Prod)", "type": "Matériel", "description": "Héberge le portail client de production.", "owner": "Équipe DevOps"},
        {"id": "BS-03", "name": "Postes de travail (Collaborateurs)", "type": "Matériel", "description": "Ordinateurs portables sous Windows.", "owner": "Support IT"}
    ]

    if project_type == "consulting":
        state["steps"] = {
            "cadrage": {
                "scope": "Ensemble du Système d'Information critique, périmètre DSI et filiales.",
                "client_missions": "Fournir des services numériques à forte valeur ajoutée en garantissant la haute disponibilité et l'intégrité des transactions.",
                "nda_signed": False,
                "nda_text": nda_text,
                "assets_metier": assets_metier_consulting,
                "assets_support": assets_support_consulting
            },
            "diagnostic": {
                "pssi_active": False,
                "governance_active": False,
                "vulnerabilities_active": False,
                "rgpd_register": [
                    {"id": "RGPD-01", "name": "Gestion des comptes clients", "purpose": "Fournir l'accès au service et assurer la facturation.", "data_categories": "Nom, Prénom, Email, Coordonnées Bancaires", "retention": "Durée du contrat + 3 ans"}
                ],
                "aipd_required": True,
                "aipd": {
                    "treatment_description": "Traitement de profilage automatique des habitudes d'achats des clients à l'aide de modèles statistiques.",
                    "necessity_eval": "Le traitement est indispensable pour adapter l'offre commerciale et réduire le taux de résiliation, respectant la minimisation des données collectées.",
                    "risks_eval": "Origine : Hameçonnage ou piratage de compte administrateur. Risque : Divulgation illicite de données d'achats sensibles (Gravité Élevée, Vraisemblance Moyenne).",
                    "mitigation_measures": "Chiffrement AES-256 de la base de données, authentification forte (MFA) pour tous les administrateurs et journalisation d'audit continue des accès."
                }
            },
            "tprm": {
                "tiers": [
                    {"name": "Hébergeur Cloud (AWS)", **_tprm_rate(5, 5, 4, 4)},
                    {"name": "Prestataire Infogérance (ESN)", **_tprm_rate(4, 5, 3, 3)},
                    {"name": "Cabinet Comptable", **_tprm_rate(2, 1, 2, 4)},
                ]
            },
            "ebios": {
                "redoute_events": [
                    {"id": "ER-01", "event": "Chiffrement complet du SI par Ransomware", "gravity": 4, "impact": "Paralysie complète de l'activité, pertes financières de 50k€/jour."},
                    {"id": "ER-02", "event": "Fuite de la base de R&D (Espionnage)", "gravity": 3, "impact": "Perte de l'avantage concurrentiel stratégique de l'entreprise."}
                ],
                "risk_sources": [
                    {"id": "SR-01", "name": "Cybercriminels motivés par l'appât du gain", "objective": "Extorsion financière (Ransomware)."},
                    {"id": "SR-02", "name": "Concurrent direct déloyal", "objective": "Espionnage industriel et vol de secrets R&D."}
                ],
                "operational_scenarios": [
                    {"id": "SO-01", "event": "Intrusion via phishing d'un poste support, pivot vers l'Active Directory, élévation de privilèges et sabotage des serveurs de prod.", "gravity": 4, "likelihood": 3, "mitigation": "MFA, cloisonnement réseau des postes, et bastions d'administration.",
                     "actif_concerne": "Active Directory + serveurs de production", "gravite_residuelle": 3, "vraisemblance_residuelle": 2,
                     "strategie_traitement": "Réduire", "owner": "RSSI", "date_revue": "2026-10-15", "statut": "En traitement"},
                    {"id": "SO-02", "event": "Attaque par rebond via la compromise de la console d'administration du prestataire d'infogérance tiers.", "gravity": 3, "likelihood": 2, "mitigation": "Limitation des accès tiers par VPN IPsec dédié, et audit de sécurité du prestataire.",
                     "actif_concerne": "Console d'administration tierce", "gravite_residuelle": 2, "vraisemblance_residuelle": 1,
                     "strategie_traitement": "Réduire", "owner": "DSI", "date_revue": "2026-10-15", "statut": "Ouvert"}
                ],
                "case_studies": [
                    {"case": "Marriott (Fuite de données)", "lessons": "Importance cruciale du chiffrement des bases de données et du contrôle strict des privilèges de base."},
                    {"case": "Pathé (Arnaque président)", "lessons": "Gouvernance de validation des virements bancaires manuels et double signature requise."},
                    {"case": "Biotech (Sabotage)", "lessons": "Cloisonnement hermétique de la R&D et restriction d'accès aux prestataires industriels tierces."}
                ]
            },
            "resilience": {
                "logging_active": False,
                "bcp_strategy": {
                    "rto": "4 heures",
                    "rpo": "24 heures",
                    "backup_policy": "Sauvegardes immuables quotidiennes hébergées hors-ligne (air-gapped) avec restauration testée semestriellement."
                },
                "e3r": {
                    "endiguement": "Procédure d'isolement automatique des VLANs de postes de travail en cas d'alerte EDR.",
                    "eviction": "Procédure d'isolement de l'Active Directory, réinitialisation complète des mots de passe des comptes d'administration et de krbtgt.",
                    "eradication": "Nettoyage intégral des serveurs via un outil antivirus hors-ligne et suppression des comptes dormants.",
                    "reconstruction": "Reconstruction systématique à partir de gabarits d'infrastructure-as-code (IaC) durcis et approuvés."
                },
                "strategie_remediation": {
                    "urgence_redemarrage": "Ligne de production R&D à l'arrêt : impact direct sur les délais contractuels clients aéronautiques.",
                    "couts_risques_redemarrage": "Un redémarrage précipité sans éradication complète expose à une ré-infection et à la perte de la piste d'investigation.",
                    "decision_direction": "Direction Générale : priorité à l'éradication complète avant redémarrage, délai maximal accepté de 48 h."
                }
            },
            "traitement": {
                "remediations": [
                    {"id": "REM-01", "axe": "Gouvernance", "measure": "Faire approuver et diffuser la nouvelle PSSI par la direction générale.", "priority": "Élevé",
                     "responsable": "RSSI", "echeance": "2026-09-30", "statut": "En cours", "cout_estime": "Négligeable", "risque_lie": "SO-01"},
                    {"id": "REM-02", "axe": "Protection", "measure": "Déployer le MFA (Multi-Factor Authentication) sur tous les comptes d'accès distants.", "priority": "Critique",
                     "responsable": "DSI", "echeance": "2026-09-01", "statut": "En cours", "cout_estime": "Léger", "risque_lie": "SO-01"},
                    {"id": "REM-03", "axe": "Défense", "measure": "Déployer un outil de détection EDR moderne sur tous les serveurs et postes.", "priority": "Élevé",
                     "responsable": "DSI", "echeance": "2026-11-30", "statut": "À faire", "cout_estime": "Élevé", "risque_lie": "SO-01"},
                    {"id": "REM-04", "axe": "Résilience", "measure": "Mettre en œuvre des sauvegardes immuables résistantes aux ransomwares.", "priority": "Critique",
                     "responsable": "DSI", "echeance": "2026-09-15", "statut": "Fait", "cout_estime": "Moyen", "risque_lie": "SO-01"}
                ],
                "quick_wins": [
                    "Activer le MFA sur les messageries et VPN",
                    "Changer tous les mots de passe d'administration par défaut",
                    "Mettre en place des sauvegardes hors-ligne immuables",
                    "Sensibiliser l'ensemble des collaborateurs au Phishing",
                    "Déployer les correctifs de sécurité critiques (Patchs)",
                    "Restreindre les droits d'accès administratifs (Moindre privilège)"
                ]
            }
        }
    else:  # GRC
        ids = framework_ids or [framework_id]
        fw = get_framework_by_id(ids[0]) or {"name": "Referentiel", "requirements": []}
        manual_controls = []
        for fw_id in ids:
            referentiel = get_framework_by_id(fw_id) or {"name": fw_id, "requirements": []}
            manual_controls += [
                {
                    "id": req["id"],
                    "title": req["title"],
                    "description": req["description"],
                    "status": "A_VERIFIER",
                    "notes": "",
                    "referentiel_id": fw_id,
                    "referentiel_name": referentiel.get("name", fw_id),
                }
                for req in referentiel.get("requirements", [])
            ]
        state["steps"] = {
            "cadrage": {
                "scope": "Ensemble des serveurs de production critiques de la DSI.",
                "client_missions": "Garantir la conformité réglementaire et l'intégrité des opérations.",
                "nda_signed": False,
                "nda_text": nda_text,
                "assets_metier": [
                    {"id": "VM-01", "name": "Données d'évaluation d'audit", "description": "Preuves de conformité recueillies auprès des opérationnels.", "is_personal_data": True}
                ],
                "assets_support": [
                    {"id": "BS-01", "name": "Serveur API GREEN SHIELD", "type": "Logiciel", "description": "Contrôle continu local des politiques.", "owner": "RSSI"},
                    {"id": "BS-02", "name": "Fichiers de configurations cibles (/targets)", "type": "Logiciel", "description": "sshd_config et nginx.conf importés.", "owner": "Auditeur"}
                ],
                "framework_id": ids[0],
                "framework_name": fw.get("name", ids[0]),
                "framework_ids": ids,
            },
            "diagnostic": {
                "pssi_active": False,
                "governance_active": False,
                "vulnerabilities_active": False,
                "rgpd_register": [
                    {"id": "RGPD-01", "name": f"Audit de conformité {fw.get('name')}", "purpose": "Vérification des contrôles organisationnels.", "data_categories": "Résultats d'évaluation et rapports", "retention": "Durée du projet + 5 ans"}
                ],
                "aipd_required": False,
                "aipd": {
                    "treatment_description": "Traitement local des rapports d'audit de sécurité et notes d'évaluation.",
                    "necessity_eval": "Le traitement est indispensable pour répondre aux obligations légales d'audit.",
                    "risks_eval": "Risque négligeable sur les personnes concernées en raison du confinement 100% hors-ligne.",
                    "mitigation_measures": "Chiffrement AES du disque local et restrictions d'accès physique à la machine."
                },
                "violations": [],
            },
            "tprm": {
                # Volet GRC : pas de score de risque (§14.1bis). Les curseurs
                # restent saisis — ils décrivent le tiers — mais la conformité
                # se démontre par les exigences DORA, que la migration ajoute.
                "tiers": [
                    {"name": "Hébergeur Cloud (AWS)", "dependence": 4,
                     "penetration": 4, "maturity": 4, "trust": 4},
                ]
            },
            "ebios": {
                "redoute_events": [
                    {"id": "ER-01", "event": "Non-conformité réglementaire lors d'un contrôle CNIL/ANSSI", "gravity": 3, "impact": "Sanctions financières majeures (jusqu'à 4% du CA mondial) et arrêt de commercialisation."}
                ],
                "risk_sources": [
                    {"id": "SR-01", "name": "Autorité de contrôle / Régulateur", "objective": "Sanctions judiciaires ou amendes administratives."}
                ],
                "operational_scenarios": [
                    {"id": "SO-01", "event": "Contrôle CNIL inopiné révélant l'absence d'Analyse d'Impact (AIPD) pour un traitement à haut risque.", "gravity": 3, "likelihood": 2, "mitigation": "Réaliser l'AIPD de manière exhaustive via le module AIPD intégré.",
                     "actif_concerne": "Registre des traitements", "gravite_residuelle": 2, "vraisemblance_residuelle": 1,
                     "strategie_traitement": "Réduire", "owner": "DPO", "date_revue": "2026-10-01", "statut": "En traitement"}
                ],
                "case_studies": [
                    {"case": "Marriott (Fuite de données)", "lessons": "Amende historique de plus de 20M£ par l'ICO pour défaut de chiffrement et négligence d'audit de conformité."}
                ]
            },
            "resilience": {
                "logging_active": False,
                "bcp_strategy": {
                    "rto": "8 heures",
                    "rpo": "24 heures",
                    "backup_policy": "Sauvegarde chiffrée des rapports sur disque dur externe déconnecté."
                },
                "e3r": {
                    "endiguement": "Révocation immédiate des accès de l'auditeur compromis.",
                    "eviction": "Changement de tous les tokens et clés d'API locales.",
                    "eradication": "Mise à jour de sécurité des composants et purge des caches.",
                    "reconstruction": "Re-scaffolding de l'environnement d'audit local."
                },
                "strategie_remediation": {
                    "urgence_redemarrage": "",
                    "couts_risques_redemarrage": "",
                    "decision_direction": ""
                }
            },
            "evaluation": {
                "manual_controls": manual_controls,
                "technical_results": None,
                # SoA (93 contrôles) uniquement si ISO 27001 fait partie des
                # référentiels actifs — non statuée, au même titre qu'une
                # mission réelle (zéro invention).
                "soa": soa.entrees_par_defaut() if "iso27001" in ids else [],
            },
            "restitution": {
                "exec_summary": f"Audit de conformité par rapport au référentiel {fw.get('name')}.",
                "remediation_plan": []
            },
            "traitement": {
                "remediations": [
                    {"id": "REM-01", "axe": "Gouvernance", "measure": f"Valider formellement la conformité réglementaire aux exigences {fw.get('name')}.", "priority": "Élevé",
                     "responsable": "RSSI", "echeance": "2026-10-31", "statut": "À faire", "cout_estime": "Négligeable", "risque_lie": "SO-01"}
                ],
                "quick_wins": [
                    "Valider le périmètre d'audit",
                    "Réaliser le registre de traitement",
                    "Lancer le diagnostic d'hygiène",
                    "Vérifier le scan technique",
                    "Compléter la check-list GRC",
                    "Exporter le rapport d'audit"
                ]
            }
        }
    return state




# --- Jeu de démonstration (F16) ---------------------------------------------
# Démontrer l'outil en portfolio ou en entretien exigeait jusqu'ici d'ouvrir une
# mission réelle — un manquement à la confidentialité. Cette mission est
# entièrement fictive et porte un marqueur explicite.

DEMO_ID = "demo_green_shield"







# NOTE (31/07/2026) : `POST /projects/{p_id}/upload` vivait aussi ici et
# dans exports.py, en triple avec crud.py — supprimée ici, la version
# authentifiée vit uniquement dans `crud.py`.


def _phase_nouvellement_validee(state_file: Path, nouveau: dict) -> str | None:
    """Nom de la phase qui vient de passer à « validée », le cas échéant.

    Compare l'état sur disque à celui qu'on s'apprête à écrire : sans cette
    comparaison, chaque sauvegarde d'une mission déjà validée créerait un
    instantané inutile.
    """
    try:
        ancien = json.loads(state_file.read_text(encoding="utf-8")) if state_file.is_file() else {}
    except (OSError, json.JSONDecodeError):
        return None

    etapes_anciennes = ancien.get("steps", {}) or {}
    etapes_nouvelles = nouveau.get("steps", {}) or {}
    for phase in ("cadrage", "diagnostic", "tprm", "ebios", "resilience", "traitement"):
        avant = bool((etapes_anciennes.get(phase) or {}).get("validated"))
        apres = bool((etapes_nouvelles.get(phase) or {}).get("validated"))
        if apres and not avant:
            return phase
    return None


@router.get("/projects/{p_id}/snapshots")
def list_snapshots(p_id: str, current_user: User = Depends(get_current_user)) -> list[dict]:
    """Historique versionné d'une mission (F9)."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.is_dir():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return snapshots.lister(p_dir)


@router.post("/projects/{p_id}/snapshots/{nom}/restore")
def restore_snapshot(p_id: str, nom: str, current_user: User = Depends(get_current_user)) -> dict:
    """Restaure la mission à l'état d'un instantané.

    L'état courant est lui-même instantané avant écrasement : une restauration
    ne doit jamais être un aller sans retour.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    state_file = p_dir / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    # Le nom d'instantané vient du client : il compose un chemin disque.
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}_[A-Za-z0-9_-]{1,40}\.json", nom):
        audit_log.record("snapshot.restore", target=p_id, outcome="denied", detail=repr(nom)[:60])
        raise HTTPException(status_code=400, detail="Nom d'instantané invalide")

    try:
        restaure = snapshots.lire(p_dir, nom, dechiffrer=_dechiffrer)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Instantané illisible")

    try:
        courant = _read_state(state_file)
        snapshots.creer(p_dir, courant, "avant-restauration", chiffrer=_chiffrer)

        restaure = schema_migration.migrate(restaure)
        restaure["id"] = p_id
        restaure["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        restaure["progress"] = calculate_progress(restaure)
        _write_json_atomic(state_file, restaure)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    audit_log.record("snapshot.restore", target=p_id, detail=nom)
    return restaure



# --- Conservation des données personnelles (F17) -----------------------------
# Le consultant est responsable de traitement pour les noms, fonctions et
# déclarations des personnes interrogées. Ces routes lui donnent de quoi tenir
# ses propres obligations, celles-là mêmes qu'il audite chez ses clients.









def _tprm_tiers(state: dict) -> list[dict]:
    return state.setdefault("steps", {}).setdefault("tprm", {}).setdefault("tiers", [])












# --- Export / import d'une mission en archive chiffrée (F14, F15) -----------
# Le mot de passe transite dans le CORPS de la requête, jamais en paramètre
# d'URL : une URL finit dans les journaux d'accès et l'historique.



# NOTE (31/07/2026) : `POST /projects/import-archive` vivait aussi ici en
# double de `crud.py` (dupliqué une 3e fois dans exports.py) — trois
# définitions de la même route, dont deux mortes puisque `crud.router` est
# inclus en premier dans `router.py`. Supprimée ici ; la version authentifiée
# et à jour vit uniquement dans `crud.py`.









def _servir_rapport_html(p_id: str, nom: str, html: str, action_journal: str) -> Response:
    """Écrit et sert un export HTML — factorisé pour les 5 formats de restitution."""
    p_dir = PROJECTS_DIR / p_id
    reports = p_dir / "reports"
    reports.mkdir(exist_ok=True)
    (reports / nom).write_text(html, encoding="utf-8")
    audit_log.record(action_journal, target=p_id)
    return Response(
        content=html.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'inline; filename="{quote(nom)}"'},
    )






















def _est_un_referentiel(data) -> bool:
    """Le répertoire `frameworks/` ne contient pas que des référentiels.

    `mesures_catalogue.yaml` y vit aussi (clés `metadata`/`mesures`) : sans ce
    filtre il apparaissait dans la liste comme une entrée fantôme `id: null`,
    donc comme une option vide dans le sélecteur de référentiel à la création
    d'une mission GRC — et la choisir produisait une mission sans référentiel.
    """
    return isinstance(data, dict) and bool(data.get("id")) and bool(data.get("name"))






def _lire_state_pour_docx(p_id: str) -> tuple[str, dict]:
    """Validation + lecture communes aux cinq routes d'export Word."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    try:
        return p_id, _read_state(state_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lecture projet: {exc}")


def _servir_docx(p_id: str, filename: str, content: bytes, action_journal: str) -> Response:
    """Réponse HTTP `.docx` — factorisée pour les cinq formats de restitution."""
    # Les en-têtes HTTP ne transportent pas d'UTF-8 tel quel : un nom de client
    # accentué (« cassiopé ») arriverait mutilé. On fournit donc un repli ASCII
    # et la forme encodée RFC 5987, que les navigateurs privilégient.
    ascii_fallback = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode() or "rapport.docx"
    disposition = (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(filename, safe='')}"
    )
    audit_log.record(action_journal, target=p_id, detail="format=docx")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": disposition},
    )

















def _call_gemini_copilot(api_key: str, client: str, prompt: str) -> str | None:
    """Appelle l'API Gemini (via ai_gateway) avec le contexte de la mission.
    Retourne None en cas d'échec pour laisser l'appelant basculer silencieusement
    sur l'intelligence experte locale hors-ligne."""
    system_context = (
        "Tu es un consultant senior en cybersécurité et GRC (Gouvernance, Risques, "
        "Conformité), expert ISO 27001, NIS2, EBIOS RM et RGPD. Réponds de façon "
        f"factuelle, structurée en Markdown, pour la mission client « {client} »."
    )
    return ai_gateway.call_gemini(api_key, system_context, prompt)
