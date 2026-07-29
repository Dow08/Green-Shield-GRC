"""Tests des référentiels personnels (chaînon manquant de F2).

L'audit prescrit d'enrichir les référentiels **au fil des missions réelles**
plutôt qu'en amont. Encore faut-il que le consultant puisse le faire : la route
d'import existait sans aucune interface, et rien n'empêchait un référentiel
personnel de masquer un référentiel livré.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import projects  # noqa: E402


@pytest.fixture()
def referentiels(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "FRAMEWORKS_DIR", tmp_path)
    (tmp_path / "custom").mkdir()
    # Un référentiel « livré avec l'application »
    (tmp_path / "iso27001.yaml").write_text(
        yaml.safe_dump({"id": "iso27001", "name": "ISO/IEC 27001:2022",
                        "description": "d", "requirements": [{"id": "ISO-A.5", "title": "Politiques"}]},
                       allow_unicode=True),
        encoding="utf-8",
    )
    return tmp_path


# --- Création d'un référentiel personnel -----------------------------------

def test_cree_un_referentiel_personnel(referentiels):
    resultat = projects.import_framework({
        "id": "secteur_sante", "name": "Exigences secteur santé",
        "requirements": [{"id": "SANTE-01", "title": "Hébergeur de données de santé (HDS)"}],
    })
    assert resultat["status"] == "ok"
    assert (referentiels / "custom" / "secteur_sante.yaml").is_file()


def test_le_referentiel_cree_est_relisible(referentiels):
    projects.import_framework({
        "id": "secteur_sante", "name": "Exigences secteur santé",
        "requirements": [{"id": "SANTE-01", "title": "HDS"}],
    })
    detail = projects.get_framework_detail("secteur_sante")
    assert detail["name"] == "Exigences secteur santé"
    assert detail["requirements"][0]["id"] == "SANTE-01"
    assert detail["personnel"] is True


def test_un_referentiel_livre_est_signale_comme_non_personnel(referentiels):
    """Il est écrasé à chaque mise à jour de l'application : l'interface doit
    pouvoir l'indiquer plutôt que de laisser croire qu'il est modifiable."""
    assert projects.get_framework_detail("iso27001")["personnel"] is False


def test_enrichir_un_referentiel_personnel_conserve_les_exigences_renvoyees(referentiels):
    """L'enrichissement se fait en relisant puis en réimportant la liste
    complète — c'est le contrat de la route, qui réécrit le fichier."""
    projects.import_framework({"id": "perso", "name": "P", "requirements": [{"id": "R1", "title": "Un"}]})
    detail = projects.get_framework_detail("perso")
    exigences = detail["requirements"] + [{"id": "R2", "title": "Deux"}]
    projects.import_framework({"id": "perso", "name": "P", "requirements": exigences})

    assert len(projects.get_framework_detail("perso")["requirements"]) == 2


# --- Refus des collisions --------------------------------------------------

def test_un_identifiant_de_referentiel_livre_est_refuse(referentiels):
    """Sans ce refus, custom/iso27001.yaml serait masqué par le fichier livré
    et le référentiel apparaîtrait deux fois dans la liste."""
    with pytest.raises(HTTPException) as exc:
        projects.import_framework({"id": "iso27001", "name": "Ma version"})
    assert exc.value.status_code == 409
    assert "livré avec l'application" in exc.value.detail


def test_le_referentiel_livre_reste_intact_apres_une_tentative(referentiels):
    with pytest.raises(HTTPException):
        projects.import_framework({"id": "iso27001", "name": "Ma version"})
    original = yaml.safe_load((referentiels / "iso27001.yaml").read_text(encoding="utf-8"))
    assert original["name"] == "ISO/IEC 27001:2022"


def test_un_identifiant_traverse_est_refuse(referentiels):
    with pytest.raises(HTTPException) as exc:
        projects.import_framework({"id": "../evasion", "name": "X"})
    assert exc.value.status_code == 400


def test_id_et_nom_sont_obligatoires(referentiels):
    with pytest.raises(HTTPException) as exc:
        projects.import_framework({"id": "", "name": ""})
    assert exc.value.status_code == 400


# --- Lecture ---------------------------------------------------------------

def test_lire_un_referentiel_inexistant_renvoie_404(referentiels):
    with pytest.raises(HTTPException) as exc:
        projects.get_framework_detail("nexiste_pas")
    assert exc.value.status_code == 404


def test_les_referentiels_personnels_apparaissent_dans_la_liste(referentiels):
    projects.import_framework({"id": "perso", "name": "Mon référentiel",
                               "requirements": [{"id": "R1", "title": "Un"}]})
    liste = projects.list_frameworks()
    par_id = {f["id"]: f for f in liste}
    assert "iso27001" in par_id
    assert par_id["perso"]["name"].startswith("[Perso]")
    assert par_id["perso"]["requirements_count"] == 1


# --- Le répertoire frameworks/ ne contient pas que des référentiels --------

def test_le_catalogue_de_mesures_n_apparait_pas_comme_referentiel(referentiels):
    """`mesures_catalogue.yaml` vit dans frameworks/ sans être un référentiel.
    Sans filtre il produisait une entrée fantôme `id: null`, soit une option
    vide dans le sélecteur à la création d'une mission GRC."""
    (referentiels / "mesures_catalogue.yaml").write_text(
        yaml.safe_dump({"metadata": {"version": "1"}, "mesures": [{"id": "M1"}]}, allow_unicode=True),
        encoding="utf-8",
    )
    liste = projects.list_frameworks()
    assert all(f["id"] for f in liste), "une entrée sans identifiant s'est glissée dans la liste"
    assert all(f["name"] for f in liste)
    assert "mesures_catalogue" not in [f["id"] for f in liste]


def test_un_yaml_sans_nom_est_ignore(referentiels):
    (referentiels / "incomplet.yaml").write_text(
        yaml.safe_dump({"id": "incomplet"}, allow_unicode=True), encoding="utf-8")
    assert "incomplet" not in [f["id"] for f in projects.list_frameworks()]


def test_un_yaml_illisible_n_interrompt_pas_la_liste(referentiels):
    (referentiels / "casse.yaml").write_text("{ ceci n'est pas: du yaml: valide", encoding="utf-8")
    assert "iso27001" in [f["id"] for f in projects.list_frameworks()]
