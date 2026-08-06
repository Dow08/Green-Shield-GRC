from __future__ import annotations
import os
import json
import logging
import re
import shutil
import unicodedata
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, Depends
import yaml
from ..database.session import get_db
from ..database.models import Project, User
from ..auth import get_current_user
from sqlalchemy.orm import Session
from ..schemas import (
    coerce,
    CreateProjectRequest, UpdateProjectRequest, UpdateRgpdRequest, AddTiersRequest,
    UpdateExigenceTiersRequest, AddTempsRequest, CopilotMissionRequest,
    AddDemandePreuveRequest, UpdateDemandePreuveRequest,
    ImportFrameworkRequest, DocxExportRequest,
)

def _resolve_test_deps(current_user, db):
    if hasattr(current_user, "dependency") or type(current_user).__name__ == "Depends":
        current_user = User(id=0, email="test@test.local", role="user", is_premium=False)
    if hasattr(db, "dependency") or type(db).__name__ == "Depends":
        from ..database.session import SessionLocal
        db = SessionLocal()
    return current_user, db

def _get_project_db_or_disk(p_id: str, db: Session | None = None) -> tuple[Project | None, dict | None]:
    """Résout une mission depuis la base ou le disque.

    Outil mono-poste (31/07/2026) : l'authentification protège l'accès à
    l'application dans son ensemble (un écran de connexion), pas mission par
    mission — une seule personne à la fois utilise une instance donnée.
    `owner_id` reste une métadonnée informative (qui a créé la mission),
    jamais un filtre d'accès : aucune mission n'est donc scopée par
    utilisateur ici.
    """
    p = None
    if db and hasattr(db, "query"):
        try:
            p = db.query(Project).filter(Project.id == p_id).first()
        except Exception:
            p = None

    p_dir = PROJECTS_DIR / p_id
    state_file = p_dir / "project.json"
    state = None
    if state_file.is_file():
        try:
            state = _read_state(state_file)
        except Exception:
            state = None

    if state:
        if "progress" not in state:
            state["progress"] = calculate_progress(state)
        return p, state

    if p:
        d = p.to_dict()
        if "progress" not in d:
            d["progress"] = p.progress if p.progress is not None else calculate_progress(d)
        return p, d

    return None, None

from .. import aipd
from .. import archive
from .. import auditcraft_grc
from .. import ai_gateway
from .. import demandes_preuves
from .. import nist_csf_map
from .. import controles_techniques
from .. import audit_log
from .. import demo_fixture
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
from .. import ids

router = APIRouter(prefix="/api")
_log = logging.getLogger("greenshield.projects.crud")

from . import PROJECTS_DIR, FRAMEWORKS_DIR, _write_json_atomic, _read_state, calculate_progress, get_framework_by_id, _rempli, _tprm_rate, _chiffrer, _dechiffrer

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

    Bug corrigé le 31/07/2026 : un correctif automatisé (`fix_crud.py`,
    resté à la racine du dépôt) avait renommé cette fonction en
    `create_empty_state`, entrant en collision avec la fonction homonyme
    (la vraie, celle qui rend un état vide) définie juste au-dessus — Python
    ne conservait que cette définition-ci, si bien que `create_project`
    livrait par erreur des missions réelles **pré-remplies de données
    fictives** (« Fichier Clients & Prospects », affaire Marriott, etc.),
    exactement la régression que F16 avait corrigée.
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

