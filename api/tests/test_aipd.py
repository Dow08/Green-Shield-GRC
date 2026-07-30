"""Obligations organisationnelles de l'AIPD (§14.2.1).

Le module couvrait les quatre volets d'*analyse* ; ces tests portent sur les
cinq obligations de *conduite*, dont l'une — la consultation préalable de la
CNIL — n'est due que si un risque résiduel élevé subsiste après mesures.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import aipd, report_builder, revue_export, schema_migration  # noqa: E402


def _aipd(risque: str = "acceptable", satisfaites: tuple[str, ...] = ()) -> dict:
    return {
        "risque_residuel": risque,
        "obligations": [
            {"id": o["id"], "satisfait": o["id"] in satisfaites, "commentaire": ""}
            for o in aipd.OBLIGATIONS
        ],
    }


# --- Le référentiel ---------------------------------------------------------

def test_les_cinq_obligations_du_spec_sont_couvertes():
    ids = {o["id"] for o in aipd.OBLIGATIONS}
    assert ids == {"DPO", "PERSONNES", "LISTES_CNIL", "REEXAMEN", "ART36"}


def test_chaque_obligation_cite_son_article():
    """Sans référence, le consultant ne peut ni la justifier ni la vérifier."""
    assert all(o["reference"].startswith("RGPD Art.") for o in aipd.OBLIGATIONS)


def test_seule_la_consultation_prealable_est_conditionnelle():
    conditionnelles = [o["id"] for o in aipd.OBLIGATIONS if o["conditionnelle"]]
    assert conditionnelles == ["ART36"]


def test_le_referentiel_ne_recopie_pas_le_texte_du_reglement():
    """F3 : identifiants et intitulés courts reformulés, jamais le texte."""
    assert all(len(o["libelle"]) < 90 for o in aipd.OBLIGATIONS)


def test_les_obligations_par_defaut_sont_non_traitees():
    obligations = aipd.obligations_par_defaut()
    assert len(obligations) == 5
    assert all(o["satisfait"] is False for o in obligations)


def test_deux_appels_ne_partagent_pas_la_meme_liste():
    a, b = aipd.obligations_par_defaut(), aipd.obligations_par_defaut()
    a[0]["satisfait"] = True
    assert b[0]["satisfait"] is False


# --- L'obligation conditionnelle -------------------------------------------

def test_la_consultation_cnil_n_est_pas_due_sur_risque_acceptable():
    assert aipd.art36_requise(_aipd("acceptable")) is False


def test_la_consultation_cnil_est_due_sur_risque_eleve():
    assert aipd.art36_requise(_aipd("eleve")) is True


def test_un_risque_non_evalue_ne_declenche_pas_l_article_36():
    """Il ne le déclenche pas, mais la revue avant export le signale : c'est là
    que le manque doit apparaître, pas sous forme d'obligation inventée."""
    assert aipd.art36_requise(_aipd("non_evalue")) is False


def test_une_obligation_non_exigible_ne_compte_pas_au_denominateur():
    """La compter ferait afficher un taux inférieur à la réalité, et pousserait
    à cocher une case qui n'est pas due."""
    assert aipd.etat(_aipd("acceptable"))["total"] == 4
    assert aipd.etat(_aipd("eleve"))["total"] == 5


def test_le_taux_ignore_l_obligation_non_exigible():
    etat = aipd.etat(_aipd("acceptable", ("DPO", "PERSONNES", "LISTES_CNIL", "REEXAMEN")))
    assert etat["taux"] == 100
    assert etat["complete"] is True


def test_les_quatre_obligations_ne_suffisent_pas_sur_risque_eleve():
    etat = aipd.etat(_aipd("eleve", ("DPO", "PERSONNES", "LISTES_CNIL", "REEXAMEN")))
    assert etat["complete"] is False
    assert etat["manquantes"] == ["Consultation préalable de la CNIL avant mise en œuvre"]


def test_une_aipd_vierge_n_est_pas_complete():
    etat = aipd.etat({})
    assert etat["complete"] is False
    assert etat["satisfaites"] == 0


# --- L'alerte bloquante -----------------------------------------------------

def test_aucune_alerte_quand_le_risque_residuel_est_acceptable():
    assert aipd.alerte_bloquante(_aipd("acceptable")) is None


def test_alerte_quand_un_risque_eleve_n_a_pas_ete_soumis_a_la_cnil():
    message = aipd.alerte_bloquante(_aipd("eleve"))
    assert message is not None
    assert "Art. 36" in message


def test_l_alerte_disparait_une_fois_la_cnil_consultee():
    assert aipd.alerte_bloquante(_aipd("eleve", ("ART36",))) is None


# --- Migration v6 -----------------------------------------------------------

def test_la_migration_ajoute_les_obligations():
    state = schema_migration.migrate({"schema_version": 5})
    assert len(state["steps"]["diagnostic"]["aipd"]["obligations"]) == 5


