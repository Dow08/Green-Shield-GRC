import { useState } from "react";
import { AlertCircle, Award, BookOpen, CheckCircle2, Gauge, Plus, RefreshCw, Shield, Trash2 } from "lucide-react";
import { nextId } from "../../lib/ids";
import type { CouvertureTechnique, ProjectState, RedouteEvent, RiskSource, OperationalScenario, CaseStudy } from "../../types";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
  handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleTriggerAudit: () => void;
  uploading: boolean;
  auditing: boolean;
  couverture: CouvertureTechnique | null;
}

const _NOUVEL_EVENEMENT: RedouteEvent = { id: "", event: "", gravity: 3, impact: "" };
const _NOUVELLE_SOURCE: RiskSource = { id: "", name: "", objective: "" };
const _NOUVEAU_SCENARIO: OperationalScenario = {
  id: "", event: "", gravity: 3, likelihood: 3, mitigation: "",
  actif_concerne: "", gravite_residuelle: undefined, vraisemblance_residuelle: undefined,
  strategie_traitement: "", owner: "", date_revue: "", statut: "",
};
const _NOUVEAU_CAS: CaseStudy = { case: "", lessons: "" };

/** Phase 4 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici.
 *
 *  CRUD des 4 collections EBIOS RM ajouté le 30/07/2026 : jusque-là seule la
 *  mission de démonstration en portait (données pré-remplies via
 *  `create_default_state`), aucun écran ne permettant à un consultant d'en
 *  saisir sur une mission réelle — l'analyse de risque était donc
 *  consultable, jamais réalisable de bout en bout. */
