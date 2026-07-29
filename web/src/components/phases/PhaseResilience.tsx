import { CheckCircle2 } from "lucide-react";
import type { ManualControl, ProjectState } from "../../types";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
}

/** Phase 5 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici. */
export function PhaseResilience({ activeProject, updateStepData, handleSaveProject }: Props) {


  return (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <CheckCircle2 size={15} /> 5. Préparation à la Crise, Continuité &amp; Diagnostic de Conformité
                </div>

                {/* MANUAL GRC CHECKLIST FOR THE SELECTED FRAMEWORK */}
                {activeProject.type === "grc" && (
                  <div className="flex flex-col gap-3">
                    <div className="text-xs font-bold text-[var(--sky)] mb-1">Check-list d'Audit Organisationnel ({activeProject.steps.cadrage?.framework_name})</div>
                    <div className="flex flex-col gap-2.5 max-h-[250px] overflow-y-auto pr-1">
                      {activeProject.steps.evaluation?.manual_controls?.map((ctrl: ManualControl, idx: number) => (
                        <div key={ctrl.id} className="bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] flex flex-col gap-2 animate-fade-in">
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs">
                            <div>
                              <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-2">{ctrl.id}</span>
                              <span className="font-bold text-[var(--ink)]">{ctrl.title}</span>
                              <p className="text-[10px] text-[var(--soft)] mt-0.5">{ctrl.description}</p>
                            </div>
                            
                            <div className="flex gap-1.5 self-start md:self-center">
                              <button
                                type="button"
                                onClick={() => {
                                  const list = [...(activeProject.steps.evaluation?.manual_controls || [])];
                                  list[idx].status = "CONFORME";
                                  updateStepData("evaluation", "manual_controls", list);
                                }}
                                className={`px-2 py-0.5 rounded text-[9px] font-bold transition ${ctrl.status === "CONFORME" ? "bg-[rgba(46,230,160,0.15)] text-[var(--g1)]" : "bg-white/[0.03] text-[var(--soft)]"}`}
                              >
                                Conforme
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  const list = [...(activeProject.steps.evaluation?.manual_controls || [])];
                                  list[idx].status = "NON_CONFORME";
                                  updateStepData("evaluation", "manual_controls", list);
                                }}
                                className={`px-2 py-0.5 rounded text-[9px] font-bold transition ${ctrl.status === "NON_CONFORME" ? "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]" : "bg-white/[0.03] text-[var(--soft)]"}`}
                              >
                                Non conforme
                              </button>
                            </div>
                          </div>
                          <input
                            type="text"
                            placeholder="Observations, constats, preuves d'audit..."
                            value={ctrl.notes}
                            onChange={(e) => {
                              const list = [...(activeProject.steps.evaluation?.manual_controls || [])];
                              list[idx].notes = e.target.value;
                              updateStepData("evaluation", "manual_controls", list);
                            }}
                            className="w-full bg-white/[0.03] border border-white/5 rounded-lg px-2 py-0.5 text-[10px] focus:outline-none"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cibles de continuité — RTO/RPO.
                    Ces champs étaient remplis par défaut et repris dans les
                    livrables PSSI/PRI, mais aucun écran ne les affichait : le
                    consultant exportait des cibles temporelles qu'il n'avait
                    jamais vues ni validées. */}
                <div className="mt-2 border-t border-white/[0.04] pt-3">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">
                    Cibles de continuité (reprises dans le livrable PSSI / PRI)
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[10px] font-bold text-[var(--sky)] mb-1" htmlFor="bcp-rto">
                        RTO — durée maximale d'interruption admissible
                      </label>
                      <input
                        id="bcp-rto"
                        type="text"
                        placeholder="ex : 4 heures"
                        value={activeProject.steps.resilience?.bcp_strategy?.rto || ""}
                        onChange={(e) => {
                          const bcp = { ...activeProject.steps.resilience?.bcp_strategy, rto: e.target.value };
                          updateStepData("resilience", "bcp_strategy", bcp);
                        }}
                        className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-[var(--sky)] mb-1" htmlFor="bcp-rpo">
                        RPO — perte de données maximale admissible
                      </label>
                      <input
                        id="bcp-rpo"
                        type="text"
                        placeholder="ex : 1 heure"
                        value={activeProject.steps.resilience?.bcp_strategy?.rpo || ""}
                        onChange={(e) => {
                          const bcp = { ...activeProject.steps.resilience?.bcp_strategy, rpo: e.target.value };
                          updateStepData("resilience", "bcp_strategy", bcp);
                        }}
                        className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-[var(--sky)] mb-1" htmlFor="bcp-sauvegarde">
                        Politique de sauvegarde
                      </label>
                      <input
                        id="bcp-sauvegarde"
                        type="text"
                        placeholder="ex : snapshots immuables, 3-2-1"
                        value={activeProject.steps.resilience?.bcp_strategy?.backup_policy || ""}
                        onChange={(e) => {
                          const bcp = { ...activeProject.steps.resilience?.bcp_strategy, backup_policy: e.target.value };
                          updateStepData("resilience", "bcp_strategy", bcp);
                        }}
                        className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                      />
                    </div>
                  </div>
                </div>

                {/* Séquence E3R de l'ANSSI */}
                <div className="mt-2 border-t border-white/[0.04] pt-3">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">Séquence de remédiation cyber E3R de l'ANSSI</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <span className="block text-[10px] font-bold text-[var(--rose)] mb-1">E1 - Endiguement (Isolement d'urgence)</span>
                      <textarea
                        rows={2}
                        value={activeProject.steps.resilience?.e3r?.endiguement || ""}
                        onChange={(e) => {
                          const e3r = { ...activeProject.steps.resilience?.e3r, endiguement: e.target.value };
                          updateStepData("resilience", "e3r", e3r);
                        }}
                        className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2 text-xs focus:outline-none"
                      />
                    </div>
                    <div>
                      <span className="block text-[10px] font-bold text-[var(--g1)] mb-1">R - Reconstruction (IaC &amp; Durcissement)</span>
                      <textarea
                        rows={2}
                        value={activeProject.steps.resilience?.e3r?.reconstruction || ""}
                        onChange={(e) => {
                          const e3r = { ...activeProject.steps.resilience?.e3r, reconstruction: e.target.value };
                          updateStepData("resilience", "e3r", e3r);
                        }}
                        className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2 text-xs focus:outline-none"
                      />
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
                      checked={activeProject.steps.resilience?.validated || false}
                      onChange={(e) => {
                        updateStepData("resilience", "validated", e.target.checked);
                        setTimeout(() => handleSaveProject(), 100);
                      }}
                      className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                    />
                    Étape 5 (Résilience &amp; E3R) validée
                  </label>
                </div>

              </div>
  );
}