def test_le_risque_residuel_demarre_non_evalue():
    """Le supposer acceptable ferait disparaître l'obligation Art. 36 sans que
    personne ne l'ait jugée."""
    state = schema_migration.migrate({"schema_version": 5})
    assert state["steps"]["diagnostic"]["aipd"]["risque_residuel"] == "non_evalue"


def test_la_migration_preserve_les_quatre_volets_d_analyse():
    existant = {"treatment_description": "Profilage", "necessity_eval": "n",
                "risks_eval": "r", "mitigation_measures": "m"}
    state = schema_migration.migrate({"schema_version": 5,
                                      "steps": {"diagnostic": {"aipd": dict(existant)}}})
    aipd_migre = state["steps"]["diagnostic"]["aipd"]
    assert all(aipd_migre[k] == v for k, v in existant.items())


def test_la_migration_n_ecrase_pas_des_obligations_deja_saisies():
    deja = [{"id": "DPO", "satisfait": True, "commentaire": "Avis du 12/06"}]
    state = schema_migration.migrate({"schema_version": 5,
                                      "steps": {"diagnostic": {"aipd": {"obligations": deja}}}})
    assert state["steps"]["diagnostic"]["aipd"]["obligations"] == deja


@pytest.mark.parametrize("depart", [1, 2, 3, 4, 5])
def test_une_mission_de_n_importe_quelle_version_recoit_les_obligations(depart):
    state = schema_migration.migrate({"schema_version": depart})
    assert state["schema_version"] == schema_migration.CURRENT_SCHEMA_VERSION
    assert "obligations" in state["steps"]["diagnostic"]["aipd"]


# --- Revue avant export -----------------------------------------------------

def _mission(aipd_data: dict) -> dict:
    return {"steps": {"diagnostic": {"aipd_required": True, "rgpd_register": [{"id": "R1"}],
                                     "aipd": {"treatment_description": "d", "necessity_eval": "n",
                                              "risks_eval": "r", "mitigation_measures": "m",
                                              **aipd_data}}}}


def _champs(mission: dict) -> list[str]:
    return [m["champ"] for m in revue_export.revue(mission)["manques"]]


def test_la_revue_signale_une_obligation_non_traitee():
    champs = _champs(_mission(_aipd("acceptable", ("DPO",))))
    assert any("avis des personnes concernées" in c.lower() for c in champs)


def test_la_revue_signale_un_risque_residuel_non_qualifie():
    champs = _champs(_mission(_aipd("non_evalue")))
    assert any("risque résiduel" in c for c in champs)


def test_la_revue_ne_reclame_pas_l_article_36_hors_risque_eleve():
    champs = _champs(_mission(_aipd("acceptable")))
    assert not any("CNIL avant mise en œuvre" in c for c in champs)


def test_la_revue_reclame_l_article_36_sur_risque_eleve():
    champs = _champs(_mission(_aipd("eleve", ("DPO", "PERSONNES", "LISTES_CNIL", "REEXAMEN"))))
    assert any("CNIL avant mise en œuvre" in c for c in champs)


def test_les_obligations_ne_sont_pas_reclamees_si_l_aipd_n_est_pas_requise():
    mission = _mission(_aipd("non_evalue"))
    mission["steps"]["diagnostic"]["aipd_required"] = False
    assert not any(c.startswith("AIPD") for c in _champs(mission))


# --- Livrable ---------------------------------------------------------------

def test_le_livrable_expose_les_obligations_et_leurs_articles():
    markdown = report_builder._obligations_aipd_md(_aipd("acceptable", ("DPO",)))
    assert "RGPD Art. 35 §2" in markdown
    assert "Fait" in markdown


def test_le_livrable_montre_ce_qui_reste_du():
    """Un rapport qui tairait les manques laisserait croire la démarche
    achevée — c'est exactement ce que la promesse « zéro invention » interdit."""
    markdown = report_builder._obligations_aipd_md(_aipd("acceptable"))
    assert "Reste à faire" in markdown


def test_le_livrable_marque_l_article_36_non_applicable_quand_il_ne_l_est_pas():
    markdown = report_builder._obligations_aipd_md(_aipd("acceptable"))
    assert "Non applicable" in markdown


def test_le_livrable_porte_l_avertissement_bloquant():
    markdown = report_builder._obligations_aipd_md(_aipd("eleve"))
    assert "ne peut pas être mis en œuvre" in markdown


def test_un_commentaire_multiligne_ne_casse_pas_le_tableau_markdown():
    donnees = _aipd("acceptable", ("DPO",))
    donnees["obligations"][0]["commentaire"] = "Avis rendu\nle 12/06 | favorable"
    ligne = [l for l in report_builder._obligations_aipd_md(donnees).splitlines() if "Art. 35 §2" in l][0]
    assert ligne.count("|") == 5
