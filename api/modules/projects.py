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
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
import yaml
from . import archive
from . import auditcraft_grc
from . import ai_gateway
from . import audit_log
from . import couverture
from . import data_paths
from . import docx_export
from . import schema_migration
from . import workflow_loader
from . import mesures_catalogue
from . import path_safety
from . import report_builder
from . import retention
from . import revue_export
from . import snapshots

router = APIRouter(prefix="/api")

# --- Emplacement des données ------------------------------------------------
# Résolution centralisée dans data_paths.py (partagée avec le journal d'audit).
PROJECTS_DIR = data_paths.resolve_projects_dir()
# Les référentiels sont du code applicatif livré avec l'app : chemin relatif au module.
FRAMEWORKS_DIR = Path(__file__).resolve().parent.parent / "frameworks"
# Ancien emplacement (dans le dépôt) : source d'une migration unique.
_LEGACY_PROJECTS_DIR = Path(__file__).resolve().parent.parent.parent / "projects"


def _write_json_atomic(path: Path, data: dict) -> None:
    """Écrit un JSON sans risque de corruption : fichier temporaire puis remplacement.

    os.replace est atomique sous Windows comme sous POSIX : si l'écriture est
    interrompue, l'ancien fichier reste intact au lieu d'être laissé tronqué.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _read_state(path: Path) -> dict:
    """Lit une mission et l'amène au schéma courant.

    Point de passage unique pour toute lecture de project.json : une mission
    créée avant le jalon 1 ne doit jamais atteindre le reste du code sans être
    passée par la chaîne de migration (cf. docs/audit-critique-plan.md, F4).
    La migration n'est PAS réécrite sur disque ici — c'est la prochaine sauvegarde
    (explicite, via update_project) qui la persistera, pour ne jamais modifier
    un fichier client en dehors d'une action volontaire de l'utilisateur.
    """
    state = json.loads(path.read_text(encoding="utf-8"))
    return schema_migration.migrate(state)


def _migrate_legacy_projects() -> None:
    """Recopie une seule fois les missions de l'ancien emplacement (dans le dépôt)
    vers le nouveau.

    Non destructif : l'ancien dossier est laissé en place, à supprimer manuellement
    une fois la migration vérifiée. Une mission déjà présente n'est jamais écrasée.

    Le marqueur est indispensable : cette fonction s'exécute à *chaque import* du
    module. Sans lui, pointer `GREENSHIELD_DATA_DIR` vers un répertoire de test ou
    de démonstration y recopiait silencieusement les missions clientes réelles, à
    chaque démarrage (constaté le 29/07/2026).
    """
    if not _LEGACY_PROJECTS_DIR.is_dir() or _LEGACY_PROJECTS_DIR == PROJECTS_DIR:
        return

    marqueur = PROJECTS_DIR / ".legacy-migre"
    if marqueur.exists():
        return

    for legacy in _LEGACY_PROJECTS_DIR.iterdir():
        if not (legacy / "project.json").is_file():
            continue
        target = PROJECTS_DIR / legacy.name
        if target.exists():
            continue
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(legacy, target)
        audit_log.record("legacy.migrate", target=legacy.name)
        print(f"[GREEN SHIELD] Mission migrée hors du dépôt : {legacy.name} -> {target}")

    try:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        marqueur.write_text(
            "Migration depuis l'ancien emplacement effectuée. "
            "Supprimer ce fichier force une nouvelle tentative.\n",
            encoding="utf-8",
        )
    except OSError:
        # Répertoire non inscriptible : on retentera au prochain démarrage
        # plutôt que d'empêcher l'application de se lancer.
        pass


PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
_migrate_legacy_projects()

def _tprm_rate(dependence: int, penetration: int, maturity: int, trust: int) -> dict:
    """Criticité d'un tiers, dérivée de ses 4 critères — jamais écrite à la main.

    Miroir exact du calcul appliqué côté frontend (web/src/pages/Projects.tsx) :
    les valeurs pré-remplies qui étaient saisies en dur divergeaient de ce que
    l'application calculait réellement, et la note changeait donc sous les yeux
    du client à la première réédition du tiers.

    L'arrondi reproduit `Number.toFixed(1)` de JavaScript (moitié vers le haut),
    et non l'arrondi au pair de Python, sans quoi 2.25 donnerait 2.2 ici et 2.3
    dans le navigateur.

    NOTE : cette formule (moyenne) migrera vers le ratio ANSSI
    (dépendance × pénétration) / (maturité × confiance) au Jalon 2, avec le
    radar des parties prenantes — cf. docs/spec-refonte-grc-consulting.md §14.1bis.
    """
    raw = (dependence + penetration + (6 - maturity) + (6 - trust)) / 4
    score = float(Decimal(str(raw)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    if score >= 4.0:
        rating = "Critique"
    elif score >= 3.0:
        rating = "Élevé"
    elif score >= 2.0:
        rating = "Moyen"
    else:
        rating = "Faible"
    return {
        "dependence": dependence, "penetration": penetration,
        "maturity": maturity, "trust": trust,
        "score": score, "rating": rating,
    }


def get_framework_by_id(fw_id: str) -> dict | None:
    fw_path = FRAMEWORKS_DIR / f"{fw_id}.yaml"
    if not fw_path.exists():
        fw_path = FRAMEWORKS_DIR / "custom" / f"{fw_id}.yaml"
        if not fw_path.exists():
            return None
    try:
        return yaml.safe_load(fw_path.read_text(encoding="utf-8"))
    except Exception:
        return None

def calculate_progress(state: dict) -> int:
    steps = state.get("steps", {})
    score = 0
    
    # 6 Steps overall progress contribution
    # Step 1: Cadrage & Patrimoine (max 15%)
    if steps.get("cadrage", {}).get("nda_signed"): score += 5
    if len(steps.get("cadrage", {}).get("assets_metier", [])) > 0: score += 5
    if len(steps.get("cadrage", {}).get("assets_support", [])) > 0: score += 5
    
    # Step 2: Diagnostic & RGPD (max 15%)
    if steps.get("diagnostic", {}).get("pssi_active"): score += 5
    if len(steps.get("diagnostic", {}).get("rgpd_register", [])) > 0: score += 5
    if steps.get("diagnostic", {}).get("aipd_required") is not None: score += 5
    
    # Step 3: TPRM (max 15%)
    if len(steps.get("tprm", {}).get("tiers", [])) > 0: score += 15
    else: score += 5 # base participation
    
    # Step 4: EBIOS RM (max 20%)
    if len(steps.get("ebios", {}).get("redoute_events", [])) > 0: score += 10
    if len(steps.get("ebios", {}).get("operational_scenarios", [])) > 0: score += 10
    
    # Step 5: Résilience E3R (max 15%)
    if steps.get("resilience", {}).get("logging_active"): score += 5
    if len(steps.get("resilience", {}).get("e3r", {}).get("endiguement", "")): score += 10
    
    # Step 6: Plan de Traitement (max 20%)
    if len(steps.get("traitement", {}).get("remediations", [])) > 0: score += 10
    if len(steps.get("traitement", {}).get("quick_wins", [])) == 6: score += 10
    
    return min(score, 100)

def create_default_state(project_id: str, name: str, client: str, project_type: str, framework_id: str = "iso27001") -> dict:
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
                    {"id": "SO-01", "event": "Intrusion via phishing d'un poste support, pivot vers l'Active Directory, élévation de privilèges et sabotage des serveurs de prod.", "gravity": 4, "likelihood": 3, "mitigation": "MFA, cloisonnement réseau des postes, et bastions d'administration."},
                    {"id": "SO-02", "event": "Attaque par rebond via la compromise de la console d'administration du prestataire d'infogérance tiers.", "gravity": 3, "likelihood": 2, "mitigation": "Limitation des accès tiers par VPN IPsec dédié, et audit de sécurité du prestataire."}
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
                }
            },
            "traitement": {
                "remediations": [
                    {"id": "REM-01", "axe": "Gouvernance", "measure": "Faire approuver et diffuser la nouvelle PSSI par la direction générale.", "priority": "Élevé"},
                    {"id": "REM-02", "axe": "Protection", "measure": "Déployer le MFA (Multi-Factor Authentication) sur tous les comptes d'accès distants.", "priority": "Critique"},
                    {"id": "REM-03", "axe": "Défense", "measure": "Déployer un outil de détection EDR moderne sur tous les serveurs et postes.", "priority": "Élevé"},
                    {"id": "REM-04", "axe": "Résilience", "measure": "Mettre en œuvre des sauvegardes immuables résistantes aux ransomwares.", "priority": "Critique"}
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
        fw = get_framework_by_id(framework_id) or {"name": "Referentiel", "requirements": []}
        manual_controls = [
            {
                "id": req["id"],
                "title": req["title"],
                "description": req["description"],
                "status": "A_VERIFIER",
                "notes": ""
            }
            for req in fw.get("requirements", [])
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
                "framework_id": framework_id,
                "framework_name": fw.get("name", framework_id),
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
                }
            },
            "tprm": {
                "tiers": [
                    {"name": "Hébergeur Cloud (AWS)", **_tprm_rate(4, 4, 4, 4)},
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
                    {"id": "SO-01", "event": "Contrôle CNIL inopiné révélant l'absence d'Analyse d'Impact (AIPD) pour un traitement à haut risque.", "gravity": 3, "likelihood": 2, "mitigation": "Réaliser l'AIPD de manière exhaustive via le module AIPD intégré."}
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
                }
            },
            "evaluation": {
                "manual_controls": manual_controls,
                "technical_results": None
            },
            "restitution": {
                "exec_summary": f"Audit de conformité par rapport au référentiel {fw.get('name')}.",
                "remediation_plan": []
            },
            "traitement": {
                "remediations": [
                    {"id": "REM-01", "axe": "Gouvernance", "measure": f"Valider formellement la conformité réglementaire aux exigences {fw.get('name')}.", "priority": "Élevé"}
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
def list_projects() -> list[dict]:
    projects = []
    if not PROJECTS_DIR.exists():
        return []
    for item in PROJECTS_DIR.iterdir():
        if item.is_dir():
            state_file = item / "project.json"
            if state_file.is_file():
                try:
                    state = _read_state(state_file)
                    state["progress"] = calculate_progress(state)
                    projects.append(state)
                except Exception:
                    pass
    return sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True)

@router.post("/projects")
def create_project(data: dict) -> dict:
    name = data.get("name")
    client = data.get("client", "Client Anonyme")
    project_type = data.get("type", "consulting")
    framework_id = data.get("framework_id", "iso27001")
    
    if not name:
        raise HTTPException(status_code=400, detail="Le nom du projet est obligatoire")
        
    project_id = "".join(c for c in name.lower().replace(" ", "_") if c.isalnum() or c == "_")
    if not project_id:
         project_id = f"project_{int(datetime.now().timestamp())}"
         
    p_dir = PROJECTS_DIR / project_id
    if p_dir.exists():
        raise HTTPException(status_code=400, detail="Un projet avec ce nom existe déjà")
        
    p_dir.mkdir(parents=True, exist_ok=True)
    (p_dir / "targets").mkdir(exist_ok=True)
    (p_dir / "reports").mkdir(exist_ok=True)
    
    state = create_default_state(project_id, name, client, project_type, framework_id)
    # Un projet neuf traverse la même chaîne de migration qu'un projet ancien :
    # une seule logique construit le socle/grc/consulting, jamais deux.
    state = schema_migration.migrate(state)
    _write_json_atomic(p_dir / "project.json", state)
    audit_log.record("project.create", target=project_id, detail=f"type={project_type}")
    return state


# --- Jeu de démonstration (F16) ---------------------------------------------
# Démontrer l'outil en portfolio ou en entretien exigeait jusqu'ici d'ouvrir une
# mission réelle — un manquement à la confidentialité. Cette mission est
# entièrement fictive et porte un marqueur explicite.

DEMO_ID = "demo_green_shield"


@router.post("/projects/demo")
def create_demo_project() -> dict:
    """Crée (ou recrée) la mission de démonstration fictive."""
    p_dir = PROJECTS_DIR / DEMO_ID
    if p_dir.exists():
        shutil.rmtree(p_dir)
    (p_dir / "targets").mkdir(parents=True)
    (p_dir / "reports").mkdir()

    state = create_default_state(DEMO_ID, "DÉMO — Audit ISO 27001",
                                 "Cabinet Fictif SAS", "grc", "iso27001")
    state = schema_migration.migrate(state)
    # Marqueur explicite : aucune confusion possible avec une mission réelle.
    state["is_demo"] = True
    state["socle"]["qualification"]["budget"] = "12 jours"
    state["socle"]["temps"]["entrees"] = [
        {"id": "T-001", "phase": "cadrage", "minutes": 180,
         "date": date.today().isoformat(), "note": "Réunion de lancement (fictive)"},
        {"id": "T-002", "phase": "ebios", "minutes": 240,
         "date": date.today().isoformat(), "note": "Atelier 3 EBIOS RM (fictif)"},
    ]

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

    audit_log.record("project.demo_create", target=DEMO_ID)
    return state


@router.get("/projects/{p_id}")
def get_project(p_id: str) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_file = PROJECTS_DIR / p_id / "project.json"
    if not p_file.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    try:
        state = _read_state(p_file)
        state["progress"] = calculate_progress(state)
        return state
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lecture projet: {str(exc)}")

@router.put("/projects/{p_id}")
def update_project(p_id: str, state: dict) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["progress"] = calculate_progress(state)
    try:
        # Instantané AVANT écriture, et seulement quand une phase vient d'être
        # validée : c'est le jalon métier qui mérite d'être versionné, pas
        # chaque frappe (F9).
        phase_validee = _phase_nouvellement_validee(p_dir / "project.json", state)
        if phase_validee:
            snapshots.creer(p_dir, state, f"phase-{phase_validee}-validee")

        _write_json_atomic(p_dir / "project.json", state)
        audit_log.record("project.update", target=p_id, detail=f"progress={state['progress']}%")
        return state
    except Exception as exc:
        audit_log.record("project.update", target=p_id, outcome="error")
        raise HTTPException(status_code=500, detail=f"Erreur ecriture projet: {str(exc)}")

@router.delete("/projects/{p_id}")
def delete_project(p_id: str) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    try:
        shutil.rmtree(p_dir)
        # Suppression irréversible d'une mission cliente : la trace la plus
        # importante de tout le journal.
        audit_log.record("project.delete", target=p_id)
        return {"status": "ok", "message": "Projet supprimé avec succès"}
    except Exception as exc:
         audit_log.record("project.delete", target=p_id, outcome="error")
         raise HTTPException(status_code=500, detail=f"Erreur suppression: {str(exc)}")

@router.post("/projects/{p_id}/upload")
async def upload_file(p_id: str, file: UploadFile = File(...)) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    safe_filename = path_safety.safe_filename(file.filename)
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    target_path = p_dir / "targets" / safe_filename
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    state_file = p_dir / "project.json"
    try:
        state = _read_state(state_file)
        # we populate both step levels for compatibility
        files_list = state.setdefault("steps", {}).setdefault("collecte", {}).setdefault("files", [])
        if safe_filename not in files_list:
            files_list.append(safe_filename)
        state["progress"] = calculate_progress(state)
        _write_json_atomic(state_file, state)
        audit_log.record("project.upload", target=p_id, detail=f"file={safe_filename}")
        return state
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/projects/{p_id}/audit")
def run_project_audit(p_id: str) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    
    state_file = p_dir / "project.json"
    try:
        state = _read_state(state_file)
        targets_dir = p_dir / "targets"
        result = auditcraft_grc.run(str(targets_dir))
        
        state.setdefault("steps", {}).setdefault("evaluation", {})["technical_results"] = result
        state["progress"] = calculate_progress(state)
        _write_json_atomic(state_file, state)
        audit_log.record("project.scan", target=p_id, detail=f"score={result.get('score')}")
        return state
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
def list_snapshots(p_id: str) -> list[dict]:
    """Historique versionné d'une mission (F9)."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.is_dir():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return snapshots.lister(p_dir)