export function PhaseEbios({ activeProject, updateStepData, handleSaveProject, handleFileUpload, handleTriggerAudit, uploading, auditing, couverture }: Props) {
  const [newEvenement, setNewEvenement] = useState<RedouteEvent>(_NOUVEL_EVENEMENT);
  const [newSource, setNewSource] = useState<RiskSource>(_NOUVELLE_SOURCE);
  const [newScenario, setNewScenario] = useState<OperationalScenario>(_NOUVEAU_SCENARIO);
  const [newCas, setNewCas] = useState<CaseStudy>(_NOUVEAU_CAS);

  const evenements = activeProject.steps.ebios?.redoute_events || [];
  const sources = activeProject.steps.ebios?.risk_sources || [];
  const scenarios = activeProject.steps.ebios?.operational_scenarios || [];
  const casReels = activeProject.steps.ebios?.case_studies || [];

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

                      {/* Taux de couverture (F10) : dire quelle part de l'audit
                          repose sur une mesure automatisée plutôt que sur du
                          déclaratif. Aucun concurrent n'affiche cette métrique —
                          la taire serait une survente. */}
                      {couverture && (
                        <div className="text-[10px] text-[var(--soft)] bg-white/[0.02] border border-white/[0.04] rounded-lg px-2.5 py-1.5 flex items-start gap-1.5">
                          <Gauge size={11} className="text-[var(--sky)] shrink-0 mt-0.5" />
                          <span>
                            <strong className="text-[var(--ink)]">
                              {couverture.controles_couverts}/{couverture.controles_total} contrôle(s) ({couverture.taux} %)
                            </strong>{" "}
                            appuyés par une preuve technique automatisée. Les autres reposent
                            sur des éléments déclaratifs — cette proportion figure aussi dans le rapport exporté.
                          </span>
                        </div>
                      )}

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

                {/* A. EVENEMENTS REDOUTES */}
                <div className="mt-2 border-t border-white/[0.04] pt-3">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">A. Événements Redoutés (Atelier 1)</div>
                  <div className="flex flex-col gap-2">
                    {evenements.map((e: RedouteEvent, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs flex justify-between items-center">
                        <div>
                          <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-2">{e.id}</span>
                          <span className="font-bold text-[var(--ink)]">{e.event}</span>
                          <span className="ml-2 text-[9px] font-extrabold rounded-full px-1.5 py-0.5 bg-white/5 text-[var(--soft)]">G:{e.gravity}</span>
                          {e.impact && <span className="text-[11px] text-[var(--soft)] ml-2">— {e.impact}</span>}
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const list = [...evenements]; list.splice(idx, 1);
                            updateStepData("ebios", "redoute_events", list);
                          }}
                          className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                          aria-label={`Supprimer l'événement redouté ${e.event}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mt-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
                    <input
                      type="text" placeholder="ID (ex: ER-05)" value={newEvenement.id}
                      onChange={(e) => setNewEvenement({ ...newEvenement, id: e.target.value })}
                      className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                    />
                    <input
                      type="text" placeholder="Événement redouté" value={newEvenement.event}
                      onChange={(e) => setNewEvenement({ ...newEvenement, event: e.target.value })}
                      className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                    />
                    <select
                      value={newEvenement.gravity}
                      onChange={(e) => setNewEvenement({ ...newEvenement, gravity: Number(e.target.value) })}
                      className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                    >
                      {[1, 2, 3, 4].map((g) => <option key={g} value={g}>Gravité {g}</option>)}
                    </select>
                    <div className="flex gap-2">
                      <input
                        type="text" placeholder="Impacts (financier, juridique...)" value={newEvenement.impact}
                        onChange={(e) => setNewEvenement({ ...newEvenement, impact: e.target.value })}
                        className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (!newEvenement.id.trim() || !newEvenement.event.trim()) return;
                          const list = [...evenements, newEvenement];
                          updateStepData("ebios", "redoute_events", list);
                          setNewEvenement({ ..._NOUVEL_EVENEMENT, id: nextId("ER", list.map((x) => x.id)) });
                        }}
                        className="bg-[var(--g1)] text-[#04150e] p-1.5 rounded-xl hover:opacity-90"
                      >
                        <Plus size={15} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* B. SOURCES DE RISQUE */}
                <div className="mt-1 border-t border-white/[0.04] pt-3">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">B. Sources de Risque &amp; Objectifs Visés (Atelier 2)</div>
                  <div className="flex flex-col gap-2">
                    {sources.map((s: RiskSource, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs flex justify-between items-center">
                        <div>
                          <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-2">{s.id}</span>
                          <span className="font-bold text-[var(--ink)]">{s.name}</span>
                          {s.objective && <span className="text-[11px] text-[var(--soft)] ml-2">— {s.objective}</span>}
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const list = [...sources]; list.splice(idx, 1);
                            updateStepData("ebios", "risk_sources", list);
                          }}
                          className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                          aria-label={`Supprimer la source de risque ${s.name}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
                    <input
                      type="text" placeholder="ID (ex: SR-03)" value={newSource.id}
                      onChange={(e) => setNewSource({ ...newSource, id: e.target.value })}
                      className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                    />
                    <input
                      type="text" placeholder="Source de risque (ex: Cybercriminels)" value={newSource.name}
                      onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                      className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                    />
                    <div className="flex gap-2">
                      <input
                        type="text" placeholder="Objectif visé" value={newSource.objective}
                        onChange={(e) => setNewSource({ ...newSource, objective: e.target.value })}
                        className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (!newSource.id.trim() || !newSource.name.trim()) return;
                          const list = [...sources, newSource];
                          updateStepData("ebios", "risk_sources", list);
                          setNewSource({ ..._NOUVELLE_SOURCE, id: nextId("SR", list.map((x) => x.id)) });
                        }}
                        className="bg-[var(--g1)] text-[#04150e] p-1.5 rounded-xl hover:opacity-90"
                      >
                        <Plus size={15} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* C. SCENARIOS OPERATIONNELS (registre de risques) */}
                <div className="mt-1 border-t border-white/[0.04] pt-3 grid grid-cols-1 lg:grid-cols-3 gap-4">

                  {/* Heatmap matrix SVG */}
                  <div className="lg:col-span-1 glass-2 p-3 flex flex-col items-center justify-center">
                    <span className="text-[10px] font-bold text-[var(--faint)] mb-2 uppercase">Grille Gravité × Vraisemblance (EBIOS RM)</span>
                    <svg width="180" height="150" className="border border-white/5 bg-[#030d08]">
                      {Array.from({ length: 4 }).map((_, r) => (
                        Array.from({ length: 5 }).map((_, c) => {
                          const gravity = 4 - r;
                          const likelihood = c + 1;
                          const count = scenarios.filter(s => s.gravity === gravity && s.likelihood === likelihood).length;
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
                  <div className="lg:col-span-2 flex flex-col gap-2 max-h-[220px] overflow-y-auto">
                    <span className="text-[10px] font-bold text-[var(--faint)] uppercase">C. Scénarios Opérationnels — registre de risques (Atelier 3/4)</span>
                    {scenarios.map((s: OperationalScenario, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-[11px] flex flex-col gap-1">
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="font-mono text-[var(--g3)] mr-2">{s.id}</span>
                            <span className="font-bold text-[var(--ink)]">{s.event}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="bg-white/5 rounded px-2 py-0.5 text-[9px] text-[var(--soft)]">G:{s.gravity} · V:{s.likelihood}</span>
                            <button
                              type="button"
                              onClick={() => {
                                const list = [...scenarios]; list.splice(idx, 1);
                                updateStepData("ebios", "operational_scenarios", list);
                              }}
                              className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                              aria-label={`Supprimer le scénario ${s.event}`}
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </div>
                        <div className="text-[var(--soft)] flex flex-wrap gap-x-3 gap-y-0.5">
                          {s.actif_concerne && <span><strong className="text-[var(--faint)]">Actif :</strong> {s.actif_concerne}</span>}
                          {s.owner
                            ? <span><strong className="text-[var(--faint)]">Owner :</strong> {s.owner}</span>
                            : <span className="text-[var(--rose)]">Sans propriétaire</span>}
                          {s.strategie_traitement
                            ? <span><strong className="text-[var(--faint)]">Stratégie :</strong> {s.strategie_traitement}</span>
                            : <span className="text-[var(--amber)]">Traitement non décidé</span>}
                          {(s.gravite_residuelle != null && s.vraisemblance_residuelle != null) && (
                            <span><strong className="text-[var(--faint)]">Résiduel :</strong> G:{s.gravite_residuelle} · V:{s.vraisemblance_residuelle}</span>
                          )}
                          {s.statut && <span><strong className="text-[var(--faint)]">Statut :</strong> {s.statut}</span>}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Add scenario form — deux lignes : cadrage du scénario, puis
                      chaîne de traitement (propriétaire, résiduel, décision). */}
                  <div className="lg:col-span-3 flex flex-col gap-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                      <input
                        type="text" placeholder="ID (ex: SO-05)" value={newScenario.id}
                        onChange={(e) => setNewScenario({ ...newScenario, id: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <input
                        type="text" placeholder="Scénario opérationnel" value={newScenario.event}
                        onChange={(e) => setNewScenario({ ...newScenario, event: e.target.value })}
                        className="md:col-span-2 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <select
                        value={newScenario.gravity}
                        onChange={(e) => setNewScenario({ ...newScenario, gravity: Number(e.target.value) })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        {[1, 2, 3, 4].map((g) => <option key={g} value={g}>Gravité {g}</option>)}
                      </select>
                      <select
                        value={newScenario.likelihood}
                        onChange={(e) => setNewScenario({ ...newScenario, likelihood: Number(e.target.value) })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>Vraisemblance {v}</option>)}
                      </select>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                      <input
                        type="text" placeholder="Actif concerné" value={newScenario.actif_concerne}
                        onChange={(e) => setNewScenario({ ...newScenario, actif_concerne: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <input
                        type="text" placeholder="Mesures d'atténuation" value={newScenario.mitigation}
                        onChange={(e) => setNewScenario({ ...newScenario, mitigation: e.target.value })}
                        className="md:col-span-2 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <input
                        type="text" placeholder="Propriétaire du risque" value={newScenario.owner}
                        onChange={(e) => setNewScenario({ ...newScenario, owner: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                      <select
                        value={newScenario.gravite_residuelle ?? ""}
                        onChange={(e) => setNewScenario({ ...newScenario, gravite_residuelle: e.target.value ? Number(e.target.value) : undefined })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="">Gravité résiduelle</option>
                        {[1, 2, 3, 4].map((g) => <option key={g} value={g}>{g}</option>)}
                      </select>
                      <select
                        value={newScenario.vraisemblance_residuelle ?? ""}
                        onChange={(e) => setNewScenario({ ...newScenario, vraisemblance_residuelle: e.target.value ? Number(e.target.value) : undefined })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="">Vraisemblance résiduelle</option>
                        {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
                      </select>
                      <select
                        value={newScenario.strategie_traitement}
                        onChange={(e) => setNewScenario({ ...newScenario, strategie_traitement: e.target.value as OperationalScenario["strategie_traitement"] })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="">Stratégie (ISO 6.1.3)</option>
                        <option value="Réduire">Réduire</option>
                        <option value="Accepter">Accepter</option>
                        <option value="Transférer">Transférer</option>
                        <option value="Éviter">Éviter</option>
                      </select>
                      <select
                        value={newScenario.statut}
                        onChange={(e) => setNewScenario({ ...newScenario, statut: e.target.value as OperationalScenario["statut"] })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="">Statut</option>
                        <option value="Ouvert">Ouvert</option>
                        <option value="En traitement">En traitement</option>
                        <option value="Traité">Traité</option>
                        <option value="Clos">Clos</option>
                      </select>
                      <button
                        type="button"
                        onClick={() => {
                          if (!newScenario.id.trim() || !newScenario.event.trim()) return;
                          const list = [...scenarios, newScenario];
                          updateStepData("ebios", "operational_scenarios", list);
                          setNewScenario({ ..._NOUVEAU_SCENARIO, id: nextId("SO", list.map((x) => x.id)) });
                        }}
                        className="flex items-center justify-center gap-1 bg-[var(--g1)] text-[#04150e] p-1.5 rounded-xl hover:opacity-90 font-bold"
                      >
                        <Plus size={15} /> Ajouter
                      </button>
                    </div>
                  </div>
                </div>

                {/* CASE STUDIES REFLEXES */}
                <div className="mt-1 border-t border-white/[0.04] pt-2">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">D. Fiches de Décision &amp; Retours d'Expérience Réels (REX)</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {casReels.map((c: CaseStudy, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] border border-white/5 rounded-xl p-3 text-xs animate-fade-in relative group">
                        <button
                          type="button"
                          onClick={() => {
                            const list = [...casReels]; list.splice(idx, 1);
                            updateStepData("ebios", "case_studies", list);
                          }}
                          className="absolute top-2 right-2 text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg opacity-0 group-hover:opacity-100 transition"
                          aria-label={`Supprimer le cas réel ${c.case}`}
                        >
                          <Trash2 size={12} />
                        </button>
                        <div className="font-bold text-[var(--sky)] mb-1 flex items-center gap-1 pr-5">
                          <BookOpen size={12} /> {c.case}
                        </div>
                        <p className="text-[11px] text-[var(--soft)] leading-normal">{c.lessons}</p>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
                    <input
                      type="text" placeholder="Cas réel (ex: Norsk Hydro)" value={newCas.case}
                      onChange={(e) => setNewCas({ ...newCas, case: e.target.value })}
                      className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                    />
                    <div className="md:col-span-2 flex gap-2">
                      <input
                        type="text" placeholder="Enseignement retenu pour ce client" value={newCas.lessons}
                        onChange={(e) => setNewCas({ ...newCas, lessons: e.target.value })}
                        className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (!newCas.case.trim()) return;
                          updateStepData("ebios", "case_studies", [...casReels, newCas]);
                          setNewCas(_NOUVEAU_CAS);
                        }}
                        className="bg-[var(--g1)] text-[#04150e] p-1.5 rounded-xl hover:opacity-90"
                      >
                        <Plus size={15} />
                      </button>
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