@router.get("/projects")
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Liste toutes les missions connues (base + disque).

    Outil mono-poste : pas de filtrage par `owner_id`, voir
    `_get_project_db_or_disk`.
    """
    current_user, db = _resolve_test_deps(current_user, db)
    db_projects = []
    if db and hasattr(db, "query"):
        try:
            db_projects = db.query(Project).all()
        except Exception:
            db_projects = []
    
    res = {p.id: p.to_dict() for p in db_projects}
    if PROJECTS_DIR.exists():
        for d in PROJECTS_DIR.iterdir():
            if d.is_dir() and (d / "project.json").is_file() and d.name not in res:
                try:
                    st = _read_state(d / "project.json")
                    res[d.name] = st
                except Exception:
                    pass
    return sorted(list(res.values()), key=lambda x: x.get("updated_at") or "", reverse=True)

def get_project_db(project_id: str, db: Session | None = None) -> dict | None:
    """Helper synchrone pour les connecteurs/autres modules."""
    close_after = False
    if db is None or type(db).__name__ == "Depends":
        from ..database.session import SessionLocal
        db = SessionLocal()
        close_after = True
    try:
        p, state = _get_project_db_or_disk(project_id, db)
        return state
    finally:
        if close_after:
            try:
                db.close()
            except Exception:
                pass

def update_project_db(project_id: str, state: dict, db: Session | None = None):
    """Helper synchrone pour la sauvegarde depuis d'autres modules."""
    p_dir = PROJECTS_DIR / project_id
    p_dir.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(p_dir / "project.json", state)
    
    close_after = False
    if db is None or type(db).__name__ == "Depends":
        from ..database.session import SessionLocal
        db = SessionLocal()
        close_after = True
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if p:
            p.steps = state.get("steps", {})
            p.grc = state.get("grc", {})
            p.technical_findings = state.get("technical_findings", {})
            p.socle = state.get("socle", {})
            p.progress = calculate_progress(state)
            p.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            db.commit()
    except Exception:
        db.rollback()
    finally:
        if close_after:
            try:
                db.close()
            except Exception:
                pass

@router.post("/projects")
def create_project(data: CreateProjectRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    current_user, db = _resolve_test_deps(current_user, db)
    data = coerce(CreateProjectRequest, data)
    name = data.name
    client = data.client
    project_type = data.type
    framework_ids = data.framework_ids or [data.framework_id]
    framework_id = framework_ids[0]
        
    project_id = "".join(c for c in name.lower().replace(" ", "_") if c.isalnum() or c == "_")
    if not project_id:
         project_id = f"project_{int(datetime.now().timestamp())}"
         
    if db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=400, detail="Un projet avec ce nom existe déjà")
        
    state = create_empty_state(project_id, name, client, project_type, framework_id, framework_ids)
    state = schema_migration.migrate(state)
    
    # DB Insert
    p = Project(
        id=project_id,
        owner_id=current_user.id,
        name=name,
        client=client,
        type=project_type,
        status="en_cours",
        progress=0,
        created_at=state["created_at"],
        updated_at=state["updated_at"],
        steps=state.get("steps", {}),
        grc=state.get("grc", {}),
        technical_findings=state.get("technical_findings", {})
    )
    db.add(p)
    db.commit()
    
    # Conservation fichiers locaux temporaire
    p_dir = PROJECTS_DIR / project_id
    p_dir.mkdir(parents=True, exist_ok=True)
    (p_dir / "targets").mkdir(exist_ok=True)
    (p_dir / "reports").mkdir(exist_ok=True)
    _write_json_atomic(p_dir / "project.json", state)
    
    audit_log.record("project.create", target=project_id, detail=f"type={project_type}")
    return state


# --- Jeu de démonstration (F16) ---------------------------------------------
# Démontrer l'outil en portfolio ou en entretien exigeait jusqu'ici d'ouvrir une
# mission réelle — un manquement à la confidentialité. Cette mission est
# entièrement fictive et porte un marqueur explicite.

DEMO_ID = "demo_green_shield"


