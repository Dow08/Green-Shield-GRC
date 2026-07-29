import { AlertCircle, Award, BookOpen, CheckCircle2, RefreshCw, Shield } from "lucide-react";
import type { ProjectState } from "../../types";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
  handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleTriggerAudit: () => void;
  uploading: boolean;
  auditing: boolean;
}

/** Phase 4 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici. */
export function PhaseEbios({ activeProject, updateStepData, handleSaveProject, handleFileUpload, handleTriggerAudit, uploading, auditing }: Props) {


  return (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <Award size={15} /> 4. Analyse des Menaces EBIOS RM &amp; Scan Réel de Configuration
                </div>

                {/* GRC ACTIVE SCANS AND GENUINE TARGET AUDITS (SHIELD) */}
                <div className="glass p-4 border border-[var(--stroke)] flex flex-col gap-3">
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <div>
                      <h4 className="font-bold text-xs text-[var(--ink)] flex items-center gap-1.5">
                        <Shield size={14} className="text-[var(--g1)]" /> Audit Réel de Configuration (AuditCraft)
                      </h4>
                      <p className="text-[11px] text-[var(--soft)] mt-0.5">
                        Importez vos configurations réelles (`sshd_config`, `nginx.conf`) pour faire une analyse statique factuelle de sécurité en temps réel.
                      </p>
                    </div>
                    <div className="flex gap-2 ml-auto flex-shrink-0">
                      <input type="file" onChange={handleFileUpload} disabled={uploading} className="hidden" id="grc-upload-ph4" />
                      <label htmlFor="grc-upload-ph4" className="cursor-pointer bg-white/[0.04] hover:bg-white/[0.08] px-3.5 py-1.5 rounded-xl border border-[var(--stroke)] text-xs font-bold transition">
                        {uploading ? "Importation..." : "Importer config client"}
                      </label>
                      <button
                        onClick={handleTriggerAudit}
                        disabled={auditing || activeProject.steps.collecte?.files?.length === 0}
                        className="px-3.5 py-1.5 bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] text-[#04150e] font-bold rounded-xl text-xs hover:opacity-90 transition flex items-center gap-1"
                      >
                        <RefreshCw size={13} className={auditing ? "animate-spin" : ""} /> {auditing ? "Analyse..." : "Lancer le scan"}
                      </button>
                    </div>
                  </div>

                  {/* Inform if targets are missing */}
                  {(!activeProject.steps.collecte?.files || activeProject.steps.collecte.files.length === 0) && (
                    <div className="text-xs text-[var(--amber)] bg-[rgba(255,207,107,0.06)] border border-dashed border-[rgba(255,207,107,0.3)] p-3 rounded-xl flex items-center gap-2">
                      <AlertCircle size={14} /> Aucun fichier de configuration n'est déposé. Pour tester l'analyseur sur des fichiers réels vulnérables, déposez les fichiers du lab (ex: `sshd_config` de `lab_target`).
                    </div>
                  )}

                  {/* Tech results representation with lines of code */}
                  {activeProject.steps.evaluation?.technical_results && (
                    <div className="flex flex-col gap-2.5 bg-white/[0.02] p-3 rounded-xl border border-white/[0.03]">
                      <div className="flex items-center gap-3">
                        <div className="text-xs font-bold text-[var(--g1)]">
                          Score de Conformité Technique : {activeProject.steps.evaluation.technical_results.score}% ({activeProject.steps.evaluation.technical_results.band})
                        </div>
                        <span className="text-[10px] text-[var(--soft)]">
                          · {activeProject.steps.evaluation.technical_results.critical_count} failles critiques identifiées
                        </span>
                      </div>
                      
                      {/* Technical checklist details */}
                      <div className="flex flex-col gap-1.5 max-h-[160px] overflow-y-auto pr-1 border-t border-white/[0.04] pt-2">
                        {activeProject.steps.evaluation.technical_results.controls?.map((c, idx) => (
                          <div key={idx} className="flex justify-between items-center text-[10px] bg-white/[0.01] p-1.5 rounded animate-fade-in">
                            <span className="font-mono text-[var(--soft)]">{c.file} ➔ {c.key}</span>
                            <span className={`font-bold px-2 py-0.5 rounded text-[9px] ${
                              c.status === "CONFORME" ? "bg-[rgba(46,230,160,0.12)] text-[var(--g1)]" : "bg-[rgba(255,111,145,0.12)] text-[var(--rose)]"
                            }`}>
                              {c.status === "CONFORME" ? "Conforme" : "Écart"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* EVENEMENTS REDOUTES & SCENARIOS */}
                <div className="mt-2 border-t border-white/[0.04] pt-3 grid grid-cols-1 lg:grid-cols-3 gap-4">
                  
                  {/* Heatmap matrix SVG */}
                  <div className="lg:col-span-1 glass-2 p-3 flex flex-col items-center justify-center">
                    <span className="text-[10px] font-bold text-[var(--faint)] mb-2 uppercase">Grille Gravité × Vraisemblance (EBIOS RM)</span>
                    <svg width="180" height="150" className="border border-white/5 bg-[#030d08]">
                      {Array.from({ length: 4 }).map((_, r) => (
                        Array.from({ length: 5 }).map((_, c) => {
                          const gravity = 4 - r;
                          const likelihood = c + 1;
                          const count = activeProject.steps.ebios?.operational_scenarios?.filter(s => s.gravity === gravity && s.likelihood === likelihood).length || 0;
                          let cellColor = "rgba(46,230,160,0.05)";
                          if (gravity * likelihood >= 12) cellColor = "rgba(255,111,145,0.3)";
                          else if (gravity * likelihood >= 6) cellColor = "rgba(255,207,107,0.18)";

                          return (
                            <g key={`${r}-${c}`}>
                              <rect x={c * 35 + 5} y={r * 32 + 5} width="30" height="27" fill={cellColor} stroke="rgba(255,255,255,0.03)" />
                              {count > 0 && <circle cx={c * 35 + 20} cy={r * 32 + 18} r="8" fill={gravity * likelihood >= 12 ? "#ff6f91" : gravity * likelihood >= 6 ? "#ffcf6b" : "#2ee6a0"} />}
                              {count > 0 && <text x={c * 35 + 20} y={r * 32 + 21} textAnchor="middle" fontSize="8" fontWeight="bold" fill="#04150e">{count}</text>}
                            </g>
                          );
                        })
                      ))}
                    </svg>
                  </div>

                  {/* Scenarios lists with optional-chaining mapping to prevent crashes */}
                  <div className="lg:col-span-2 flex flex-col gap-2 max-h-[150px] overflow-y-auto">
                    {activeProject.steps.ebios?.operational_scenarios?.map((s, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] p-2 rounded-xl border border-white/[0.05] text-[11px] flex justify-between items-center">
                        <div>
                          <span className="font-mono text-[var(--g3)] mr-2">{s.id}</span>
                          <span className="font-bold text-[var(--ink)]">{s.event}</span>
                        </div>
                        <span className="bg-white/5 rounded px-2 py-0.5 text-[9px] text-[var(--soft)]">G:{s.gravity} · V:{s.likelihood}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* CASE STUDIES REFLEXES */}
                <div className="mt-1 border-t border-white/[0.04] pt-2">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">C. Fiches de Décision &amp; Retours d'Expérience Réels (REX)</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {activeProject.steps.ebios?.case_studies?.map((c, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] border border-white/5 rounded-xl p-3 text-xs animate-fade-in">
                        <div className="font-bold text-[var(--sky)] mb-1 flex items-center gap-1">
                          <BookOpen size={12} /> {c.case}
                        </div>
                        <p className="text-[11px] text-[var(--soft)] leading-normal">{c.lessons}</p>
                      </div>
                    ))}
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
                      checked={activeProject.steps.ebios?.validated || false}
                      onChange={(e) => {
                        updateStepData("ebios", "validated", e.target.checked);
                        setTimeout(() => handleSaveProject(), 100);
                      }}
                      className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                    />
                    Étape 4 (Analyse des Menaces) validée
                  </label>
                </div>

              </div>
  );
}
