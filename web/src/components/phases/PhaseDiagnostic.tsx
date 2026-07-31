import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, HelpCircle, Plus, Shield, Trash2 } from "lucide-react";
import { nextId } from "../../lib/ids";
import { useDismissOnOutsideOrEscape } from "../../lib/useDismissOnOutsideOrEscape";
import type { AIPDData, ProjectState, RGPDRegister } from "../../types";
import { ObligationsAIPD } from "../ObligationsAIPD";
import { ViolationsPanel } from "../ViolationsPanel";
import { BadgesControles } from "../BadgesControles";
import { AnimatePresence } from "framer-motion";
import { SUGGESTED_RGPD } from "../../lib/gabarits";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
}

/** Phase 2 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici. */
export function PhaseDiagnostic({ activeProject, updateStepData, handleSaveProject }: Props) {
  const [activeHelp, setActiveHelp] = useState<string | null>(null);
  const [showRgpdMenu, setShowRgpdMenu] = useState(false);
  const [showCustomRgpd, setShowCustomRgpd] = useState(false);
  const [customRgpdData, setCustomRgpdData] = useState({ name: "", purpose: "", data_categories: "", retention: "5 ans" });
  const rgpdMenuRef = useDismissOnOutsideOrEscape<HTMLDivElement>(showRgpdMenu, () => setShowRgpdMenu(false));

  return (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <Shield size={15} /> 2. Socle de Sécurité, État des lieux &amp; Protection RGPD/CNIL
                </div>

                {/* Security Hygiène checklist with click-for-help panels */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  
                  <div 
                    onClick={() => setActiveHelp(activeHelp === "pssi" ? null : "pssi")}
                    className={`glass p-3 flex flex-col gap-1.5 cursor-pointer border transition hover:border-[var(--g1)] ${activeHelp === "pssi" ? "border-[var(--g1)] bg-[rgba(46,230,160,0.02)]" : "border-white/5"}`}
                  >
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--ink)]">
                      <input
                        type="checkbox"
                        checked={activeProject.steps.diagnostic?.pssi_active || false}
                        onChange={(e) => updateStepData("diagnostic", "pssi_active", e.target.checked)}
                        onClick={(e) => e.stopPropagation()} // avoid toggling help panel
                        className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                      />
                      Politique de Sécurité (PSSI) active
                    </label>
                    <p className="text-[10px] text-[var(--soft)] flex items-center gap-1">
                      <HelpCircle size={10} className="text-[var(--g3)]" /> Cliquez pour afficher l'aide à la rédaction.
                    </p>
                  </div>

                  <div 
                    onClick={() => setActiveHelp(activeHelp === "gov" ? null : "gov")}
                    className={`glass p-3 flex flex-col gap-1.5 cursor-pointer border transition hover:border-[var(--g1)] ${activeHelp === "gov" ? "border-[var(--g1)] bg-[rgba(46,230,160,0.02)]" : "border-white/5"}`}
                  >
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--ink)]">
                      <input
                        type="checkbox"
                        checked={activeProject.steps.diagnostic?.governance_active || false}
                        onChange={(e) => updateStepData("diagnostic", "governance_active", e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                      />
                      Gouvernance Cyber organisée
                    </label>
                    <p className="text-[10px] text-[var(--soft)] flex items-center gap-1">
                      <HelpCircle size={10} className="text-[var(--g3)]" /> Cliquez pour voir les rôles et structures.
                    </p>
                  </div>

                  <div 
                    onClick={() => setActiveHelp(activeHelp === "vuln" ? null : "vuln")}
                    className={`glass p-3 flex flex-col gap-1.5 cursor-pointer border transition hover:border-[var(--g1)] ${activeHelp === "vuln" ? "border-[var(--g1)] bg-[rgba(46,230,160,0.02)]" : "border-white/5"}`}
                  >
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--ink)]">
                      <input
                        type="checkbox"
                        checked={activeProject.steps.diagnostic?.vulnerabilities_active || false}
                        onChange={(e) => updateStepData("diagnostic", "vulnerabilities_active", e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                      />
                      Gestion continue des Vulnérabilités
                    </label>
                    <BadgesControles pratique="vulnerabilites" />
                    <p className="text-[10px] text-[var(--soft)] flex items-center gap-1">
                      <HelpCircle size={10} className="text-[var(--g3)]" /> Cliquez pour voir le contrôle continu.
                    </p>
                  </div>

                </div>

                {/* ANIMATED INTERACTIVE SLIDEOUT HELP COMPONENT */}
                <AnimatePresence>
                  {activeHelp && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="glass border-[var(--g1)] p-4 text-xs flex flex-col gap-2.5 bg-gradient-to-br from-[rgba(46,230,160,0.02)] to-[rgba(25,198,198,0.01)] text-[var(--soft)] leading-relaxed"
                    >
                      {activeHelp === "pssi" && (
                        <div>
                          <div className="font-bold text-[var(--g1)] text-xs mb-1.5">Guide Méthodologique : Comment rédiger et valider une PSSI ?</div>
                          <p>
                            La **PSSI (Politique de Sécurité des Systèmes d'Information)** est le document de référence définissant les règles et consignes de sécurité à appliquer au sein de l'entreprise.
                          </p>
                          <ul className="list-disc pl-4 mt-1.5 flex flex-col gap-1 text-[11px]">
                            <li><strong>Canevas de base :</strong> Doit impérativement traiter de la gestion des accès, de la complexité des mots de passe (CIS 5), du télétravail, de la classification des données, et de l'usage des supports amovibles.</li>
                            <li><strong>Validation :</strong> Elle doit obligatoirement être **approuvée et signée par la direction générale** (ComDir) pour avoir une valeur réglementaire et opérationnelle contraignante.</li>
                            <li><strong>Sensibilisation :</strong> Elle doit être annexée au règlement intérieur de l'entreprise et diffusée à 100% des collaborateurs lors de l'onboarding.</li>
                          </ul>
                        </div>
                      )}
                      {activeHelp === "gov" && (
                        <div>
                          <div className="font-bold text-[var(--g1)] text-xs mb-1.5">Guide Organisationnel : Structurer la Gouvernance de Sécurité</div>
                          <p>
                            Une bonne gouvernance cyber répartit les responsabilités entre les équipes exécutives, techniques et de contrôle.
                          </p>
                          <ul className="list-disc pl-4 mt-1.5 flex flex-col gap-1 text-[11px]">
                            <li><strong>Désignation d'un Référent / RSSI :</strong> Un Responsable Sécurité (même à temps partiel) doit être nommé pour arbitrer et porter la voix de la cyber auprès de la direction.</li>
                            <li><strong>Comité de Pilotage Sécurité :</strong> Réunion trimestrielle du RSSI, DSI et Direction Générale pour arbitrer les budgets cyber et valider le Plan d'Action d'Amélioration (PAA).</li>
                            <li><strong>Sous-traitance :</strong> Revue annuelle des responsabilités cyber partagées avec votre prestataire d'infogérance (ESN/ESSP) via un plan d'assurance sécurité (PAS).</li>
                          </ul>
                        </div>
                      )}
                      {activeHelp === "vuln" && (
                        <div>
                          <div className="font-bold text-[var(--g1)] text-xs mb-1.5">Guide SecOps : Déployer une Gestion Continue des Vulnérabilités (CIS Controls 7 / NIST ID.RA-01)</div>
                          <p>
                            La gestion des vulnérabilités consiste à identifier, évaluer et corriger en continu les failles logicielles avant qu'elles ne soient exploitées.
                          </p>
                          <ul className="list-disc pl-4 mt-1.5 flex flex-col gap-1 text-[11px]">
                            <li><strong>Scans Réguliers :</strong> Déployer des scanners automatiques (comme Nessus ou OpenVAS) pour cartographier les ports ouverts et logiciels obsolètes.</li>
                            <li><strong>Politique de Patching (Correctifs) :</strong> Établir des délais stricts de remédiation : maximum **48 heures pour les failles critiques exploitées** (0-day), et 30 jours pour les failles moyennes.</li>
                            <li><strong>Maintien en Condition de Sécurité :</strong> Automatiser les mises à jour majeures du système d'exploitation et des applications logicielles d'administration.</li>
                          </ul>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* RGPD REGISTER */}
                <div className="mt-2">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide flex justify-between items-center flex-wrap gap-2 relative">
                    <span>A. Registre des Activités de Traitement (RGPD Article 30)</span>

                    {/* TRIGGERABLE PLUS BUTTON TRIGGERING THE SELECT OPTION MENU */}
                    <div className="relative" ref={rgpdMenuRef}>
                      <button
                        type="button"
                        onClick={() => setShowRgpdMenu(!showRgpdMenu)}
                        className="flex items-center gap-1 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-1 text-xs font-bold text-[var(--g1)] transition cursor-pointer"
                      >
                        <Plus size={14} /> Ajouter un traitement...
                      </button>

                      {showRgpdMenu && (
                        <div className="absolute right-0 mt-1.5 w-64 max-h-72 overflow-y-auto rounded-xl bg-[#091510] border border-[var(--stroke)] shadow-2xl z-50 p-2 text-xs flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-[var(--faint)] uppercase px-2 py-1">Traitements standards</div>
                          {SUGGESTED_RGPD.map((r) => (
                            <button
                              key={r.id}
                              type="button"
                              onClick={() => {
                                const list = [...(activeProject.steps.diagnostic?.rgpd_register || [])];
                                list.push({
                                  id: nextId(r.id, list.map((a) => a.id)),
                                  name: r.name,
                                  purpose: r.purpose,
                                  data_categories: r.data_categories,
                                  retention: r.retention
                                });
                                updateStepData("diagnostic", "rgpd_register", list);
                                setShowRgpdMenu(false);
                              }}
                              className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-white/5 transition flex flex-col text-[var(--ink)] cursor-pointer"
                            >
                              <strong className="text-[11px]">{r.name}</strong>
                              <span className="text-[9px] text-[var(--soft)] mt-0.5 truncate">{r.purpose}</span>
                            </button>
                          ))}
                          <div className="border-t border-white/[0.04] my-1" />
                          <button
                            type="button"
                            onClick={() => {
                              setShowCustomRgpd(true);
                              setShowRgpdMenu(false);
                            }}
                            className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[rgba(46,230,160,0.12)] text-[var(--g1)] font-bold transition cursor-pointer"
                          >
                            + Créer une activité personnalisée...
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex flex-col gap-2 mt-2">
                    {activeProject.steps.diagnostic?.rgpd_register?.map((r: RGPDRegister, idx: number) => (
                      <div key={idx} className="flex justify-between items-start bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs">
                        <div>
                          <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-2">{r.id}</span>
                          <span className="font-bold text-[var(--ink)]">{r.name}</span>
                          <p className="text-[11px] text-[var(--soft)] mt-1 ml-1"><span className="font-bold text-[var(--ink)]">Finalité :</span> {r.purpose} · <span className="font-bold text-[var(--ink)]">Catégories :</span> {r.data_categories} · <span className="font-bold text-[var(--ink)]">Conservation :</span> {r.retention}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const list = [...(activeProject.steps.diagnostic?.rgpd_register || [])];
                            list.splice(idx, 1);
                            updateStepData("diagnostic", "rgpd_register", list);
                          }}
                          className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                          aria-label={`Supprimer le traitement RGPD ${r.name}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* EXPANDABLE INLINE CUSTOM RGPD REGISTER FORM */}
                  {showCustomRgpd && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="glass p-3 border border-dashed border-[var(--stroke)] rounded-xl mt-2 flex flex-col gap-2.5 text-xs animate-fade-in"
                    >
                      <div className="font-bold text-[var(--g1)]">Saisie d'Activité de Traitement RGPD</div>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                        <input
                          type="text"
                          placeholder="Nom de l'activité"
                          value={customRgpdData.name}
                          onChange={(e) => setCustomRgpdData({ ...customRgpdData, name: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <input
                          type="text"
                          placeholder="Finalité opérationnelle"
                          value={customRgpdData.purpose}
                          onChange={(e) => setCustomRgpdData({ ...customRgpdData, purpose: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <input
                          type="text"
                          placeholder="Données (Nom, NIR...)"
                          value={customRgpdData.data_categories}
                          onChange={(e) => setCustomRgpdData({ ...customRgpdData, data_categories: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <input
                          type="text"
                          placeholder="Rétention (ex: 5 ans)"
                          value={customRgpdData.retention}
                          onChange={(e) => setCustomRgpdData({ ...customRgpdData, retention: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setShowCustomRgpd(false)}
                          className="px-3 py-1 border border-white/5 rounded-lg text-[10px] text-[var(--soft)] hover:bg-white/5"
                        >
                          Annuler
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (!customRgpdData.name.trim()) return;
                            const list = [...(activeProject.steps.diagnostic?.rgpd_register || [])];
                            list.push({
                              id: nextId("RGPD", list.map((a) => a.id)),
                              name: customRgpdData.name,
                              purpose: customRgpdData.purpose,
                              data_categories: customRgpdData.data_categories,
                              retention: customRgpdData.retention
                            });
                            updateStepData("diagnostic", "rgpd_register", list);
                            setCustomRgpdData({ name: "", purpose: "", data_categories: "", retention: "5 ans" });
                            setShowCustomRgpd(false);
                          }}
                          className="px-3.5 py-1 bg-[var(--g1)] text-[#04150e] font-bold rounded-lg text-[10px] hover:opacity-90"
                        >
                          Enregistrer
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* AIPD / PIA COMPLIANCE QUESTIONNAIRE */}
                <div className="mt-3 border-t border-white/[0.04] pt-3 flex flex-col gap-3">
                  <div className="flex items-center justify-between font-wrap gap-2 flex-wrap">
                    <span className="text-[11px] font-bold text-[var(--soft)] uppercase tracking-wide">B. Analyse d'Impact relative à la Protection des Données (AIPD / PIA)</span>
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--sky)] flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={activeProject.steps.diagnostic?.aipd_required || false}
                        onChange={(e) => updateStepData("diagnostic", "aipd_required", e.target.checked)}
                        className="rounded border-[var(--stroke)] bg-transparent text-[var(--sky)] focus:ring-0"
                      />
                      AIPD obligatoire pour ce projet (Risque élevé détecté)
                    </label>
                  </div>

                  {activeProject.steps.diagnostic?.aipd_required && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="flex flex-col gap-3.5 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-4 rounded-2xl text-xs"
                    >
                      <div>
                        <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">1. Description systématique et finalités du traitement</label>
                        <textarea
                          rows={2}
                          value={activeProject.steps.diagnostic?.aipd?.treatment_description || ""}
                          onChange={(e) => {
                            const aipd = { ...activeProject.steps.diagnostic?.aipd, treatment_description: e.target.value };
                            updateStepData("diagnostic", "aipd", aipd);
                          }}
                          className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2.5 text-xs focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">2. Évaluation de la nécessité et de la proportionnalité</label>
                        <textarea
                          rows={2}
                          value={activeProject.steps.diagnostic?.aipd?.necessity_eval || ""}
                          onChange={(e) => {
                            const aipd = { ...activeProject.steps.diagnostic?.aipd, necessity_eval: e.target.value };
                            updateStepData("diagnostic", "aipd", aipd);
                          }}
                          className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2.5 text-xs focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">3. Évaluation des risques pour les droits et libertés des personnes (Impacts &amp; Gravité CNIL)</label>
                        <textarea
                          rows={2}
                          value={activeProject.steps.diagnostic?.aipd?.risks_eval || ""}
                          onChange={(e) => {
                            const aipd = { ...activeProject.steps.diagnostic?.aipd, risks_eval: e.target.value };
                            updateStepData("diagnostic", "aipd", aipd);
                          }}
                          className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2.5 text-xs focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">4. Mesures d'atténuation et de sécurité (Chiffrement, MFA, logs...)</label>
                        <textarea
                          rows={2}
                          value={activeProject.steps.diagnostic?.aipd?.mitigation_measures || ""}
                          onChange={(e) => {
                            const aipd = { ...activeProject.steps.diagnostic?.aipd, mitigation_measures: e.target.value };
                            updateStepData("diagnostic", "aipd", aipd);
                          }}
                          className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl p-2.5 text-xs focus:outline-none"
                        />
                      </div>

                      <ObligationsAIPD
                        aipd={activeProject.steps.diagnostic?.aipd || ({} as AIPDData)}
                        onChange={(aipd) => updateStepData("diagnostic", "aipd", aipd)}
                      />
                    </motion.div>
                  )}
                </div>

                <div className="mt-2 border-t border-white/[0.04] pt-3">
                  <ViolationsPanel
                    violations={activeProject.steps.diagnostic?.violations || []}
                    onChange={(violations) => updateStepData("diagnostic", "violations", violations)}
                  />
                </div>

                {/* STEP EXPLICIT CONFIRMATION BUTTON */}
                <div className="border-t border-white/[0.04] pt-4 mt-2 flex justify-between items-center bg-white/[0.01] p-3 rounded-2xl flex-wrap gap-2">
                  <span className="text-xs text-[var(--soft)] flex items-center gap-1.5">
                    <CheckCircle2 size={13} className="text-[var(--g1)] flex-shrink-0" /> Validez pour faire progresser la jauge de la mission.
                  </span>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--g1)] flex-shrink-0">
                    <input
                      type="checkbox"
                      checked={activeProject.steps.diagnostic?.validated || false}
                      onChange={(e) => {
                        updateStepData("diagnostic", "validated", e.target.checked);
                        setTimeout(() => handleSaveProject(), 100);
                      }}
                      className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                    />
                    Étape 2 (Diagnostic &amp; RGPD) validée
                  </label>
                </div>

              </div>
  );
}
