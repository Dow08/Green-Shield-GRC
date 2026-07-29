"""Tests de la conservation et de la purge des données personnelles (F17).

Le consultant est responsable de traitement pour les noms, fonctions et
déclarations des personnes interrogées. Deux exigences vérifiées ici :
  * la purge efface bien TOUTES les données identifiantes ;
  * elle n'efface RIEN d'autre — les constats d'audit sont la valeur du travail
    et ne sont pas des données personnelles.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects, retention, schema_migration  # noqa: E402


def mission_avec_personnes() -> dict:
    return {
        "id": "acme", "name": "Acme", "client": "Acme Corp",
        "socle": {
            "entretiens": [
                {"nom": "Marie Dupont", "fonction": "RSSI", "declarations": "La PSSI date de 2019."},
                {"nom": "Paul Martin", "fonction": "DSI", "declarations": "Sauvegardes non testées."},
            ],
            "kickoff": {"date": "2026-01-10", "participants": ["Marie Dupont", "Paul Martin"],
                        "gouvernance": "Comité mensuel"},
            "rgpd_consultant": {"duree_conservation_mois": 36, "date_fin_mission": "", "purge_effectuee_le": ""},
        },
        "steps": {
            "cadrage": {"scope": "SI de production",
                        "assets_support": [{"id": "BS-01", "name": "Active Directory"}]},
            "traitement": {"remediations": [{"id": "REM-01", "measure": "Déployer un EDR"}]},
            "evaluation": {"manual_controls": [{"id": "A.5.1", "status": "NON_CONFORME"}]},
        },
    }


# --- Migration -------------------------------------------------------------

def test_migration_v4_ajoute_la_politique_de_conservation():
    state = schema_migration.migrate({"id": "x"})
    rgpd = state["socle"]["rgpd_consultant"]
    assert rgpd["duree_conservation_mois"] == 36
    assert rgpd["date_fin_mission"] == ""
    assert state["schema_version"] == 4


def test_migration_v4_n_ecrase_pas_une_politique_existante():
    existante = {"duree_conservation_mois": 12, "date_fin_mission": "2026-01-01", "purge_effectuee_le": ""}
    state = schema_migration.migrate({"schema_version": 3, "socle": {"rgpd_consultant": existante}})
    assert state["socle"]["rgpd_consultant"]["duree_conservation_mois"] == 12


# --- Échéance --------------------------------------------------------------

def test_aucune_echeance_tant_que_la_mission_n_est_pas_terminee():
    """Le délai court depuis la FIN de la relation, pas depuis son début."""
    e = retention.echeance(mission_avec_personnes())
    assert e["statut"] == "mission_en_cours"
    assert e["date_purge_prevue"] == ""


def test_echeance_calculee_depuis_la_fin_de_mission():
    m = mission_avec_personnes()
    m["socle"]["rgpd_consultant"]["date_fin_mission"] = "2026-01-31"
    m["socle"]["rgpd_consultant"]["duree_conservation_mois"] = 12
    assert retention.echeance(m)["date_purge_prevue"] == "2027-01-31"


def test_le_calcul_gere_les_fins_de_mois_courts():
    """31 janvier + 1 mois n'existe pas : on ramène au dernier jour de février."""
    m = mission_avec_personnes()
    m["socle"]["rgpd_consultant"]["date_fin_mission"] = "2026-01-31"
    m["socle"]["rgpd_consultant"]["duree_conservation_mois"] = 1
    assert retention.echeance(m)["date_purge_prevue"] == "2026-02-28"


def test_une_echeance_depassee_est_signalee():
    m = mission_avec_personnes()
    m["socle"]["rgpd_consultant"]["date_fin_mission"] = (date.today() - timedelta(days=800)).isoformat()
    m["socle"]["rgpd_consultant"]["duree_conservation_mois"] = 12
    e = retention.echeance(m)
    assert e["statut"] == "echue"
    assert e["jours_restants"] < 0


def test_une_echeance_a_venir_indique_les_jours_restants():
    m = mission_avec_personnes()
    m["socle"]["rgpd_consultant"]["date_fin_mission"] = date.today().isoformat()
    m["socle"]["rgpd_consultant"]["duree_conservation_mois"] = 12
    e = retention.echeance(m)
    assert e["statut"] == "en_conservation"
    assert e["jours_restants"] > 300


def test_une_mission_deja_purgee_n_a_plus_d_echeance():
    m = mission_avec_personnes()
    m["socle"]["rgpd_consultant"]["purge_effectuee_le"] = "2026-05-01"
    assert retention.echeance(m)["statut"] == "purgee"


def test_une_date_de_fin_invalide_est_signalee_sans_planter():
    m = mission_avec_personnes()
    m["socle"]["rgpd_consultant"]["date_fin_mission"] = "pas-une-date"
    assert retention.echeance(m)["statut"] == "date_invalide"