@router.post("/projects/demo")
def create_demo_project(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Crée (ou recrée) la mission de démonstration fictive."""
    current_user, db = _resolve_test_deps(current_user, db)
    p_dir = PROJECTS_DIR / DEMO_ID
    if p_dir.exists():
        shutil.rmtree(p_dir)
    (p_dir / "targets").mkdir(parents=True)
    (p_dir / "reports").mkdir()

    # Recette du 31/07/2026 : la démo était trop pauvre pour servir de vitrine
    # (chapitre RGPD absent car `aipd_required` à False, SoA à 0/93, aucune
    # preuve ni violation). Elle est désormais construite par un module dédié
    # qui traverse chaque fonctionnalité livrée — `demo_fixture.construire`.
    state = demo_fixture.construire(DEMO_ID)
    state = schema_migration.migrate(state)

    # Configuration volontairement vulnérable, pour que le scan technique ait
    # quelque chose à trouver pendant une démonstration.
    (p_dir / "targets" / "sshd_config").write_text(
        "\n".join([
            "# Configuration FICTIVE de démonstration — aucun système réel",
            "Port 22",
            "PermitRootLogin yes",
            "PasswordAuthentication yes",
            "PermitEmptyPasswords no",
            "X11Forwarding yes",
            "",
        ]),
        encoding="utf-8",
    )
    state.setdefault("steps", {}).setdefault("collecte", {})["files"] = ["sshd_config"]
    state["progress"] = calculate_progress(state)
    _write_json_atomic(p_dir / "project.json", state)
    
    # Save to SQLite
    existing_p = db.query(Project).filter(Project.id == DEMO_ID).first()
    if existing_p:
        db.delete(existing_p)
        db.commit()
        
    p = Project(
        id=DEMO_ID,
        owner_id=current_user.id,
        name=state["name"],
        client=state["client"],
        type=state["type"],
        status=state["status"],
        progress=state["progress"],
        created_at=state["created_at"],
        updated_at=state["updated_at"],
        steps=state.get("steps", {}),
        grc=state.get("grc", {}),
        technical_findings=state.get("technical_findings", {})
    )
    db.add(p)
    db.commit()

    audit_log.record("project.demo_create", target=DEMO_ID)
    return state



@router.get("/projects/{p_id}")
def get_project(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    current_user, db = _resolve_test_deps(current_user, db)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable ou accès refusé")
    return state

@router.put("/projects/{p_id}")
def update_project(p_id: str, state: UpdateProjectRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    state = coerce(UpdateProjectRequest, state).model_dump()
    current_user, db = _resolve_test_deps(current_user, db)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p, old_state = _get_project_db_or_disk(p_id, db)
    if not old_state:
        raise HTTPException(status_code=404, detail="Projet introuvable ou accès refusé")
    if state["id"] != p_id:
        raise HTTPException(status_code=400, detail="L'identifiant de la mission dans le corps ne correspond pas à celui de l'URL")

    p_dir = PROJECTS_DIR / p_id
    p_dir.mkdir(parents=True, exist_ok=True)
    
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    
    if (p_dir / "project.json").is_file():
        phase_validee = _phase_nouvellement_validee(p_dir / "project.json", state)
        if phase_validee:
            snapshots.creer(p_dir, state, f"phase-{phase_validee}-validee", chiffrer=_chiffrer)
            
    _write_json_atomic(p_dir / "project.json", state)
    
    if p and db:
        p.steps = state.get("steps", {})
        p.grc = state.get("grc", {})
        p.technical_findings = state.get("technical_findings", {})
        p.socle = state.get("socle", {})
        p.progress = state["progress"]
        p.updated_at = state["updated_at"]
        db.commit()
        
    audit_log.record("project.update", target=p_id, detail=f"progress={state['progress']}%")
    return state

@router.delete("/projects/{p_id}")
def delete_project(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    current_user, db = _resolve_test_deps(current_user, db)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p, state = _get_project_db_or_disk(p_id, db)
    if not state and not p:
        raise HTTPException(status_code=404, detail="Projet introuvable ou accès refusé")
        
    if p and db:
        try:
            db.delete(p)
            db.commit()
        except Exception:
            db.rollback()
            
    p_dir = PROJECTS_DIR / p_id
    if p_dir.exists():
        shutil.rmtree(p_dir)
        
    audit_log.record("project.delete", target=p_id)
    return {"status": "ok", "message": "Projet supprimé avec succès"}

@router.post("/projects/{p_id}/upload")
async def upload_file(p_id: str, file: UploadFile = File(...),
                       current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    current_user, db = _resolve_test_deps(current_user, db)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    safe_filename = path_safety.safe_filename(file.filename)
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    target_path = p_dir / "targets" / safe_filename
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    # we populate both step levels for compatibility
    files_list = state.setdefault("steps", {}).setdefault("collecte", {}).setdefault("files", [])
    if safe_filename not in files_list:
        files_list.append(safe_filename)
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)
    audit_log.record("project.upload", target=p_id, detail=f"file={safe_filename}")
    return state

@router.post("/projects/{p_id}/audit")
def run_project_audit(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    current_user, db = _resolve_test_deps(current_user, db)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    targets_dir = p_dir / "targets"
    result = auditcraft_grc.run(str(targets_dir))

    state.setdefault("steps", {}).setdefault("evaluation", {})["technical_results"] = result
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)
    audit_log.record("project.scan", target=p_id, detail=f"score={result.get('score')}")
    return state

@router.get("/projects/{p_id}/preuves/suggestions")
def get_preuves_suggestions(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Suggestions de réutilisation croisée de preuves (Lot F)."""
    current_user, db = _resolve_test_deps(current_user, db)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    from . import preuves as preuves_module
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return preuves_module.suggestions_reutilisation(state)

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







# --- Conservation des données personnelles (F17) -----------------------------
# Le consultant est responsable de traitement pour les noms, fonctions et
# déclarations des personnes interrogées. Ces routes lui donnent de quoi tenir
# ses propres obligations, celles-là mêmes qu'il audite chez ses clients.

@router.get("/rgpd/echeances")
def list_echeances_rgpd(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Situation de conservation de toutes les missions, échues en tête."""
    resultat = []
    for state in list_projects():
        ech = retention.echeance(state)
        resultat.append({
            "project_id": state.get("id"),
            "project_name": state.get("name"),
            "client": state.get("client"),
            "donnees_personnelles": retention.compter_donnees_personnelles(state),
            **ech,
        })
    ordre = {"echue": 0, "en_conservation": 1, "mission_en_cours": 2, "date_invalide": 3, "purgee": 4}
    resultat.sort(key=lambda r: (ordre.get(r["statut"], 9), r.get("jours_restants") or 0))
    return resultat


@router.put("/projects/{p_id}/rgpd")
def update_politique_rgpd(p_id: str, data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Fixe la durée de conservation et la date de fin de mission."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
        
    duree = data.get("duree_conservation_mois")
    fin = data.get("date_fin_mission")
    
    if duree is not None:
        if not isinstance(duree, int) or duree <= 0 or duree > 120:
            raise HTTPException(status_code=400, detail="Durée de conservation invalide")
    if fin is not None and fin != "":
        try:
            date.fromisoformat(fin)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Format de date de fin invalide")

    rgpd = state.setdefault("socle", {}).setdefault("rgpd_consultant", {})
    if duree is not None:
        rgpd["duree_conservation_mois"] = duree
    if fin is not None:
        rgpd["date_fin_mission"] = fin
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)

    audit_log.record("rgpd.politique", target=p_id, detail=f"duree={duree}mois fin={fin or 'non definie'}")
    return state


@router.post("/projects/{p_id}/rgpd/purge")
def purge_donnees_personnelles(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Efface les données personnelles d'une mission.

    Irréversible : un instantané est donc pris juste avant, pour que le
    consultant garde une porte de sortie s'il purge par erreur.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    p_dir = PROJECTS_DIR / p_id
    p_dir.mkdir(parents=True, exist_ok=True)
    snapshots.creer(p_dir, state, "avant-purge-rgpd", chiffrer=_chiffrer)
    state, efface = retention.purger(state)
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)

    audit_log.record("rgpd.purge", target=p_id, detail=f"enregistrements={efface}")
    return {"status": "ok", "efface": efface, "state": state}


@router.get("/projects/{p_id}/tprm")
def get_tprm_synthese(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Synthèse TPRM adaptée au volet de la mission (§14.1bis).

    Consulting : classement par ratio ANSSI, plus la liste des tiers encore
    notés à l'ancienne méthode (le recalcul est proposé, jamais imposé).
    GRC : avancement des exigences DORA/NIS2, sans aucun score de risque.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    tiers = ((state.get("steps") or {}).get("tprm") or {}).get("tiers") or []

    if state.get("type") == "grc":
        details = [{"name": t.get("name", ""), **tprm.conformite(t)} for t in tiers]
        return {
            "volet": "grc", "methode": "exigences", "tiers": details,
            "conformes": sum(1 for d in details if d["conforme"]), "total": len(details),
        }

    classement = sorted(tiers, key=lambda t: t.get("score", 0), reverse=True)
    return {
        "volet": "consulting", "methode": tprm.METHODE_ANSSI,
        "tiers": [{"name": t.get("name", ""), "score": t.get("score", 0),
                   "rating": t.get("rating", ""), "methode": t.get("methode", "")}
                  for t in classement],
        "a_recalculer": tprm.tiers_a_recalculer(state),
    }


def _tprm_tiers(state: dict) -> list[dict]:
    return state.setdefault("steps", {}).setdefault("tprm", {}).setdefault("tiers", [])


@router.post("/projects/{p_id}/tprm/tiers")
def add_tprm_tier(p_id: str, data: AddTiersRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Ajoute un tiers — **le serveur seul le note**.

    Le frontend calculait auparavant le score de son côté, avec sa propre copie
    de la formule : deux vérités pour une même opération de domaine, qui
    divergent dès que l'une des deux évolue (c'est exactement ce qui est arrivé
    au passage au ratio ANSSI). Il n'envoie donc plus que les curseurs.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    data = coerce(AddTiersRequest, data)
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    criteres = {"dependence": data.dependence, "penetration": data.penetration,
                "maturity": data.maturity, "trust": data.trust}
    tier = {"name": data.name, **criteres}
    # Volet GRC : une check-list de conformité, jamais un score (§14.1bis).
    if state.get("type") == "grc":
        tier["exigences"] = tprm.exigences_par_defaut()
    else:
        tier.update(tprm.ratio_anssi(**criteres))

    _tprm_tiers(state).append(tier)
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)
    return state


@router.put("/projects/{p_id}/tprm/tiers/{index}/exigences/{exigence_id}")
def update_tprm_exigence(p_id: str, index: int, exigence_id: str, data: UpdateExigenceTiersRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Coche (ou décoche) une exigence de conformité d'un tiers, volet GRC."""
    data = coerce(UpdateExigenceTiersRequest, data)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    tiers = _tprm_tiers(state)
    if not 0 <= index < len(tiers):
        raise HTTPException(status_code=404, detail="Tiers introuvable")

    exigences = tiers[index].setdefault("exigences", tprm.exigences_par_defaut())
    cible = next((e for e in exigences if e.get("id") == exigence_id), None)
    if cible is None:
        raise HTTPException(status_code=404, detail="Exigence introuvable")

    cible["satisfait"] = data.satisfait
    cible["preuve"] = data.preuve or cible.get("preuve", "")
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_project_db(p_id, state, db)
    return state


@router.post("/projects/{p_id}/tprm/recalculer")
def recalculer_tprm(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Repasse les tiers au ratio ANSSI — action explicite du consultant.

    Un instantané précède le recalcul : les criticités changent de valeur, et
    elles ont pu être présentées au client sous l'ancienne méthode.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p_dir = PROJECTS_DIR / p_id
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    snapshots.creer(p_dir, state, "avant-recalcul-tprm", chiffrer=_chiffrer)
    state, recalcules = tprm.recalculer_mission(state)
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)

    audit_log.record("tprm.recalcul", target=p_id, detail=f"tiers={recalcules}")
    return {"status": "ok", "recalcules": recalcules, "state": state}


@router.get("/projects/{p_id}/couverture")
def get_couverture_technique(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Part des contrôles appuyés par une preuve technique (F10)."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    resultat = couverture.couverture_technique(state)
    return {**resultat, "phrase": couverture.phrase(resultat)}


@router.get("/projects/{p_id}/revue")
def get_revue_export(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Complétude de la mission avant génération d'un livrable.

    En lecture seule : signale ce qui manque, ne remplit rien.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return revue_export.revue(state)


# --- Export / import d'une mission en archive chiffrée (F14, F15) -----------
# Le mot de passe transite dans le CORPS de la requête, jamais en paramètre
# d'URL : une URL finit dans les journaux d'accès et l'historique.



@router.post("/projects/import-archive")
async def import_project_archive(
    file: UploadFile = File(...),
    password: str = Form(""),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Restaure une mission depuis une archive chiffrée.

    L'archive est une entrée non fiable : `archive.lire_archive` valide la
    structure, plafonne la décompression et refuse toute traversée de chemin.
    """
    donnees = await file.read()
    try:
        state, fichiers = archive.lire_archive(donnees, password)
    except archive.ArchiveInvalide as exc:
        audit_log.record("project.archive_import", outcome="denied", detail=str(exc)[:80])
        raise HTTPException(status_code=400, detail=str(exc))

    # L'identifiant vient de l'archive mais reste une donnée non fiable.
    p_id = path_safety.safe_path_component(
        str(state.get("id") or "").strip() or "mission_importee", "identifiant de mission"
    )
    if (PROJECTS_DIR / p_id).exists():
        raise HTTPException(
            status_code=409,
            detail=f"Une mission « {p_id} » existe déjà. Renommez ou supprimez-la avant d'importer.",
        )

    p_dir = PROJECTS_DIR / p_id
    try:
        archive.ecrire_fichiers(fichiers, p_dir, chiffrer=_chiffrer)
        for sous in archive.SOUS_DOSSIERS:
            (p_dir / sous).mkdir(parents=True, exist_ok=True)
        # Une mission importée peut venir d'une version antérieure du schéma :
        # elle traverse la même chaîne de migration que n'importe quelle lecture.
        state = schema_migration.migrate(state)
        state["id"] = p_id
        state["progress"] = calculate_progress(state)
        _write_json_atomic(p_dir / "project.json", state)
    except archive.ArchiveInvalide as exc:
        shutil.rmtree(p_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        shutil.rmtree(p_dir, ignore_errors=True)
        _log.exception("Échec de l'import d'archive (mission=%s)", p_id)
        raise HTTPException(status_code=500, detail="Import impossible : échec d'écriture sur disque.")

    audit_log.record("project.archive_import", target=p_id, detail=f"fichiers={len(fichiers)}")
    return state


# --- Suivi du temps consommé (F19) ------------------------------------------
# Phases reconnues : les 6 étapes méthodologiques + un fourre-tout explicite
# pour ce qui ne relève d'aucune (déplacements, coordination, rédaction).
PHASES_TEMPS = ("cadrage", "diagnostic", "tprm", "ebios", "resilience", "traitement", "autre")




@router.post("/projects/{p_id}/temps")
def add_temps_entry(p_id: str, data: AddTempsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Ajoute une entrée de temps consommé sur une mission."""
    data = coerce(AddTempsRequest, data)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    temps = state.setdefault("socle", {}).setdefault("temps", {"entrees": []})
    entrees = temps.setdefault("entrees", [])
    entree = {
        "id": ids.next_id("T", entrees),
        "phase": data.phase,
        "minutes": data.minutes,
        "date": data.date or date.today().isoformat(),
        "note": (data.note or "")[:200],
    }
    entrees.append(entree)
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)
    audit_log.record("temps.add", target=p_id, detail=f"{entree['id']} phase={data.phase} minutes={data.minutes}")
    return state


@router.delete("/projects/{p_id}/temps/{entry_id}")
def delete_temps_entry(p_id: str, entry_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Supprime une entrée de temps (saisie erronée)."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    entry_id = path_safety.safe_path_component(entry_id, "identifiant d'entrée de temps")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    temps = state.setdefault("socle", {}).setdefault("temps", {"entrees": []})
    entrees = temps.setdefault("entrees", [])
    restantes = [e for e in entrees if e.get("id") != entry_id]
    if len(restantes) == len(entrees):
        raise HTTPException(status_code=404, detail="Entrée de temps introuvable")
    temps["entrees"] = restantes
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    update_project_db(p_id, state, db)
    audit_log.record("temps.delete", target=p_id, detail=entry_id)
    return state




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










@router.get("/controles-techniques")
def list_controles_techniques(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Rattachement des pratiques aux contrôles CIS / NIST CSF (§14.2.4)."""
    return controles_techniques.referentiel()


@router.get("/projects/{p_id}/controles-techniques")
def get_controles_techniques(p_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """État des pratiques rattachées, pour une mission (§14.2.4).

    Bug corrigé le 31/07/2026 : le corps de cette fonction avait été
    remplacé par une copie collée du corps de `run_project_copilot` (plus
    bas dans ce fichier, où il a sa place légitime) — ce doublon référençait
    `data`, jamais défini ici, garantissant un `NameError` à chaque appel.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return controles_techniques.etat(state)


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

def _est_un_referentiel(data: dict) -> bool:
    return "id" in data and "name" in data and "requirements" in data

@router.get("/frameworks")
def list_frameworks(current_user: User = Depends(get_current_user)) -> list[dict]:
    fws = []
    for path in FRAMEWORKS_DIR.glob("*.yaml"):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if _est_un_referentiel(data):
                fws.append({
                    "id": data["id"],
                    "name": data["name"],
                    "description": data.get("description"),
                    "requirements_count": len(data.get("requirements") or []),
                    "is_custom": False,
                })
        except Exception:
            pass
    custom_dir = FRAMEWORKS_DIR / "custom"
    if custom_dir.exists():
        for path in custom_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if _est_un_referentiel(data):
                    fws.append({
                        "id": data["id"],
                        "name": f"[Perso] {data['name']}",
                        "description": data.get("description"),
                        "requirements_count": len(data.get("requirements") or []),
                        "is_custom": True,
                    })
            except Exception:
                pass
    return fws

@router.get("/frameworks/{fw_id}/detail")
def get_framework_detail(fw_id: str, current_user: User = Depends(get_current_user)) -> dict:
    fw_id = path_safety.safe_path_component(fw_id, "identifiant de référentiel")
    data = get_framework_by_id(fw_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Référentiel introuvable")
    return {**data, "personnel": not (FRAMEWORKS_DIR / f"{fw_id}.yaml").is_file()}

@router.get("/frameworks/{fw_id}/workflow")
def get_framework_workflow(fw_id: str, current_user: User = Depends(get_current_user)) -> dict:
    try:
        return workflow_loader.load_workflow(fw_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        # Le message inclut le chemin disque du fichier de workflow : ne
        # jamais le renvoyer tel quel au client.
        _log.error("Workflow invalide (référentiel=%s) : %s", fw_id, exc)
        raise HTTPException(status_code=500, detail=f"Workflow invalide pour le référentiel « {fw_id} ».")

@router.post("/frameworks/import")
def import_framework(data: ImportFrameworkRequest, current_user: User = Depends(get_current_user)) -> dict:
    data = coerce(ImportFrameworkRequest, data)
    fw_id = path_safety.safe_path_component(data.id, "identifiant de référentiel")

    if (FRAMEWORKS_DIR / f"{fw_id}.yaml").is_file():
        raise HTTPException(
            status_code=409,
            detail=f"« {fw_id} » est un référentiel livré avec l'application. Choisissez un autre identifiant pour votre référentiel personnel.",
        )

    fw_data = {
        "id": fw_id,
        "name": data.name,
        "description": data.description,
        "requirements": [r.model_dump() for r in data.requirements],
    }
    
    custom_dir = FRAMEWORKS_DIR / "custom"
    custom_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = custom_dir / f"{fw_id}.yaml"
    
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(fw_data, f, allow_unicode=True, sort_keys=False)
        
    audit_log.record("framework.import", target=fw_id, detail="import")
    return {"status": "ok"}

@router.post("/projects/{p_id}/copilot")
def run_project_copilot(p_id: str, data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    
    prompt = data.get("prompt", "")
    client = state.get("client", "Client")
    api_key = (data.get("key") or "").strip()
    
    technical_findings = state.get("technical_findings")
    augmented_prompt = prompt
    if technical_findings:
        augmented_prompt += f"\n\n[CONTEXTE TECHNIQUE RED SHIELD]\nVoici les constats techniques réels remontés de l'infrastructure : {technical_findings}\nPrends en compte ces éléments pour tes recommandations GRC."

    if api_key:
        online_text = _call_gemini_copilot(api_key, client, augmented_prompt)
        if online_text is not None:
            audit_log.record("copilot.mission", target=p_id, detail="source=online")
            return {"status": "success", "response": online_text, "source": "online"}

    offline_replies = {
        "ebios": f"### [Copilote AI] Recommandations EBIOS RM pour {client} ...",
        "pssi": f"### [Copilote AI] Recommandations d'Amélioration PSSI pour {client} ...",
        "resilience": f"### [Copilote AI] Stratégie de Résilience & Continuité (RTO/RPO) ...",
        "default": f"### [Copilote AI] Analyse d'Expert Cyber pour {client} ..."
    }
    
    response_text = ""
    prompt_lower = prompt.lower()
    if "ebios" in prompt_lower or "risque" in prompt_lower:
        response_text = offline_replies["ebios"]
    elif "pssi" in prompt_lower or "politique" in prompt_lower:
        response_text = offline_replies["pssi"]
    elif "resilience" in prompt_lower or "pri" in prompt_lower or "sauvegarde" in prompt_lower:
        response_text = offline_replies["resilience"]
    else:
        response_text = offline_replies["default"]
        
    source = "offline_fallback" if api_key else "offline"
    audit_log.record("copilot.mission", target=p_id, detail=f"source={source}")
    return {
        "status": "success",
        "response": response_text,
        "source": source
    }

# --- Registre des demandes de preuves ---------------------------------------
# Suivi des documents réclamés au client. Vit dans le socle : c'est un fait de
# conduite de mission, pas un constat d'audit (cf. demandes_preuves.py).

@router.get("/projects/{p_id}/demandes-preuves")
def get_demandes_preuves(p_id: str, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> dict:
    """Registre et sa synthèse, plus les contrôles conformes sans justificatif."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return {
        "demandes": demandes_preuves.liste(state),
        "synthese": demandes_preuves.synthese(state),
        "controles_sans_justificatif": demandes_preuves.controles_sans_preuve_ni_demande(state),
    }


@router.post("/projects/{p_id}/demandes-preuves")
def add_demande_preuve(p_id: str, data: AddDemandePreuveRequest,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> dict:
    """Enregistre un document réclamé au client."""
    data = coerce(AddDemandePreuveRequest, data)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    registre = state.setdefault("socle", {}).setdefault("demandes_preuves", [])
    demande = {
        "id": ids.next_id("DEM", registre),
        "libelle": data.libelle.strip(),
        "destinataire": (data.destinataire or "").strip(),
        "statut": "demandee",
        "date_demande": data.date_demande or date.today().isoformat(),
        "date_relance": "",
        "date_reponse": "",
        "echeance": data.echeance or "",
        "note": (data.note or "").strip(),
        "controles_lies": data.controles_lies or [],
        "preuve_id": "",
    }
    registre.append(demande)
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_project_db(p_id, state, db)
    # Le libellé peut nommer un document interne du client : on ne journalise
    # que l'identifiant, comme pour les autres écritures de mission.
    audit_log.record("demande_preuve.add", target=p_id, detail=demande["id"])
    return state


@router.patch("/projects/{p_id}/demandes-preuves/{demande_id}")
def update_demande_preuve(p_id: str, demande_id: str, data: UpdateDemandePreuveRequest,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> dict:
    """Fait évoluer une demande : relance, réception ou refus du client."""
    data = coerce(UpdateDemandePreuveRequest, data)
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    registre = (state.get("socle") or {}).get("demandes_preuves") or []
    demande = next((d for d in registre if d.get("id") == demande_id), None)
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")

    aujourdhui = date.today().isoformat()
    demande["statut"] = data.statut
    # Chaque transition horodate son propre champ : la date de relance sert à
    # recompter le délai d'attente, celle de réponse à clore le suivi.
    if data.statut == "relancee":
        demande["date_relance"] = aujourdhui
    elif data.statut in ("recue", "refusee"):
        demande["date_reponse"] = aujourdhui
    if data.note is not None:
        demande["note"] = data.note.strip()
    if data.preuve_id is not None:
        demande["preuve_id"] = data.preuve_id

    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_project_db(p_id, state, db)
    audit_log.record("demande_preuve.update", target=p_id,
                     detail=f"{demande_id} statut={data.statut}")
    return state


@router.delete("/projects/{p_id}/demandes-preuves/{demande_id}")
def delete_demande_preuve(p_id: str, demande_id: str,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> dict:
    """Supprime une demande saisie par erreur."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    registre = (state.get("socle") or {}).get("demandes_preuves") or []
    restant = [d for d in registre if d.get("id") != demande_id]
    if len(restant) == len(registre):
        raise HTTPException(status_code=404, detail="Demande introuvable")
    state["socle"]["demandes_preuves"] = restant
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_project_db(p_id, state, db)
    audit_log.record("demande_preuve.delete", target=p_id, detail=demande_id)
    return state

@router.get("/projects/{p_id}/nist-csf")
def get_nist_csf(p_id: str, current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> dict:
    """Roue NIST CSF de la mission : rattachement des contrôles aux 6 fonctions.

    Rattachement direct si la mission évalue NIST, indicatif (via le catalogue
    de mesures) sinon — cf. nist_csf_map.py.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    current_user, db = _resolve_test_deps(current_user, db)
    p, state = _get_project_db_or_disk(p_id, db)
    if not state:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return nist_csf_map.carte(state)

