import { useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, PlusCircle, RefreshCw, Trash2 } from "lucide-react";
import { api } from "../../lib/api";
import type { ExigenceTiers, ProjectState, Tiers } from "../../types";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
  /** Les routes TPRM écrivent côté serveur et renvoient la mission entière. */
  onProjectReplaced: (state: ProjectState) => void;
}

const CURSEURS = [
  { cle: "dependence", libelle: "Dépendance opérationnelle", accent: "var(--g1)" },
  { cle: "penetration", libelle: "Pénétration dans notre SI", accent: "var(--g3)" },
  { cle: "maturity", libelle: "Maturité Cyber estimée", accent: "var(--sky)" },
  { cle: "trust", libelle: "Niveau de Confiance historique", accent: "var(--g1)" },
] as const;

const VIDE = { name: "", dependence: 3, penetration: 3, maturity: 3, trust: 3 };

const COULEUR_RATING: Record<string, string> = {
  Critique: "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]",
  "Élevé": "bg-[rgba(255,207,107,0.15)] text-[var(--amber)]",
  Moyen: "bg-[rgba(92,200,255,0.15)] text-[var(--sky)]",
};

/** Phase 3 du parcours de mission.
 *
 *  Scindée selon le volet (§14.1bis) : le volet Consulting classe les tiers par
 *  ratio ANSSI (exposition / fiabilité cyber), le volet GRC leur oppose des
 *  exigences DORA/NIS2 vérifiables — ces référentiels ne se réclamant pas
 *  d'EBIOS RM, leur appliquer un score de risque inventerait une exigence
 *  qu'ils ne portent pas.
 */
