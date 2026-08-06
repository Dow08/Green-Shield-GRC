"""Tests de l'historique versionné des missions (F9).

Enjeu : rattraper une erreur de saisie sans avoir à ressaisir une phase
entière. Et surtout, ne jamais faire échouer une sauvegarde à cause d'un
instantané raté.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects, snapshots  # noqa: E402


@pytest.fixture()
def mission(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    p_dir = tmp_path / "acme"
    p_dir.mkdir()
    (p_dir / "project.json").write_text(
        json.dumps({"id": "acme", "name": "Acme", "client": "Acme Corp",
                    "steps": {"cadrage": {"scope": "initial"}}}),
        encoding="utf-8",
    )
    return p_dir


def _etat(p_dir: Path) -> dict:
    return projects._read_state(p_dir / "project.json")


# --- Module snapshots ------------------------------------------------------

def test_creer_produit_un_instantane_horodate(mission):
    nom = snapshots.creer(mission, {"id": "acme"}, "test")
    assert nom is not None
    assert (mission / "snapshots" / nom).is_file()


def test_lister_renvoie_du_plus_recent_au_plus_ancien(mission):
    import time
    for i in range(3):
        snapshots.creer(mission, {"i": i}, f"motif{i}")
        time.sleep(1.05)  # l'horodatage est à la seconde
    noms = [s["nom"] for s in snapshots.lister(mission)]
    assert noms == sorted(noms, reverse=True)


def test_lister_sur_une_mission_sans_historique(mission):
    assert snapshots.lister(mission) == []


def test_lire_restitue_l_etat_enregistre(mission):
    nom = snapshots.creer(mission, {"id": "acme", "marqueur": "v1"}, "test")
    assert snapshots.lire(mission, nom)["marqueur"] == "v1"


def test_lire_un_instantane_absent_leve_une_erreur(mission):
    with pytest.raises(FileNotFoundError):
        snapshots.lire(mission, "20260101-000000_inexistant.json")


# --- Chiffrement au repos (P0) : `chiffrer`/`dechiffrer` optionnels --------

def _chiffrer_test(donnees: bytes) -> bytes:
    return b"CHIFFRE:" + donnees


def _dechiffrer_test(donnees: bytes) -> bytes:
    assert donnees.startswith(b"CHIFFRE:")
    return donnees[len(b"CHIFFRE:"):]


def test_creer_sans_chiffrer_ecrit_du_json_clair(mission):
    nom = snapshots.creer(mission, {"id": "acme"}, "test")
    contenu = (mission / "snapshots" / nom).read_bytes()
    assert json.loads(contenu.decode("utf-8")) == {"id": "acme"}


def test_creer_avec_chiffrer_protege_le_fichier_sur_disque(mission):
    nom = snapshots.creer(mission, {"id": "acme"}, "test", chiffrer=_chiffrer_test)
    contenu = (mission / "snapshots" / nom).read_bytes()
    assert contenu.startswith(b"CHIFFRE:")
    assert json.loads(_dechiffrer_test(contenu)) == {"id": "acme"}


def test_lire_avec_dechiffrer_restitue_l_etat(mission):
    nom = snapshots.creer(mission, {"id": "acme", "marqueur": "v1"}, "test", chiffrer=_chiffrer_test)
    assert snapshots.lire(mission, nom, dechiffrer=_dechiffrer_test)["marqueur"] == "v1"


def test_l_historique_est_elague_au_dela_du_plafond(mission, monkeypatch):
    monkeypatch.setattr(snapshots, "MAX_SNAPSHOTS", 3)
    dossier = mission / "snapshots"
    dossier.mkdir()
    # Instantanés fabriqués directement pour maîtriser leur horodatage.
    for i in range(6):
        (dossier / f"2026010{i}-000000_motif.json").write_text("{}", encoding="utf-8")
    snapshots.creer(mission, {}, "nouveau")
    assert len(list(dossier.glob("*.json"))) == 3


def test_un_instantane_impossible_ne_leve_jamais(mission, monkeypatch):
    """Une sauvegarde de mission ne doit pas échouer parce que le disque est
    plein au moment de l'instantané."""
    def echoue(*a, **k):
        raise OSError("disque plein")
    monkeypatch.setattr(Path, "mkdir", echoue)
    assert snapshots.creer(mission, {}, "test") is None


