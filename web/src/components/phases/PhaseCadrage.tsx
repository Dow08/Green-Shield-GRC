import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Plus, Target, Trash2 } from "lucide-react";
import { nextId } from "../../lib/ids";
import { useDismissOnOutsideOrEscape } from "../../lib/useDismissOnOutsideOrEscape";
import type { AssetMetier, AssetSupport, ProjectState } from "../../types";
import { SUGGESTED_METIER, SUGGESTED_SUPPORT } from "../../lib/gabarits";

interface Props {
  activeProject: ProjectState;
  updateStepData: (stepKey: string, fieldKey: string, value: unknown) => void;
  handleSaveProject: () => void;
}

/** Phase 1 du parcours de mission — extrait de Projects.tsx (découpage du
 *  29/07/2026). Le corps JSX est repris tel quel : seul l'état strictement
 *  local à cette phase a été déplacé ici. */
export function PhaseCadrage({ activeProject, updateStepData, handleSaveProject }: Props) {
  const [showMetierMenu, setShowMetierMenu] = useState(false);
  const [showCustomMetier, setShowCustomMetier] = useState(false);
  const [customMetierData, setCustomMetierData] = useState({ name: "", description: "", is_personal_data: false });
  const metierMenuRef = useDismissOnOutsideOrEscape<HTMLDivElement>(showMetierMenu, () => setShowMetierMenu(false));
  const [showSupportMenu, setShowSupportMenu] = useState(false);
  const [showCustomSupport, setShowCustomSupport] = useState(false);
  const [customSupportData, setCustomSupportData] = useState({ name: "", type: "Logiciel", description: "", owner: "DSI" });
  const supportMenuRef = useDismissOnOutsideOrEscape<HTMLDivElement>(showSupportMenu, () => setShowSupportMenu(false));

  return (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <Target size={15} /> 1. Cadrage de l'Audit &amp; Identification du Patrimoine (NIST)
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Périmètre technique de l'audit</label>
                    <input
                      type="text"
                      value={activeProject.steps.cadrage?.scope || ""}
                      onChange={(e) => updateStepData("cadrage", "scope", e.target.value)}
                      className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Missions &amp; Finalités de l'entreprise</label>
                    <input
                      type="text"
                      value={activeProject.steps.cadrage?.client_missions || ""}
                      onChange={(e) => updateStepData("cadrage", "client_missions", e.target.value)}
                      className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                    />
                  </div>
                </div>

                {/* NDA section */}
                <div className="glass-2 p-3 flex flex-col gap-2 mt-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-[var(--ink)]">Étape d'Homologation : Accord de Confidentialité (NDA)</span>
                    <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--g1)]">
                      <input
                        type="checkbox"
                        checked={activeProject.steps.cadrage?.nda_signed || false}
                        onChange={(e) => updateStepData("cadrage", "nda_signed", e.target.checked)}
                        className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                      />
                      Signer le NDA (Signature cryptographique locale)
                    </label>
                  </div>
                  <textarea
                    rows={4}
                    value={activeProject.steps.cadrage?.nda_text || ""}
                    onChange={(e) => updateStepData("cadrage", "nda_text", e.target.value)}
                    className="w-full bg-white/[0.01] border border-white/5 rounded-xl p-3 text-[11px] text-[var(--soft)] font-mono focus:outline-none"
                  />
                </div>

                {/* VALEURS METIER (PATRIMOINE SSIBLE) */}
                <div className="mt-2">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide flex justify-between items-center flex-wrap gap-2 relative">
                    <span>A. Cartographie des Valeurs Métier (Processus, Informations)</span>

                    {/* TRIGERABLE PLUS BUTTON TRIGGERING THE SELECT OPTION MENU */}
                    <div className="relative" ref={metierMenuRef}>
                      <button
                        type="button"
                        onClick={() => setShowMetierMenu(!showMetierMenu)}
                        className="flex items-center gap-1 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-1 text-xs font-bold text-[var(--g1)] transition cursor-pointer"
                      >
                        <Plus size={14} /> Ajouter une valeur métier...
                      </button>

                      {showMetierMenu && (
                        <div className="absolute right-0 mt-1.5 w-64 max-h-72 overflow-y-auto rounded-xl bg-[#091510] border border-[var(--stroke)] shadow-2xl z-50 p-2 text-xs flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-[var(--faint)] uppercase px-2 py-1">Gabarits types</div>
                          {SUGGESTED_METIER.map((m) => (
                            <button
                              key={m.id}
                              type="button"
                              onClick={() => {
                                const list = [...(activeProject.steps.cadrage?.assets_metier || [])];
                                list.push({
                                  id: nextId(m.id, list.map((a) => a.id)),
                                  name: m.name,
                                  description: m.description,
                                  is_personal_data: m.is_personal_data
                                });
                                updateStepData("cadrage", "assets_metier", list);
                                setShowMetierMenu(false);
                              }}
                              className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-white/5 transition flex items-center justify-between text-[var(--ink)] cursor-pointer"
                            >
                              <span>{m.name}</span>
                              {m.is_personal_data && <span className="text-[8px] bg-[rgba(46,230,160,0.12)] text-[var(--g1)] font-bold px-1 rounded">RGPD</span>}
                            </button>
                          ))}
                          <div className="border-t border-white/[0.04] my-1" />
                          <button
                            type="button"
                            onClick={() => {
                              setShowCustomMetier(true);
                              setShowMetierMenu(false);
                            }}
                            className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[rgba(46,230,160,0.12)] text-[var(--g1)] font-bold transition cursor-pointer"
                          >
                            + Créer une valeur personnalisée...
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 mt-2">
                    {activeProject.steps.cadrage?.assets_metier?.map((m: AssetMetier, idx: number) => (
                      <div key={idx} className="flex justify-between items-center bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs animate-fade-in">
                        <div>
                          <span className="font-mono bg-white/5 px-1 py-0.5 rounded text-[var(--sky)] mr-2">{m.id}</span>
                          <span className="font-bold text-[var(--ink)]">{m.name}</span>
                          <span className="text-[11px] text-[var(--soft)] ml-3">— {m.description}</span>
                          {m.is_personal_data && (
                            <span className="ml-2 bg-[rgba(46,230,160,0.12)] text-[var(--g1)] text-[9px] font-extrabold px-2 py-0.5 rounded-full">
                              RGPD
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const list = [...(activeProject.steps.cadrage?.assets_metier || [])];
                            list.splice(idx, 1);
                            updateStepData("cadrage", "assets_metier", list);
                          }}
                          className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                          aria-label={`Supprimer la valeur métier ${m.name}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* EXPANDABLE INLINE CUSTOM FORM */}
                  {showCustomMetier && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="glass p-3 border border-dashed border-[var(--stroke)] rounded-xl mt-2 flex flex-col gap-2.5 text-xs animate-fade-in"
                    >
                      <div className="font-bold text-[var(--g1)]">Saisie de Valeur Métier Personnalisée</div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                        <input
                          type="text"
                          placeholder="Nom de la valeur métier"
                          value={customMetierData.name}
                          onChange={(e) => setCustomMetierData({ ...customMetierData, name: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <input
                          type="text"
                          placeholder="Description"
                          value={customMetierData.description}
                          onChange={(e) => setCustomMetierData({ ...customMetierData, description: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <label className="flex items-center gap-1.5 cursor-pointer text-xs font-bold text-[var(--soft)]">
                          <input
                            type="checkbox"
                            checked={customMetierData.is_personal_data}
                            onChange={(e) => setCustomMetierData({ ...customMetierData, is_personal_data: e.target.checked })}
                            className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                          />
                          Données Personnelles (RGPD)
                        </label>
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setShowCustomMetier(false)}
                          className="px-3 py-1 border border-white/5 rounded-lg text-[10px] text-[var(--soft)] hover:bg-white/5"
                        >
                          Annuler
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (!customMetierData.name.trim()) return;
                            const list = [...(activeProject.steps.cadrage?.assets_metier || [])];
                            list.push({
                              id: nextId("VM", list.map((a) => a.id)),
                              name: customMetierData.name,
                              description: customMetierData.description,
                              is_personal_data: customMetierData.is_personal_data
                            });
                            updateStepData("cadrage", "assets_metier", list);
                            setCustomMetierData({ name: "", description: "", is_personal_data: false });
                            setShowCustomMetier(false);
                          }}
                          className="px-3.5 py-1 bg-[var(--g1)] text-[#04150e] font-bold rounded-lg text-[10px] hover:opacity-90"
                        >
                          Enregistrer
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* BIENS SUPPORTS */}
                <div className="mt-2">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide flex justify-between items-center flex-wrap gap-2 relative">
                    <span>B. Inventaire des Biens Supports (Actifs de l'infrastructure - NIST)</span>

                    {/* TRIGGERABLE PLUS BUTTON TRIGGERING THE SELECT OPTION MENU */}
                    <div className="relative" ref={supportMenuRef}>
                      <button
                        type="button"
                        onClick={() => setShowSupportMenu(!showSupportMenu)}
                        className="flex items-center gap-1 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-1 text-xs font-bold text-[var(--g1)] transition cursor-pointer"
                      >
                        <Plus size={14} /> Ajouter un bien support...
                      </button>

                      {showSupportMenu && (
                        <div className="absolute right-0 mt-1.5 w-64 max-h-72 overflow-y-auto rounded-xl bg-[#091510] border border-[var(--stroke)] shadow-2xl z-50 p-2 text-xs flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-[var(--faint)] uppercase px-2 py-1">Gabarits types</div>
                          {SUGGESTED_SUPPORT.map((s) => (
                            <button
                              key={s.id}
                              type="button"
                              onClick={() => {
                                const list = [...(activeProject.steps.cadrage?.assets_support || [])];
                                list.push({
                                  id: nextId(s.id, list.map((a) => a.id)),
                                  name: s.name,
                                  type: s.type,
                                  description: s.description,
                                  owner: s.owner
                                });
                                updateStepData("cadrage", "assets_support", list);
                                setShowSupportMenu(false);
                              }}
                              className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-white/5 transition flex items-center justify-between text-[var(--ink)] cursor-pointer"
                            >
                              <span>{s.name}</span>
                              <span className="text-[8px] bg-white/5 px-1 py-0.5 rounded text-[var(--soft)]">{s.type}</span>
                            </button>
                          ))}
                          <div className="border-t border-white/[0.04] my-1" />
                          <button
                            type="button"
                            onClick={() => {
                              setShowCustomSupport(true);
                              setShowSupportMenu(false);
                            }}
                            className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[rgba(46,230,160,0.12)] text-[var(--g1)] font-bold transition cursor-pointer"
                          >
                            + Créer un bien personnalisé...
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 mt-2">
                    {activeProject.steps.cadrage?.assets_support?.map((s: AssetSupport, idx: number) => (
                      <div key={idx} className="flex justify-between items-start bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs animate-fade-in">
                        <div>
                          <span className="font-mono bg-white/5 px-1 py-0.5 rounded text-[var(--g3)] mr-2">{s.id}</span>
                          <span className="font-bold text-[var(--ink)]">{s.name}</span>
                          <span className="text-[10px] text-[var(--soft)] bg-white/5 rounded px-1.5 py-0.5 ml-2">{s.type}</span>
                          <p className="text-[11px] text-[var(--soft)] mt-1 ml-1">{s.description} · <span className="font-bold text-[var(--ink)]">Propriétaire :</span> {s.owner}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const list = [...(activeProject.steps.cadrage?.assets_support || [])];
                            list.splice(idx, 1);
                            updateStepData("cadrage", "assets_support", list);
                          }}
                          className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg"
                          aria-label={`Supprimer le bien support ${s.name}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* EXPANDABLE INLINE CUSTOM SUPPORT FORM */}
                  {showCustomSupport && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="glass p-3 border border-dashed border-[var(--stroke)] rounded-xl mt-2 flex flex-col gap-2.5 text-xs animate-fade-in"
                    >
                      <div className="font-bold text-[var(--g1)]">Saisie de Bien Support Personnalisé</div>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                        <input
                          type="text"
                          placeholder="Nom de l'actif"
                          value={customSupportData.name}
                          onChange={(e) => setCustomSupportData({ ...customSupportData, name: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <select
                          value={customSupportData.type}
                          onChange={(e) => setCustomSupportData({ ...customSupportData, type: e.target.value })}
                          className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        >
                          <option value="Matériel">Matériel</option>
                          <option value="Logiciel">Logiciel</option>
                          <option value="Réseau">Réseau</option>
                          <option value="Ressources Humaines">Ressources Humaines</option>
                          <option value="Locaux">Locaux</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Propriétaire (DSI, RSSI...)"
                          value={customSupportData.owner}
                          onChange={(e) => setCustomSupportData({ ...customSupportData, owner: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                        <input
                          type="text"
                          placeholder="Description ou finalité"
                          value={customSupportData.description}
                          onChange={(e) => setCustomSupportData({ ...customSupportData, description: e.target.value })}
                          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setShowCustomSupport(false)}
                          className="px-3 py-1 border border-white/5 rounded-lg text-[10px] text-[var(--soft)] hover:bg-white/5"
                        >
                          Annuler
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (!customSupportData.name.trim()) return;
                            const list = [...(activeProject.steps.cadrage?.assets_support || [])];
                            list.push({
                              id: nextId("BS", list.map((a) => a.id)),
                              name: customSupportData.name,
                              type: customSupportData.type,
                              description: customSupportData.description,
                              owner: customSupportData.owner
                            });
                            updateStepData("cadrage", "assets_support", list);
                            setCustomSupportData({ name: "", type: "Logiciel", description: "", owner: "DSI" });
                            setShowCustomSupport(false);
                          }}
                          className="px-3.5 py-1 bg-[var(--g1)] text-[#04150e] font-bold rounded-lg text-[10px] hover:opacity-90"
                        >
                          Enregistrer
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>

                {/* STEP EXPLICIT CONFIRMATION BUTTON */}
                <div className="border-t border-white/[0.04] pt-4 mt-2 flex justify-between items-center bg-white/[0.01] p-3 rounded-2xl flex-wrap gap-2">
                  <span className="text-xs text-[var(--soft)] flex items-center gap-1.5">
                    <CheckCircle2 size={13} className="text-[var(--g1)] flex-shrink-0" /> Validez pour faire progresser la jauge de la mission.
                  </span>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-[var(--g1)] flex-shrink-0">
                    <input
                      type="checkbox"
                      checked={activeProject.steps.cadrage?.validated || false}
                      onChange={(e) => {
                        updateStepData("cadrage", "validated", e.target.checked);
                        setTimeout(() => handleSaveProject(), 100);
                      }}
                      className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                    />
                    Étape 1 (Cadrage &amp; Patrimoine) validée
                  </label>
                </div>

              </div>
  );
}