@router.post("/projects/{p_id}/snapshots/{nom}/restore")
def restore_snapshot(p_id: str, nom: str) -> dict:
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
        restaure = snapshots.lire(p_dir, nom)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Instantané illisible")

    try:
        courant = _read_state(state_file)
        snapshots.creer(p_dir, courant, "avant-restauration")

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

@router.get("/rgpd/echeances")
def list_echeances_rgpd() -> list[dict]:
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
def update_politique_rgpd(p_id: str, data: dict) -> dict:
    """Fixe la durée de conservation et la date de fin de mission."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    try:
        duree = int(data.get("duree_conservation_mois", retention.DUREE_CONSERVATION_DEFAUT_MOIS))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Durée de conservation invalide (mois attendus)")
    if not 1 <= duree <= 120:
        raise HTTPException(status_code=400, detail="La durée de conservation doit être comprise entre 1 et 120 mois")

    fin = str(data.get("date_fin_mission", "") or "").strip()
    if fin:
        try:
            date.fromisoformat(fin)
        except ValueError:
            raise HTTPException(status_code=400, detail="Date de fin de mission invalide (AAAA-MM-JJ)")

    try:
        state = _read_state(state_file)
        rgpd = state.setdefault("socle", {}).setdefault("rgpd_consultant", {})
        rgpd["duree_conservation_mois"] = duree
        rgpd["date_fin_mission"] = fin
        state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        state["progress"] = calculate_progress(state)
        _write_json_atomic(state_file, state)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    audit_log.record("rgpd.politique", target=p_id, detail=f"duree={duree}mois fin={fin or 'non definie'}")
    return state


@router.post("/projects/{p_id}/rgpd/purge")
def purge_donnees_personnelles(p_id: str) -> dict:
    """Efface les données personnelles d'une mission.

    Irréversible : un instantané est donc pris juste avant, pour que le
    consultant garde une porte de sortie s'il purge par erreur.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    state_file = p_dir / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    try:
        state = _read_state(state_file)
        snapshots.creer(p_dir, state, "avant-purge-rgpd")
        state, efface = retention.purger(state)
        state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        state["progress"] = calculate_progress(state)
        _write_json_atomic(state_file, state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    audit_log.record("rgpd.purge", target=p_id, detail=f"enregistrements={efface}")
    return {"status": "ok", "efface": efface, "state": state}


@router.get("/projects/{p_id}/couverture")
def get_couverture_technique(p_id: str) -> dict:
    """Part des contrôles appuyés par une preuve technique (F10)."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    try:
        state = _read_state(state_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    resultat = couverture.couverture_technique(state)
    return {**resultat, "phrase": couverture.phrase(resultat)}


@router.get("/projects/{p_id}/revue")
def get_revue_export(p_id: str) -> dict:
    """Complétude de la mission avant génération d'un livrable.

    En lecture seule : signale ce qui manque, ne remplit rien.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    try:
        state = _read_state(state_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return revue_export.revue(state)


# --- Export / import d'une mission en archive chiffrée (F14, F15) -----------
# Le mot de passe transite dans le CORPS de la requête, jamais en paramètre
# d'URL : une URL finit dans les journaux d'accès et l'historique.

@router.post("/projects/{p_id}/archive")
def export_project_archive(p_id: str, data: dict) -> Response:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not (p_dir / "project.json").is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    try:
        contenu = archive.export_archive(p_dir, data.get("password", ""))
    except archive.ArchiveInvalide as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    audit_log.record("project.archive_export", target=p_id, detail=f"octets={len(contenu)}")
    filename = f"mission_{p_id}.zip"
    return Response(
        content=contenu,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/projects/import-archive")
async def import_project_archive(
    file: UploadFile = File(...),
    password: str = Form(""),
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
        archive.ecrire_fichiers(fichiers, p_dir)
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
    except Exception as exc:
        shutil.rmtree(p_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(exc))

    audit_log.record("project.archive_import", target=p_id, detail=f"fichiers={len(fichiers)}")
    return state


# --- Suivi du temps consommé (F19) ------------------------------------------
# Phases reconnues : les 6 étapes méthodologiques + un fourre-tout explicite
# pour ce qui ne relève d'aucune (déplacements, coordination, rédaction).
PHASES_TEMPS = ("cadrage", "diagnostic", "tprm", "ebios", "resilience", "traitement", "autre")


def _next_temps_id(entrees: list[dict]) -> str:
    """Identifiant séquentiel sans collision, même logique que _next_bs_id."""
    existants = {e.get("id", "") for e in entrees}
    numeros = [int(m.group(1)) for e in existants if (m := re.fullmatch(r"T-(\d+)", e))]
    suivant = (max(numeros) + 1) if numeros else 1
    candidat = f"T-{suivant:03d}"
    while candidat in existants:
        suivant += 1
        candidat = f"T-{suivant:03d}"
    return candidat


@router.post("/projects/{p_id}/temps")
def add_temps_entry(p_id: str, data: dict) -> dict:
    """Ajoute une entrée de temps consommé sur une mission."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    try:
        minutes = int(data.get("minutes", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Durée invalide : minutes attendues (entier)")
    if minutes <= 0:
        raise HTTPException(status_code=400, detail="La durée doit être supérieure à 0 minute")
    if minutes > 24 * 60:
        raise HTTPException(status_code=400, detail="Une entrée ne peut pas dépasser 24 h ; découpez-la par journée")

    phase = data.get("phase") or "autre"
    if phase not in PHASES_TEMPS:
        raise HTTPException(status_code=400, detail=f"Phase inconnue : {phase}")

    try:
        state = _read_state(state_file)
        temps = state.setdefault("socle", {}).setdefault("temps", {"entrees": []})
        entrees = temps.setdefault("entrees", [])
        entree = {
            "id": _next_temps_id(entrees),
            "phase": phase,
            "minutes": minutes,
            "date": data.get("date") or date.today().isoformat(),
            "note": str(data.get("note", ""))[:200],
        }
        entrees.append(entree)
        state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Comme toute mutation renvoyant la mission au client : la progression
        # est recalculée, sinon l'UI réafficherait la valeur stockée (périmée).
        state["progress"] = calculate_progress(state)
        _write_json_atomic(state_file, state)
        audit_log.record("temps.add", target=p_id, detail=f"{entree['id']} phase={phase} minutes={minutes}")
        return state
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/projects/{p_id}/temps/{entry_id}")
def delete_temps_entry(p_id: str, entry_id: str) -> dict:
    """Supprime une entrée de temps (saisie erronée)."""
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    entry_id = path_safety.safe_path_component(entry_id, "identifiant d'entrée de temps")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    try:
        state = _read_state(state_file)
        temps = state.setdefault("socle", {}).setdefault("temps", {"entrees": []})
        entrees = temps.setdefault("entrees", [])
        restantes = [e for e in entrees if e.get("id") != entry_id]
        if len(restantes) == len(entrees):
            raise HTTPException(status_code=404, detail="Entrée de temps introuvable")
        temps["entrees"] = restantes
        state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        state["progress"] = calculate_progress(state)
        _write_json_atomic(state_file, state)
        audit_log.record("temps.delete", target=p_id, detail=entry_id)
        return state
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mesures")
def list_mesures(axe: str | None = None, referentiel: str | None = None) -> list[dict]:
    """Catalogue de mesures réutilisable (décision G3) — filtrable par axe ou référentiel."""
    try:
        if referentiel:
            return mesures_catalogue.mesures_pour_referentiel(referentiel)
        if axe:
            return mesures_catalogue.mesures_par_axe(axe)
        return mesures_catalogue.list_mesures()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/frameworks/{fw_id}/workflow")
def get_framework_workflow(fw_id: str) -> dict:
    """Parcours structuré (macro-phases/étapes) d'un référentiel, pour le Kanban générique."""
    try:
        return workflow_loader.load_workflow(fw_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/frameworks/{fw_id}/agenda")
def get_framework_agenda(fw_id: str, date_demarrage: str) -> list[dict]:
    """Agenda dérivé du même workflow.yaml : jour_relatif converti en dates réelles."""
    try:
        workflow = workflow_loader.load_workflow(fw_id)
        debut = date.fromisoformat(date_demarrage)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"date_demarrage invalide (AAAA-MM-JJ) : {exc}")
    return workflow_loader.resolve_agenda(workflow, debut)


@router.get("/frameworks")
def list_frameworks() -> list[dict]:
    fws = []
    for path in FRAMEWORKS_DIR.glob("*.yaml"):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if data:
                fws.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "requirements_count": len(data.get("requirements", []))
                })
        except Exception:
            pass
    custom_dir = FRAMEWORKS_DIR / "custom"
    if custom_dir.exists():
        for path in custom_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if data:
                    fws.append({
                        "id": data.get("id"),
                        "name": f"[Perso] {data.get('name')}",
                        "description": data.get("description"),
                        "requirements_count": len(data.get("requirements", []))
                    })
            except Exception:
                pass
    return fws

@router.post("/frameworks/import")
def import_framework(data: dict) -> dict:
    fw_id = data.get("id")
    name = data.get("name")
    description = data.get("description", "")
    requirements = data.get("requirements", [])
    
    if not fw_id or not name:
        raise HTTPException(status_code=400, detail="ID et Nom sont requis")
    fw_id = path_safety.safe_path_component(fw_id, "identifiant de référentiel")

    fw_data = {
        "id": fw_id,
        "name": name,
        "description": description,
        "requirements": requirements
    }
    
    dest = FRAMEWORKS_DIR / "custom" / f"{fw_id}.yaml"
    try:
        dest.write_text(yaml.safe_dump(fw_data, allow_unicode=True), encoding="utf-8")
        audit_log.record("framework.import", target=fw_id, detail=f"requirements={len(requirements)}")
        return {"status": "ok", "id": fw_id}
    except Exception as exc:
        audit_log.record("framework.import", target=fw_id, outcome="error")
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/projects/{p_id}/report.docx")
def export_project_docx(p_id: str, auditeur: str = "", cabinet: str = "") -> Response:
    """Rapport d'audit au format Word natif (.docx), ouvrable sans avertissement.

    Chemin distinct de /export/{doc_type} : cette route-là capturerait sinon un
    doc_type="docx" et renverrait du Markdown.
    """
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    state_file = PROJECTS_DIR / p_id / "project.json"
    if not state_file.is_file():
        raise HTTPException(status_code=404, detail="Projet introuvable")
    try:
        state = _read_state(state_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lecture projet: {exc}")

    try:
        content = docx_export.render_iso27001(state, auditeur=auditeur, cabinet=cabinet)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Les en-têtes HTTP ne transportent pas d'UTF-8 tel quel : un nom de client
    # accentué (« cassiopé ») arriverait mutilé. On fournit donc un repli ASCII
    # et la forme encodée RFC 5987, que les navigateurs privilégient.
    filename = f"rapport_{p_id}.docx"
    ascii_fallback = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode() or "rapport.docx"
    disposition = (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(filename, safe='')}"
    )

    audit_log.record("project.export", target=p_id, detail="format=docx")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": disposition},
    )


@router.get("/projects/{p_id}/export/{doc_type}")
def export_project_document(p_id: str, doc_type: str) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")

    state_file = p_dir / "project.json"
    try:
        state = _read_state(state_file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        title, markdown_content = report_builder.build_document(state, p_id, doc_type)
    except report_builder.TypeDocumentInconnu as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    (p_dir / "reports").mkdir(parents=True, exist_ok=True)
    (p_dir / "reports" / title).write_text(markdown_content, encoding="utf-8")

    audit_log.record("project.export", target=p_id, detail=f"format=md type={doc_type}")
    return {"title": title, "markdown": markdown_content}

@router.post("/projects/{p_id}/copilot")
def run_project_copilot(p_id: str, data: dict) -> dict:
    p_id = path_safety.safe_path_component(p_id, "identifiant de mission")
    p_dir = PROJECTS_DIR / p_id
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable")
        
    state_file = p_dir / "project.json"
    try:
        state = _read_state(state_file)
    except Exception as exc:
         raise HTTPException(status_code=500, detail=str(exc))
         
    prompt = data.get("prompt", "")
    client = state.get("client", "Client")
    api_key = (data.get("key") or "").strip()

    if api_key:
        online_text = _call_gemini_copilot(api_key, client, prompt)
        if online_text is not None:
            # Sortie réseau effective : c'est la seule circonstance où des données
            # quittent le poste. Le contenu du prompt n'est jamais journalisé.
            audit_log.record("copilot.mission", target=p_id, detail="source=online")
            return {"status": "success", "response": online_text, "source": "online"}

    offline_replies = {
        "ebios": f"""### [Copilote AI] Recommandations EBIOS RM pour {client}

Sur la base des scénarios d'intrusion par ransomware et hameçonnage modélisés :
1. **Éradication de l'élévation de privilèges :** Restreindre drastiquement le groupe 'Administrateurs du Domaine' et isoler l'administration Active Directory via un serveur de rebond dédié (Tier-0/Tier-1).
2. **Cloisonnement de l'écosystème tiers (TPRM) :** Imposer un VPN avec double authentification nominative pour tout accès infogéreur tiers.
3. **MFA et Protection des Terminaux :** Déployer un EDR managé en 24/7 sur tous les postes et serveurs pour détecter les mouvements latéraux.""",
        
        "pssi": f"""### [Copilote AI] Recommandations d'Amélioration PSSI pour {client}

Pour élever l'hygiène informatique au niveau des guides de l'ANSSI :
1. **Politique de Mots de Passe :** Migrer vers l'authentification sans mot de passe ou imposer une longueur minimale de 15 caractères complexes.
2. **Minimisation des Privilèges :** Retirer les droits d'administration locale de tous les utilisateurs sur les postes de travail.
3. **Revues de Comptes :** Organiser une revue trimestrielle systématique de tous les accès et couper les comptes dormants.""",
        
        "resilience": f"""### [Copilote AI] Stratégie de Résilience & Continuité (RTO/RPO)

Pour garantir que l'organisation puisse résister à un rançongiciel destructeur :
1. **Sauvegardes Immuables :** Configurer des instantanés (snapshots) immuables WORM sur stockage cloud ou bandes physiques déconnectées.
2. **Séquence E3R :** Établir des fiches réflexes plastifiées pour la coupure d'urgence d'Internet en cas d'attaque active pour bloquer l'exfiltration.
3. **Exercices réguliers :** Planifier un exercice de table (simulation de gestion de crise) de 4 heures avec le Comité de Direction pour tester la communication de crise.""",
        
        "default": f"""### [Copilote AI] Analyse d'Expert Cyber pour {client}

Sur la base des informations recueillies :
1. **Mesure immédiate :** Établir le Plan de Reprise Informatique (PRI) et tester la restauration à blanc d'un serveur métier critique sous 4 heures (RTO).
2. **Alignement NIS 2 :** Lancer l'évaluation TPRM pour tous les prestataires clés d'ici la fin du mois.
3. **Vigilance RGPD :** Réaliser le PIA/AIPD requis sur le traitement des données clients afin de devancer d'éventuels contrôles de la CNIL."""
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
