import { useState } from "react";
import { Activity, CheckCircle2, PlusCircle, Trash2 } from "lucide-react";
import type { ProjectState, Tiers } from "../../types";


interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
}

/** Phase 3 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici. */
export function PhaseTprm({ activeProject, updateStepData, handleSaveProject }: Props) {
  const [newTiers, setNewTiers] = useState({ name: "", dependence: 3, penetration: 3, maturity: 3, trust: 3 });

  const addTiersHelper = () => {
    if (!newTiers.name.trim()) return;
    const score = parseFloat(((newTiers.dependence + newTiers.penetration + (6 - newTiers.maturity) + (6 - newTiers.trust)) / 4).toFixed(1));
    let rating: "Critique" | "Élevé" | "Moyen" | "Faible" = "Faible";
    if (score >= 4.0) rating = "Critique";
    else if (score >= 3.0) rating = "Élevé";
    else if (score >= 2.0) rating = "Moyen";
    
    const list = [...(activeProject.steps.tprm?.tiers || [])];
    list.push({ ...newTiers, score, rating });
    updateStepData("tprm", "tiers", list);
    setNewTiers({ name: "", dependence: 3, penetration: 3, maturity: 3, trust: 3 });
  };

  return (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <Activity size={15} /> 3. Évaluation de l'Écosystème &amp; des Risques Tiers (TPRM / NIST ID.RA-10)
                </div>
                
                <p className="text-xs text-[var(--soft)]">
                  Cartographiez les clients, sous-traitants, hébergeurs et infogéreurs du client, puis évaluez leur criticité cyber de manière pondérée.
                </p>

                {/* TPRM TABLE */}
                <div className="flex flex-col gap-2">
                  {activeProject.steps.tprm?.tiers?.map((t: Tiers, idx: number) => (
                    <div key={idx} className="bg-white/[0.02] p-3 rounded-xl border border-white/[0.05] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                      <div>
                        <div className="font-bold text-[var(--ink)] text-sm flex items-center gap-2">
                          {t.name}
                          <span className={`text-[9px] font-extrabold rounded-full px-2 py-0.5 ${
                            t.rating === "Critique" ? "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]" :
                            t.rating === "Élevé" ? "bg-[rgba(255,207,107,0.15)] text-[var(--amber)]" :
                            t.rating === "Moyen" ? "bg-[rgba(92,200,255,0.15)] text-[var(--sky)]" : "bg-white/10 text-[var(--soft)]"
                          }`}>
                            {t.rating} ({t.score}/5)
                          </span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[10px] text-[var(--soft)] mt-1.5">
                          <span>Dépendance : <strong className="text-[var(--ink)]">{t.dependence}/5</strong></span>
                          <span>Pénétration SI : <strong className="text-[var(--ink)]">{t.penetration}/5</strong></span>
                          <span>Maturité Cyber : <strong className="text-[var(--ink)]">{t.maturity}/5</strong></span>
                          <span>Niveau Confiance : <strong className="text-[var(--ink)]">{t.trust}/5</strong></span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          const list = [...(activeProject.steps.tprm?.tiers || [])];
                          list.splice(idx, 1);
                          updateStepData("tprm", "tiers", list);
                        }}
                        className="text-[var(--rose)] hover:bg-white/5 p-1.5 rounded-lg self-end md:self-center"
                        aria-label={`Supprimer le tiers ${t.name}`}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Add Tiers Form WITH EXPLICIT SLIDER LABELS */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-4 rounded-xl text-xs">
                  <div className="md:col-span-3">
                    <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Nom du tiers / Fournisseur critique</label>
                    <input
                      type="text"
                      placeholder="ex: Infogéreur DevOps, AWS, Cabinet Comptable"
                      value={newTiers.name}
                      onChange={(e) => setNewTiers({ ...newTiers, name: e.target.value })}
                      className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                    />
                  </div>
                  
                  {/* Sliders with explicit value numbers on UI */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-[var(--soft)] flex justify-between">
                      <span>Dépendance opérationnelle :</span> <strong className="text-[var(--g1)]">{newTiers.dependence}/5</strong>
                    </span>
                    <input
                      type="range" min="1" max="5" value={newTiers.dependence}
                      onChange={(e) => setNewTiers({ ...newTiers, dependence: parseInt(e.target.value) })}
                      className="accent-[var(--g1)]"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-[var(--soft)] flex justify-between">
                      <span>Pénétration dans notre SI :</span> <strong className="text-[var(--g3)]">{newTiers.penetration}/5</strong>
                    </span>
                    <input
                      type="range" min="1" max="5" value={newTiers.penetration}
                      onChange={(e) => setNewTiers({ ...newTiers, penetration: parseInt(e.target.value) })}
                      className="accent-[var(--g3)]"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-[var(--soft)] flex justify-between">
                      <span>Maturité Cyber estimée :</span> <strong className="text-[var(--sky)]">{newTiers.maturity}/5</strong>
                    </span>
                    <input
                      type="range" min="1" max="5" value={newTiers.maturity}
                      onChange={(e) => setNewTiers({ ...newTiers, maturity: parseInt(e.target.value) })}
                      className="accent-[var(--sky)]"
                    />
                  </div>
                  <div className="flex flex-col gap-1 md:col-span-3">
                    <span className="text-[10px] font-bold text-[var(--soft)] flex justify-between">
                      <span>Niveau de Confiance historique :</span> <strong className="text-[var(--g1)]">{newTiers.trust}/5</strong>
                    </span>
                    <input
                      type="range" min="1" max="5" value={newTiers.trust}
                      onChange={(e) => setNewTiers({ ...newTiers, trust: parseInt(e.target.value) })}
                      className="accent-[var(--g1)]"
                    />
                  </div>

                  <div className="md:col-span-3 flex justify-end">
                    <button
                      type="button"
                      onClick={addTiersHelper}
                      className="px-4 py-2 bg-[var(--g1)] text-[#04150e] font-bold rounded-xl text-xs hover:opacity-90 flex items-center gap-1"
                    >
                      <PlusCircle size={14} /> Enregistrer et évaluer
                    </button>
                  </div>
                </div>

                {/* GRAPHICAL KPI CHART SUMMARY (SVG) */}
                <div className="glass-2 p-4 flex flex-col gap-2 mt-2">
                  <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">Métrique : Répartition de la Criticité Tiers</span>
                  <div className="flex items-center gap-4 h-[50px] mt-1">
                    <div className="flex-1 h-3.5 rounded-full overflow-hidden flex bg-white/[0.03]">
                      <div className="bg-[var(--rose)] h-full" style={{ width: `${((activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Critique").length || 0) / (activeProject.steps.tprm?.tiers?.length || 1)) * 100}%` }} title="Critique" />
                      <div className="bg-[var(--amber)] h-full" style={{ width: `${((activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Élevé").length || 0) / (activeProject.steps.tprm?.tiers?.length || 1)) * 100}%` }} title="Élevé" />
                      <div className="bg-[var(--sky)] h-full" style={{ width: `${((activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Moyen").length || 0) / (activeProject.steps.tprm?.tiers?.length || 1)) * 100}%` }} title="Moyen" />
                      <div className="bg-white/10 h-full" style={{ width: `${((activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Faible").length || 0) / (activeProject.steps.tprm?.tiers?.length || 1)) * 100}%` }} title="Faible" />
                    </div>
                    <div className="flex gap-3 text-[10px]">
                      <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--rose)]" /> Critique ({activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Critique").length || 0})</span>
                      <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--amber)]" /> Élevé ({activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Élevé").length || 0})</span>
                      <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--sky)]" /> Moyen ({activeProject.steps.tprm?.tiers?.filter(t => t.rating === "Moyen").length || 0})</span>
                    </div>
                  </div>
                </div>

                {/* STEP EXPLICIT CONFIRMATION BUTTON */}
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
