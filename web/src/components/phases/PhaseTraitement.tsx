import { useState } from "react";
import { motion } from "framer-motion";
import { Bot, CheckCircle2, FileDown, Plus, Trash2 } from "lucide-react";
import { nextId } from "../../lib/ids";
import { CopilotSourceBadge } from "../CopilotSourceBadge";
import { RevueExport } from "../RevueExport";
import type { ProjectState, Remediation } from "../../types";
import { api } from "../../lib/api";
import { safeGetItem } from "../../lib/storage";
import type { CopilotSource, RevueExportResult } from "../../types";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
  handleExportDoc: (docType: string) => void;
  revue: RevueExportResult | null;
  revueEnCours: boolean;
  onAllerALaPhase: (phase: number) => void;
}

/** Phase 6 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici. */
export function PhaseTraitement({ activeProject, updateStepData, handleSaveProject, handleExportDoc,
                                  revue, revueEnCours, onAllerALaPhase }: Props) {
  const [copilotPrompt, setCopilotPrompt] = useState("");
  const [copilotResponse, setCopilotResponse] = useState("");
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotSource, setCopilotSource] = useState<CopilotSource | null>(null);
  const [newRemediation, setNewRemediation] = useState<Remediation>({
    id: "", axe: "Protection", measure: "", priority: "Élevé",
    responsable: "", echeance: "", statut: "À faire", cout_estime: "", risque_lie: "",
  });

  // Téléchargement Word : POST + blob (pas un simple lien) depuis le
  // 30/07/2026, pour que le logo personnalisé du cabinet (Réglages) puisse
  // transiter dans le corps de la requête plutôt que dans une URL.
  const handleDownloadDocx = (telecharger: (id: string) => Promise<void>) => {
    telecharger(activeProject.id).catch((err) => alert("Export Word indisponible : " + err.message));
  };

  const handleRunCopilot = () => {
    if (!copilotPrompt.trim()) return;
    setCopilotLoading(true);
    setCopilotResponse("");
    setCopilotSource(null);

    // Call custom copilot API — utilise la clé Gemini/OpenAI configurée dans les Réglages
    // si présente (analyse générative en ligne), sinon l'API bascule sur l'intelligence
    // experte locale hors-ligne.
    const storedKey = safeGetItem("copilot_api_key") || "";
    fetch(`/api/projects/${activeProject.id}/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: copilotPrompt, key: storedKey })
    })
    .then((res) => res.json())
    .then((data) => {
      setCopilotResponse(data.response || "Réponse indisponible");
      setCopilotSource(data.source ?? null);
    })
    .catch((err) => alert("Copilote indisponible : " + err.message))
    .finally(() => setCopilotLoading(false));
  };

  return (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <Bot size={15} /> 6. Feuille de Route de Traitement &amp; Copilote Cyber AI
                </div>

                {/* SYNTHÈSE EXÉCUTIVE — chapitre 1 du rapport, seul champ que
                    l'outil ne permettait pas de saisir jusqu'au 30/07/2026. */}
                <div>
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide">
                    A. Synthèse à destination de la direction
                  </div>
                  <label htmlFor="exec-summary" className="block text-[10px] text-[var(--faint)] mb-1">
                    Premier chapitre du rapport d'audit. Jamais rédigée automatiquement : elle engage
                    votre jugement, pas un calcul.
                  </label>
                  <textarea
                    id="exec-summary"
                    rows={4}
                    placeholder="Ce que la direction doit retenir : niveau de maturité constaté, écarts majeurs, ce qui relève d'un processus à formaliser plutôt que d'un investissement."
                    value={activeProject.steps.restitution?.exec_summary || ""}
                    onChange={(e) => updateStepData("restitution", "exec_summary", e.target.value)}
                    className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                  />
                </div>

                {/* PLAN D'ACTIONS (REMEDIATIONS) */}
                <div>
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide">B. Plan d'Action de Remédiation (4 Axes Cyber)</div>
                  <div className="flex flex-col gap-2">
                    {activeProject.steps.traitement?.remediations?.map((r: Remediation, idx: number) => {
                      const enRetard = !!r.echeance && r.statut !== "Fait" && r.echeance < new Date().toISOString().slice(0, 10);
                      return (
                      <div key={idx} className={`bg-white/[0.02] p-2.5 rounded-xl border text-xs flex flex-col gap-1 ${enRetard ? "border-[var(--rose)]/40" : "border-white/[0.05]"}`}>
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="font-bold text-[var(--g1)] bg-[rgba(46,230,160,0.12)] px-2 py-0.5 rounded-full text-[9px] uppercase mr-2">{r.axe}</span>
                            <span className="font-bold text-[var(--ink)]">{r.measure}</span>
                            <span className={`ml-2 text-[9px] font-extrabold rounded-full px-1.5 py-0.5 ${r.priority === "Critique" ? "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]" : "bg-white/5 text-[var(--soft)]"}`}>{r.priority}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              const list = [...(activeProject.steps.traitement?.remediations || [])];
                              list.splice(idx, 1);
                              updateStepData("traitement", "remediations", list);
                            }}
                            className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                            aria-label={`Supprimer la mesure ${r.measure}`}
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[var(--soft)]">
                          {r.responsable
                            ? <span><strong className="text-[var(--faint)]">Responsable :</strong> {r.responsable}</span>
                            : <span className="text-[var(--amber)]">Sans responsable</span>}
                          {r.echeance && (
                            <span className={enRetard ? "text-[var(--rose)] font-bold" : ""}>
                              <strong className="text-[var(--faint)]">Échéance :</strong> {r.echeance}{enRetard ? " — en retard" : ""}
                            </span>
                          )}
                          {r.statut && <span><strong className="text-[var(--faint)]">Statut :</strong> {r.statut}</span>}
                          {r.cout_estime && <span><strong className="text-[var(--faint)]">Coût :</strong> {r.cout_estime}</span>}
                          {r.risque_lie && <span><strong className="text-[var(--faint)]">Risque traité :</strong> {r.risque_lie}</span>}
                        </div>
                      </div>
                      );
                    })}
                  </div>

                  {/* Add Remediation Form */}
                  <div className="flex flex-col gap-2 mt-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                      <input
                        type="text" placeholder="ID (ex: REM-05)" value={newRemediation.id}
                        onChange={(e) => setNewRemediation({ ...newRemediation, id: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <select
                        value={newRemediation.axe}
                        onChange={(e) => setNewRemediation({ ...newRemediation, axe: e.target.value as Remediation["axe"] })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="Gouvernance">Gouvernance</option>
                        <option value="Protection">Protection</option>
                        <option value="Défense">Défense</option>
                        <option value="Résilience">Résilience</option>
                      </select>
                      <select
                        value={newRemediation.priority}
                        onChange={(e) => setNewRemediation({ ...newRemediation, priority: e.target.value as Remediation["priority"] })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="Critique">Critique</option>
                        <option value="Élevé">Élevé</option>
                        <option value="Moyen">Moyen</option>
                        <option value="Faible">Faible</option>
                      </select>
                      <input
                        type="text" placeholder="Mesure de sécurité à appliquer" value={newRemediation.measure}
                        onChange={(e) => setNewRemediation({ ...newRemediation, measure: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                      <input
                        type="text" placeholder="Responsable" value={newRemediation.responsable}
                        onChange={(e) => setNewRemediation({ ...newRemediation, responsable: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <input
                        type="date" value={newRemediation.echeance}
                        onChange={(e) => setNewRemediation({ ...newRemediation, echeance: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none text-[var(--ink)]"
                      />
                      <select
                        value={newRemediation.statut}
                        onChange={(e) => setNewRemediation({ ...newRemediation, statut: e.target.value as Remediation["statut"] })}
                        className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                      >
                        <option value="À faire">À faire</option>
                        <option value="En cours">En cours</option>
                        <option value="Fait">Fait</option>
                      </select>
                      <input
                        type="text" placeholder="Coût estimé" value={newRemediation.cout_estime}
                        onChange={(e) => setNewRemediation({ ...newRemediation, cout_estime: e.target.value })}
                        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <div className="flex gap-2">
                        <input
                          type="text" placeholder="Risque lié (ex: SO-01)" value={newRemediation.risque_lie}
                          onChange={(e) => setNewRemediation({ ...newRemediation, risque_lie: e.target.value })}
                          className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            if (!newRemediation.id.trim() || !newRemediation.measure.trim()) return;
                            const list = [...(activeProject.steps.traitement?.remediations || [])];
                            list.push(newRemediation);
                            updateStepData("traitement", "remediations", list);
                            setNewRemediation({
                              id: nextId("REM", list.map((r) => r.id)), axe: "Protection", measure: "", priority: "Élevé",
                              responsable: "", echeance: "", statut: "À faire", cout_estime: "", risque_lie: "",
                            });
                          }}
                          className="bg-[var(--g1)] text-[#04150e] p-1.5 rounded-xl hover:opacity-90"
                        >
                          <Plus size={15} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* RISQUES ACCEPTES (tracabilite de l'acceptation formelle) */}
                {activeProject.steps.ebios?.operational_scenarios?.some((s) => s.strategie_traitement === "Accepter") && (
                  <div className="mt-1 border-t border-white/[0.04] pt-3">
                    <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide">Risques acceptés (traçabilité de l'acceptation formelle)</div>
                    <div className="flex flex-col gap-2">
                      {activeProject.steps.ebios.operational_scenarios
                        .filter((s) => s.strategie_traitement === "Accepter")
                        .map((s, idx) => (
                          <div key={idx} className="bg-white/[0.02] p-2.5 rounded-xl border border-[var(--amber)]/30 text-xs flex justify-between items-center">
                            <div>
                              <span className="font-mono text-[var(--g3)] mr-2">{s.id}</span>
                              <span className="font-bold text-[var(--ink)]">{s.event}</span>
                            </div>
                            {s.owner
                              ? <span className="text-[var(--soft)]">Accepté par : {s.owner}</span>
                              : <span className="text-[var(--rose)] font-bold">Acceptation sans propriétaire nommé</span>}
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* THE CYBERDEPART (6 PRIORITES) */}
                <div className="mt-2 border-t border-white/[0.04] pt-3">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">C. Le Cyberdépart (6 Mesures d'hygiène vitales prioritaires - ANSSI)</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {activeProject.steps.traitement?.quick_wins?.map((qw: string, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] border border-white/5 rounded-xl p-2.5 text-xs flex items-center gap-2">
                        <CheckCircle2 size={13} className="text-[var(--g1)] flex-shrink-0" />
                        <span className="font-bold text-[var(--ink)]">{qw}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* COPILOTE CYBER AI (LLM CLIENT) */}
                <div className="mt-3 border-t border-white/[0.04] pt-4">
                  <div className="glass p-4 border-[var(--stroke)] flex flex-col gap-3 bg-[var(--bg2)] rounded-2xl animate-fade-in">
                    <div className="flex items-center gap-2">
                      <Bot size={15} className="text-purple-400" />
                      <span className="text-xs font-bold text-[var(--ink)]">Copilote IA - Analyse Cyber Générative (Offline-ready)</span>
                    </div>

                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="ex: Propose une stratégie PSSI, ou une analyse de risques EBIOS..."
                        value={copilotPrompt}
                        onChange={(e) => setCopilotPrompt(e.target.value)}
                        className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                      />
                      <button
                        onClick={handleRunCopilot}
                        disabled={copilotLoading}
                        className="px-4 py-2 bg-gradient-to-br from-purple-600 to-indigo-600 font-bold rounded-xl text-xs hover:opacity-90 disabled:opacity-40"
                      >
                        {copilotLoading ? "Analyse..." : "Demander à l'IA"}
                      </button>
                    </div>

                    {copilotResponse && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="bg-white/[0.01] border border-white/5 rounded-xl p-3 text-xs font-mono text-[var(--soft)] whitespace-pre-line leading-relaxed"
                      >
                        <CopilotSourceBadge source={copilotSource} />
                        {copilotResponse}
                      </motion.div>
                    )}
                  </div>
                </div>

                {/* DELIVERABLES EXPORTER */}
                <div className="mt-3 border-t border-white/[0.04] pt-4 flex flex-col gap-2">
                  <div className="text-[11px] font-bold text-[var(--soft)] uppercase tracking-wide">D. Téléchargement des rapports multi-formats (Impression PDF / Word)</div>

                  {/* Ce qui manquerait dans les livrables, AVANT de les générer. */}
                  <RevueExport revue={revue} chargement={revueEnCours} onAllerALaPhase={onAllerALaPhase} />

                  {/* Chaque livrable en deux formats : .md pour GitHub/le versionnement,
                      .docx à l'identité du rapport de mission — prêt à envoyer au client. */}
                  <div className="flex flex-col gap-2.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-bold text-[var(--faint)] w-32 flex-shrink-0">Accord (NDA)</span>
                      <button
                        onClick={() => handleExportDoc("nda")}
                        className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--ink)] transition"
                      >
                        <FileDown size={13} /> .md
                      </button>
                      <button
                        onClick={() => handleDownloadDocx(api.projects.downloadNdaDocx)}
                        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3 py-2 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
                      >
                        <FileDown size={13} /> Word (.docx)
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-bold text-[var(--faint)] w-32 flex-shrink-0">Analyse EBIOS RM</span>
                      <button
                        onClick={() => handleExportDoc("ebios")}
                        className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--ink)] transition"
                      >
                        <FileDown size={13} /> .md
                      </button>
                      <button
                        onClick={() => handleDownloadDocx(api.projects.downloadEbiosDocx)}
                        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3 py-2 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
                      >
                        <FileDown size={13} /> Word (.docx)
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-bold text-[var(--faint)] w-32 flex-shrink-0">PSSI &amp; Plan PRI</span>
                      <button
                        onClick={() => handleExportDoc("pssi_pri")}
                        className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--ink)] transition"
                      >
                        <FileDown size={13} /> .md
                      </button>
                      <button
                        onClick={() => handleDownloadDocx(api.projects.downloadPssiDocx)}
                        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3 py-2 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
                      >
                        <FileDown size={13} /> Word (.docx)
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-bold text-[var(--faint)] w-32 flex-shrink-0">AIPD / PIA (RGPD)</span>
                      <button
                        onClick={() => handleExportDoc("aipd")}
                        className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--ink)] transition"
                      >
                        <FileDown size={13} /> .md
                      </button>
                      <button
                        onClick={() => handleDownloadDocx(api.projects.downloadAipdDocx)}
                        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3 py-2 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
                      >
                        <FileDown size={13} /> Word (.docx)
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 border-t border-white/[0.04] pt-2.5 mt-0.5">
                      <span className="text-[10px] font-bold text-[var(--faint)] w-32 flex-shrink-0">Rapport d'audit</span>
                      {activeProject.type === "grc" && (
                        <button
                          onClick={() => handleExportDoc("audit_report")}
                          className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--ink)] transition"
                        >
                          <FileDown size={13} /> .md
                        </button>
                      )}
                      <button
                        onClick={() => handleDownloadDocx(api.projects.downloadReportDocx)}
                        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3 py-2 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
                      >
                        <FileDown size={13} /> Word (.docx)
                      </button>
                    </div>
                  </div>
                </div>

                {/* STEP EXPLICIT CONFIRMATION BUTTON */}
                <div className="border-t border-white/[0.04] pt-4 mt-2 flex justify-between items-center bg-white/[0.01] p-3 rounded-2xl flex-wrap gap-2 animate-pulse">
                  <span className="text-xs text-[var(--soft)] flex items-center gap-1.5">
                    <CheckCircle2 size={13} className="text-[var(--g1)] flex-shrink-0" /> Validez pour finaliser la jauge de la mission.
                  </span>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--g1)] flex-shrink-0">
                    <input
                      type="checkbox"
                      checked={activeProject.steps.traitement?.validated || false}
                      onChange={(e) => {
                        updateStepData("traitement", "validated", e.target.checked);
                        setTimeout(() => handleSaveProject(), 100);
                      }}
                      className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                    />
                    Étape 6 (Traitement &amp; Livrables) validée
                  </label>
                </div>

              </div>
  );
}