# --- Comptage et purge -----------------------------------------------------

def test_compte_les_enregistrements_identifiants():
    # 2 entretiens + 2 participants
    assert retention.compter_donnees_personnelles(mission_avec_personnes()) == 4


def test_la_purge_efface_les_entretiens_et_les_participants():
    state, efface = retention.purger(mission_avec_personnes())
    assert efface == 4
    assert state["socle"]["entretiens"] == []
    assert state["socle"]["kickoff"]["participants"] == []
    assert retention.compter_donnees_personnelles(state) == 0


def test_la_purge_ne_touche_pas_aux_constats_d_audit():
    """Minimisation, pas destruction : le travail d'audit reste exploitable."""
    state, _ = retention.purger(mission_avec_personnes())
    assert state["steps"]["cadrage"]["scope"] == "SI de production"
    assert state["steps"]["cadrage"]["assets_support"][0]["name"] == "Active Directory"
    assert state["steps"]["traitement"]["remediations"][0]["measure"] == "Déployer un EDR"
    assert state["steps"]["evaluation"]["manual_controls"][0]["status"] == "NON_CONFORME"


def test_la_purge_conserve_les_donnees_non_identifiantes_du_kickoff():
    state, _ = retention.purger(mission_avec_personnes())
    assert state["socle"]["kickoff"]["gouvernance"] == "Comité mensuel"
    assert state["socle"]["kickoff"]["date"] == "2026-01-10"


def test_la_purge_est_datee():
    state, _ = retention.purger(mission_avec_personnes())
    assert state["socle"]["rgpd_consultant"]["purge_effectuee_le"] == date.today().isoformat()


def test_purger_une_mission_deja_purgee_est_sans_effet():
    state, _ = retention.purger(mission_avec_personnes())
    state, efface = retention.purger(state)
    assert efface == 0


def test_la_purge_d_une_mission_vide_ne_plante_pas():
    state, efface = retention.purger({})
    assert efface == 0


# --- Routes ----------------------------------------------------------------

@pytest.fixture()
def registre(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    p_dir = tmp_path / "acme"
    p_dir.mkdir()
    (p_dir / "project.json").write_text(json.dumps(mission_avec_personnes()), encoding="utf-8")
    return tmp_path


def test_la_route_fixe_la_politique(registre):
    state = projects.update_politique_rgpd("acme", {"duree_conservation_mois": 24,
                                                    "date_fin_mission": "2026-06-30"})
    rgpd = state["socle"]["rgpd_consultant"]
    assert rgpd["duree_conservation_mois"] == 24
    assert rgpd["date_fin_mission"] == "2026-06-30"


@pytest.mark.parametrize("duree", [0, -5, 121, "trois ans"])
def test_une_duree_de_conservation_aberrante_est_rejetee(registre, duree):
    with pytest.raises(HTTPException) as exc:
        projects.update_politique_rgpd("acme", {"duree_conservation_mois": duree})
    assert exc.value.status_code == 400


def test_une_date_de_fin_invalide_est_rejetee(registre):
    with pytest.raises(HTTPException) as exc:
        projects.update_politique_rgpd("acme", {"date_fin_mission": "30/06/2026"})
    assert exc.value.status_code == 400


def test_la_route_de_purge_efface_et_compte(registre):
    resultat = projects.purge_donnees_personnelles("acme")
    assert resultat["efface"] == 4
    sur_disque = json.loads((registre / "acme" / "project.json").read_text(encoding="utf-8"))
    assert sur_disque["socle"]["entretiens"] == []


def test_la_purge_prend_un_instantane_de_secours(registre):
    """Irréversible : le consultant doit garder une porte de sortie."""
    from modules import snapshots
    projects.purge_donnees_personnelles("acme")
    motifs = [s["motif"] for s in snapshots.lister(registre / "acme")]
    assert any("purge" in m for m in motifs)


def test_les_echeances_listent_les_missions_echues_en_tete(registre):
    autre = registre / "echue"
    autre.mkdir()
    m = mission_avec_personnes()
    m["id"] = "echue"
    m["socle"]["rgpd_consultant"]["date_fin_mission"] = (date.today() - timedelta(days=2000)).isoformat()
    (autre / "project.json").write_text(json.dumps(m), encoding="utf-8")

    echeances = projects.list_echeances_rgpd()
    assert echeances[0]["statut"] == "echue"
    assert echeances[0]["project_id"] == "echue"


def test_les_echeances_comptent_les_donnees_restantes(registre):
    echeances = projects.list_echeances_rgpd()
    assert echeances[0]["donnees_personnelles"] == 4


def test_la_purge_sur_mission_introuvable_renvoie_404(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        projects.purge_donnees_personnelles("inexistante")
    assert exc.value.status_code == 404


def test_la_purge_avec_p_id_traverse_est_rejetee(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        projects.purge_donnees_personnelles("..")
    assert exc.value.status_code == 400