export function PhaseTprm({ activeProject, updateStepData, handleSaveProject, onProjectReplaced }: Props) {
  const [newTiers, setNewTiers] = useState(VIDE);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState("");

  const estGrc = activeProject.type === "grc";
  const tiers = activeProject.steps.tprm?.tiers || [];
  const aRecalculer = !estGrc && tiers.filter((t) => t.methode !== "ratio_anssi");

  const addTiers = async () => {
    if (!newTiers.name.trim() || enCours) return;
    setEnCours(true);
    setErreur("");
    try {
      onProjectReplaced(await api.projects.addTiers(activeProject.id, newTiers));
      setNewTiers(VIDE);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Ajout impossible.");
    } finally {
      setEnCours(false);
    }
  };

  const basculerExigence = async (index: number, exigence: ExigenceTiers) => {
    setErreur("");
    try {
      onProjectReplaced(
        await api.projects.setExigenceTiers(activeProject.id, index, exigence.id, {
          satisfait: !exigence.satisfait,
          preuve: exigence.preuve,
        }),
      );
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Mise à jour impossible.");
    }
  };

  const recalculer = async () => {
    setEnCours(true);
    setErreur("");
    try {
      const res = await api.projects.recalculerTprm(activeProject.id);
      onProjectReplaced(res.state);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Recalcul impossible.");
    } finally {
      setEnCours(false);
    }
  };

  const supprimer = (idx: number) => {
    const liste = [...tiers];
    liste.splice(idx, 1);
    updateStepData("tprm", "tiers", liste);
  };

  const compte = (rating: string) => tiers.filter((t) => t.rating === rating).length;
  const conformes = tiers.filter(
    (t) => (t.exigences?.length ?? 0) > 0 && t.exigences!.every((e) => e.satisfait),
  ).length;

  return (
    <div className="flex flex-col gap-4">
      <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
        <Activity size={15} /> 3. Évaluation de l'Écosystème &amp; des Risques Tiers (TPRM / NIST ID.RA-10)
      </div>

      <p className="text-xs text-[var(--soft)]">
        {estGrc
          ? "Cartographiez les prestataires du client, puis vérifiez pour chacun les exigences DORA / NIS2 applicables. Ce volet ne produit pas de score de risque : la conformité se démontre par des preuves, pas par une note."
          : "Cartographiez les clients, sous-traitants, hébergeurs et infogéreurs du client. La criticité suit la formule ANSSI (dépendance × pénétration) / (maturité × confiance) : l'exposition rapportée à la fiabilité cyber du tiers."}
      </p>

      {erreur && (
        <div className="text-[11px] text-[var(--rose)] bg-[rgba(255,111,145,0.08)] border border-[rgba(255,111,145,0.2)] rounded-xl px-3 py-2">
          {erreur}
        </div>
      )}

      {/* Bandeau de migration : le recalcul est proposé, jamais imposé — une
          criticité a pu être présentée au client sous l'ancienne méthode. */}
      {aRecalculer && aRecalculer.length > 0 && (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[rgba(255,207,107,0.06)] border border-[rgba(255,207,107,0.2)] rounded-xl px-3 py-2.5">
          <span className="text-[11px] text-[var(--amber)] flex items-start gap-2">
            <AlertTriangle size={13} className="flex-shrink-0 mt-0.5" />
            <span>
              {aRecalculer.length} tiers {aRecalculer.length > 1 ? "sont notés" : "est noté"} selon l'ancienne
              moyenne. Le recalcul modifiera {aRecalculer.length > 1 ? "leurs criticités" : "sa criticité"} —
              un instantané est pris avant.
            </span>
          </span>
          <button
            type="button"
            onClick={recalculer}
            disabled={enCours}
            className="px-3 py-1.5 bg-[var(--amber)] text-[#04150e] font-bold rounded-xl text-[11px] hover:opacity-90 flex items-center gap-1.5 flex-shrink-0 disabled:opacity-50"
          >
            <RefreshCw size={12} /> Recalculer au ratio ANSSI
          </button>
        </div>
      )}

      <div className="flex flex-col gap-2">
        {tiers.map((t: Tiers, idx: number) => (
          <div
            key={idx}
            className="bg-white/[0.02] p-3 rounded-xl border border-white/[0.05] flex flex-col md:flex-row md:items-start justify-between gap-3 text-xs"
          >
            <div className="flex-1">
              <div className="font-bold text-[var(--ink)] text-sm flex items-center gap-2 flex-wrap">
                {t.name}
                {!estGrc && (
                  <span className={`text-[9px] font-extrabold rounded-full px-2 py-0.5 ${COULEUR_RATING[t.rating] ?? "bg-white/10 text-[var(--soft)]"}`}>
                    {t.rating} (ratio {t.score})
                  </span>
                )}
                {!estGrc && t.methode !== "ratio_anssi" && (
                  <span className="text-[9px] font-bold rounded-full px-2 py-0.5 bg-white/5 text-[var(--faint)]">
                    ancienne méthode
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[10px] text-[var(--soft)] mt-1.5">
                <span>Dépendance : <strong className="text-[var(--ink)]">{t.dependence}/5</strong></span>
                <span>Pénétration SI : <strong className="text-[var(--ink)]">{t.penetration}/5</strong></span>
                <span>Maturité Cyber : <strong className="text-[var(--ink)]">{t.maturity}/5</strong></span>
                <span>Niveau Confiance : <strong className="text-[var(--ink)]">{t.trust}/5</strong></span>
              </div>

              {estGrc && (
                <div className="flex flex-col gap-1 mt-2.5 border-t border-white/[0.04] pt-2">
                  {(t.exigences || []).map((e) => (
                    <label key={e.id} className="flex items-start gap-2 cursor-pointer text-[10px] text-[var(--soft)]">
                      <input
                        type="checkbox"
                        checked={e.satisfait}
                        onChange={() => basculerExigence(idx, e)}
                        className="mt-0.5 rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                      />
                      <span className={e.satisfait ? "text-[var(--g1)]" : ""}>{e.libelle}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={() => supprimer(idx)}
              className="text-[var(--rose)] hover:bg-white/5 p-1.5 rounded-lg self-end md:self-center"
              aria-label={`Supprimer le tiers ${t.name}`}
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-4 rounded-xl text-xs">
        <div className="md:col-span-3">
          <label htmlFor="tprm-nom" className="block text-[11px] font-bold text-[var(--soft)] mb-1">
            Nom du tiers / Fournisseur critique
          </label>
          <input
            id="tprm-nom"
            type="text"
            placeholder="ex: Infogéreur DevOps, AWS, Cabinet Comptable"
            value={newTiers.name}
            onChange={(e) => setNewTiers({ ...newTiers, name: e.target.value })}
            className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
          />
        </div>

        {CURSEURS.map(({ cle, libelle, accent }, i) => (
          <div key={cle} className={`flex flex-col gap-1${i === CURSEURS.length - 1 ? " md:col-span-3" : ""}`}>
            <label htmlFor={`tprm-${cle}`} className="text-[10px] font-bold text-[var(--soft)] flex justify-between">
              <span>{libelle} :</span>
              <strong style={{ color: accent }}>{newTiers[cle]}/5</strong>
            </label>
            <input
              id={`tprm-${cle}`}
              type="range"
              min="1"
              max="5"
              value={newTiers[cle]}
              onChange={(e) => setNewTiers({ ...newTiers, [cle]: parseInt(e.target.value) })}
              style={{ accentColor: accent }}
            />
          </div>
        ))}

        <div className="md:col-span-3 flex justify-end">
          <button
            type="button"
            onClick={addTiers}
            disabled={enCours}
            className="px-4 py-2 bg-[var(--g1)] text-[#04150e] font-bold rounded-xl text-xs hover:opacity-90 flex items-center gap-1 disabled:opacity-50"
          >
            <PlusCircle size={14} /> {estGrc ? "Ajouter au registre" : "Enregistrer et évaluer"}
          </button>
        </div>
      </div>

      <div className="glass-2 p-4 flex flex-col gap-2 mt-2">
        <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">
          {estGrc ? "Métrique : Conformité du registre des prestataires" : "Métrique : Répartition de la Criticité Tiers"}
        </span>

        {estGrc ? (
          <div className="flex items-center gap-4 h-[50px] mt-1">
            <div className="flex-1 h-3.5 rounded-full overflow-hidden flex bg-white/[0.03]">
              <div
                className="bg-[var(--g1)] h-full"
                style={{ width: `${(conformes / (tiers.length || 1)) * 100}%` }}
                title="Conformes"
              />
            </div>
            <span className="text-[10px] text-[var(--soft)] flex-shrink-0">
              {conformes} / {tiers.length} prestataire(s) sans écart
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-4 h-[50px] mt-1">
            <div className="flex-1 h-3.5 rounded-full overflow-hidden flex bg-white/[0.03]">
              {(["Critique", "Élevé", "Moyen", "Faible"] as const).map((r) => (
                <div
                  key={r}
                  className={
                    r === "Critique" ? "bg-[var(--rose)] h-full"
                      : r === "Élevé" ? "bg-[var(--amber)] h-full"
                        : r === "Moyen" ? "bg-[var(--sky)] h-full" : "bg-white/10 h-full"
                  }
                  style={{ width: `${(compte(r) / (tiers.length || 1)) * 100}%` }}
                  title={r}
                />
              ))}
            </div>
            <div className="flex gap-3 text-[10px] flex-wrap">
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--rose)]" /> Critique ({compte("Critique")})</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--amber)]" /> Élevé ({compte("Élevé")})</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--sky)]" /> Moyen ({compte("Moyen")})</span>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-white/[0.04] pt-4 mt-2 flex justify-between items-center bg-white/[0.01] p-3 rounded-2xl flex-wrap gap-2">
        <span className="text-xs text-[var(--soft)] flex items-center gap-1.5">
          <CheckCircle2 size={13} className="text-[var(--g1)] flex-shrink-0" /> Validez pour faire progresser la jauge de la mission.
        </span>
        <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--g1)] flex-shrink-0">
          <input
            type="checkbox"
            checked={activeProject.steps.tprm?.validated || false}
            onChange={(e) => {
              updateStepData("tprm", "validated", e.target.checked);
              setTimeout(() => handleSaveProject(), 100);
            }}
            className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
          />
          Étape 3 (Risques Tiers / TPRM) validée
        </label>
      </div>
    </div>
  );
}
