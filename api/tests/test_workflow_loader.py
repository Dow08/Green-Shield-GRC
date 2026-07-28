"""Tests du chargement des parcours (workflow.yaml) et de la vue Agenda."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import workflow_loader  # noqa: E402


def test_iso27001_est_liste():
    assert "iso27001" in workflow_loader.list_workflow_ids()


def test_chargement_iso27001_valide():
    wf = workflow_loader.load_workflow("iso27001")
    assert wf["metadata"]["id"] == "iso27001"
    ids = [p["id"] for p in wf["macro_phases"]]
    assert ids == ["preparation", "execution", "synthese", "suivi"]


def test_referentiel_inconnu_leve_une_erreur_explicite():
    with pytest.raises(FileNotFoundError):
        workflow_loader.load_workflow("referentiel_qui_n_existe_pas")


def test_v07_referentiel_id_avec_traversee_est_rejete():
    """Non-régression : audit du 28/07/2026 (V-07). referentiel_id non assaini
    permettait de charger le workflow.yaml d'un répertoire arbitraire situé
    au-dessus de FRAMEWORKS_DIR."""
    with pytest.raises(HTTPException) as exc_info:
        workflow_loader.load_workflow("../../../../etc")
    assert exc_info.value.status_code == 400


def test_chaque_etape_du_workflow_officiel_porte_les_champs_attendus():
    """Le Kanban/Agenda/grille d'entretien dépendent tous de ces clés : leur absence
    casserait silencieusement une des 3 vues plutôt que de lever une erreur ici."""
    wf = workflow_loader.load_workflow("iso27001")
    for phase in wf["macro_phases"]:
        for etape in phase["etapes"]:
            for cle in ("id", "titre", "role_a_rencontrer", "questions", "champs", "sources"):
                assert cle in etape, f"{phase['id']}.{etape['id']} sans '{cle}'"


def test_annexe_a_porte_une_source_automatique_auditcraft():
    """Vérifie le point d'ancrage §10.7 du spec : le scan technique réel doit
    alimenter cette étape précise, pas une étape voisine renommée par erreur."""
    wf = workflow_loader.load_workflow("iso27001")
    execution = next(p for p in wf["macro_phases"] if p["id"] == "execution")
    annexe_a = next(e for e in execution["etapes"] if e["id"] == "audit_annexe_a")
    champ = next(c for c in annexe_a["champs"] if c["key"] == "controles_annexe_a")
    assert champ["source_automatique"] == "auditcraft_grc"


class _FakeWorkflow(dict):
    pass


def _workflow_minimal() -> dict:
    return {
        "macro_phases": [
            {"id": "p1", "titre": "Phase 1", "etapes": [
                {"id": "e1", "titre": "Étape 1", "jour_relatif": 1},
                {"id": "e2", "titre": "Étape 2", "jour_relatif": 8, "duree": "1 semaine",
                 "role_a_rencontrer": ["RSSI"]},
                {"id": "e3", "titre": "Sans date"},  # pas de jour_relatif -> exclue de l'agenda
            ]},
        ]
    }


def test_agenda_jour_1_correspond_a_la_date_de_demarrage():
    """Convention Hermes : jour_relatif=1 est le jour de démarrage, pas J+1."""
    agenda = workflow_loader.resolve_agenda(_workflow_minimal(), date(2026, 8, 3))
    assert agenda[0]["date"] == "2026-08-03"


def test_agenda_calcule_les_dates_suivantes_et_ignore_les_etapes_sans_date():
    agenda = workflow_loader.resolve_agenda(_workflow_minimal(), date(2026, 8, 3))
    assert len(agenda) == 2  # e3 (sans jour_relatif) n'apparaît pas
    assert agenda[1]["date"] == "2026-08-10"  # jour_relatif=8 -> +7 jours
    assert agenda[1]["role_a_rencontrer"] == ["RSSI"]


def test_agenda_trie_par_date():
    wf = {"macro_phases": [
        {"id": "p1", "titre": "P1", "etapes": [{"id": "tard", "titre": "Tard", "jour_relatif": 30}]},
        {"id": "p2", "titre": "P2", "etapes": [{"id": "tot", "titre": "Tôt", "jour_relatif": 1}]},
    ]}
    agenda = workflow_loader.resolve_agenda(wf, date(2026, 1, 1))
    assert [a["etape_id"] for a in agenda] == ["tot", "tard"]