# --- Déclenchement à la validation de phase --------------------------------

def test_valider_une_phase_declenche_un_instantane(mission):
    etat = _etat(mission)
    etat["steps"]["cadrage"]["validated"] = True
    projects.update_project("acme", etat)
    assert len(snapshots.lister(mission)) == 1
    assert "cadrage" in snapshots.lister(mission)[0]["motif"]


def test_une_sauvegarde_ordinaire_ne_cree_pas_d_instantane(mission):
    etat = _etat(mission)
    etat["steps"]["cadrage"]["scope"] = "modifié"
    projects.update_project("acme", etat)
    assert snapshots.lister(mission) == []


def test_resauvegarder_une_phase_deja_validee_ne_recree_pas_d_instantane(mission):
    etat = _etat(mission)
    etat["steps"]["cadrage"]["validated"] = True
    projects.update_project("acme", etat)

    encore = _etat(mission)
    encore["steps"]["cadrage"]["scope"] = "autre chose"
    projects.update_project("acme", encore)

    assert len(snapshots.lister(mission)) == 1


# --- Routes ----------------------------------------------------------------

def test_la_route_liste_l_historique(mission):
    snapshots.creer(mission, {"id": "acme"}, "test")
    assert len(projects.list_snapshots("acme")) == 1


def test_restaurer_remet_la_mission_dans_son_etat_anterieur(mission):
    nom = snapshots.creer(mission, {"id": "acme", "steps": {"cadrage": {"scope": "AVANT"}}}, "test")

    courant = _etat(mission)
    courant["steps"]["cadrage"]["scope"] = "APRES"
    projects.update_project("acme", courant)
    assert _etat(mission)["steps"]["cadrage"]["scope"] == "APRES"

    restaure = projects.restore_snapshot("acme", nom)
    assert restaure["steps"]["cadrage"]["scope"] == "AVANT"
    assert _etat(mission)["steps"]["cadrage"]["scope"] == "AVANT"


def test_restaurer_instantane_l_etat_courant_avant_ecrasement(mission):
    """Une restauration ne doit pas être un aller sans retour."""
    nom = snapshots.creer(mission, {"id": "acme", "steps": {}}, "test")
    projects.restore_snapshot("acme", nom)
    motifs = [s["motif"] for s in snapshots.lister(mission)]
    assert any("avant restauration" in m for m in motifs)


def test_restaurer_applique_la_migration_de_schema(mission):
    from modules import schema_migration
    nom = snapshots.creer(mission, {"id": "acme", "steps": {}}, "vieux")
    restaure = projects.restore_snapshot("acme", nom)
    assert restaure["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION


@pytest.mark.parametrize("nom_malveillant", [
    "../../../etc/passwd",
    "../project.json",
    "20260101-000000_motif.json/../../evasion",
    "pas-un-format-valide.json",
    "20260101-000000_motif.txt",
])
def test_un_nom_d_instantane_malveillant_est_rejete(mission, nom_malveillant):
    with pytest.raises(HTTPException) as exc:
        projects.restore_snapshot("acme", nom_malveillant)
    assert exc.value.status_code == 400


def test_restaurer_un_instantane_inexistant_renvoie_404(mission):
    with pytest.raises(HTTPException) as exc:
        projects.restore_snapshot("acme", "20260101-000000_absent.json")
    assert exc.value.status_code == 404


def test_lister_sur_mission_introuvable_renvoie_404(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", tmp_path, raising=False)
    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", tmp_path, raising=False)
    with pytest.raises(HTTPException) as exc:
        projects.list_snapshots("inexistante")
    assert exc.value.status_code == 404


def test_les_instantanes_voyagent_dans_l_archive(mission):
    """L'historique vit sous <mission>/snapshots/ : il doit donc être embarqué
    par l'export d'archive (F14)."""
    from modules import archive
    snapshots.creer(mission, {"id": "acme"}, "test")
    (mission / "targets").mkdir(exist_ok=True)
    donnees = archive.export_archive(mission, "motdepasse")
    _, fichiers = archive.lire_archive(donnees, "motdepasse")
    assert any(n.startswith("snapshots/") for n, _ in fichiers), (
        "l'historique doit voyager avec l'archive : sans lui, une restauration "
        "depuis archive repartirait sans aucun point de retour"
    )
