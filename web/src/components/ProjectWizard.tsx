import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Check, Sparkles, Building2, Target } from "lucide-react";
import type { Framework } from "../types";

interface ProjectWizardProps {
  frameworks: Framework[];
  onComplete: (data: { name: string; client: string; type: "grc" | "consulting"; framework_ids?: string[] }) => void;
  onCancel: () => void;
}

export function ProjectWizard({ frameworks, onComplete, onCancel }: ProjectWizardProps) {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [client, setClient] = useState("");
  const [type, setType] = useState<"grc" | "consulting">("grc");
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);

  const toggleFramework = (id: string) => {
    setSelectedFrameworks((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  };

  const nextStep = () => setStep((s) => Math.min(s + 1, 4));
  const prevStep = () => setStep((s) => Math.max(s - 1, 1));

  const handleFinish = () => {
    onComplete({
      name,
      client: client || "Client Anonyme",
      type,
      framework_ids: type === "grc" ? selectedFrameworks : undefined,
    });
  };

  return (
    <div className="flex flex-col h-full min-h-[400px]">
      {/* Progress Bar */}
      <div className="flex items-center justify-between mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center flex-1 last:flex-none">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
              step >= i ? "bg-[var(--accent)] text-white" : "bg-[var(--bg3)] text-[var(--faint)]"
            }`}>
              {step > i ? <Check size={14} /> : i}
            </div>
            {i < 4 && (
              <div className={`flex-1 h-1 mx-2 rounded transition-colors ${
                step > i ? "bg-[var(--accent)]" : "bg-[var(--bg3)]"
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 relative overflow-hidden">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="flex flex-col gap-4"
            >
              <h2 className="text-xl font-bold mb-2">Informations de base</h2>
              <div>
                <label className="block text-sm font-medium text-[var(--soft)] mb-1">Nom du projet</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Audit Cybersécurité Q3"
                  className="w-full px-3 py-2 bg-[var(--bg2)] border border-[var(--stroke)] rounded text-[var(--fg)] focus:outline-none focus:border-[var(--accent)]"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--soft)] mb-1">Client / Organisation</label>
                <div className="relative">
                  <Building2 size={16} className="absolute left-3 top-3 text-[var(--faint)]" />
                  <input
                    type="text"
                    value={client}
                    onChange={(e) => setClient(e.target.value)}
                    placeholder="Ex: Acme Corp"
                    className="w-full pl-9 pr-3 py-2 bg-[var(--bg2)] border border-[var(--stroke)] rounded text-[var(--fg)] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="flex flex-col gap-4"
            >
              <h2 className="text-xl font-bold mb-2">Type de mission</h2>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setType("grc")}
                  className={`p-4 rounded-xl border text-left transition-colors flex flex-col gap-2 ${
                    type === "grc" ? "border-[var(--accent)] bg-[var(--accent)]/10" : "border-[var(--stroke)] bg-[var(--bg2)] hover:border-[var(--soft)]"
                  }`}
                >
                  <div className={`p-2 rounded-lg w-fit ${type === "grc" ? "bg-[var(--accent)] text-white" : "bg-[var(--bg3)] text-[var(--soft)]"}`}>
                    <Target size={20} />
                  </div>
                  <div className="font-bold">Audit GRC</div>
                  <div className="text-xs text-[var(--soft)]">Conformité par rapport à un ou plusieurs référentiels de sécurité.</div>
                </button>
                <button
                  type="button"
                  onClick={() => setType("consulting")}
                  className={`p-4 rounded-xl border text-left transition-colors flex flex-col gap-2 ${
                    type === "consulting" ? "border-[var(--accent)] bg-[var(--accent)]/10" : "border-[var(--stroke)] bg-[var(--bg2)] hover:border-[var(--soft)]"
                  }`}
                >
                  <div className={`p-2 rounded-lg w-fit ${type === "consulting" ? "bg-[var(--accent)] text-white" : "bg-[var(--bg3)] text-[var(--soft)]"}`}>
                    <Sparkles size={20} />
                  </div>
                  <div className="font-bold">Conseil & Accompagnement</div>
                  <div className="text-xs text-[var(--soft)]">Mission libre, production de livrables sur mesure sans référentiel strict.</div>
                </button>
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="flex flex-col gap-4 h-full"
            >
              <h2 className="text-xl font-bold mb-2">
                {type === "grc" ? "Choix des Référentiels" : "Options Avancées"}
              </h2>
              {type === "grc" ? (
                <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-2 max-h-[250px]">
                  {frameworks.map((fw) => (
                    <label
                      key={fw.id}
                      className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedFrameworks.includes(fw.id)
                          ? "border-[var(--accent)] bg-[var(--accent)]/5"
                          : "border-[var(--stroke)] bg-[var(--bg2)] hover:bg-[var(--bg3)]"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedFrameworks.includes(fw.id)}
                        onChange={() => toggleFramework(fw.id)}
                        className="mt-1"
                      />
                      <div>
                        <div className="font-medium text-sm text-[var(--fg)]">{fw.name}</div>
                        {fw.description && (
                          <div className="text-xs text-[var(--soft)] mt-0.5 leading-snug">{fw.description}</div>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="text-[var(--soft)] text-sm bg-[var(--bg2)] p-4 rounded-lg border border-[var(--stroke)]">
                  Aucun référentiel de conformité n'est requis pour une mission de conseil pur. 
                  Vous pourrez créer des livrables libres directement depuis l'espace de travail.
                </div>
              )}
            </motion.div>
          )}

          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="flex flex-col gap-4"
            >
              <h2 className="text-xl font-bold mb-2">Récapitulatif</h2>
              <div className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-lg p-5 space-y-4">
                <div>
                  <div className="text-xs text-[var(--soft)] uppercase font-bold tracking-wider mb-1">Projet</div>
                  <div className="font-medium">{name}</div>
                </div>
                <div>
                  <div className="text-xs text-[var(--soft)] uppercase font-bold tracking-wider mb-1">Client</div>
                  <div className="font-medium">{client || "Non spécifié"}</div>
                </div>
                <div>
                  <div className="text-xs text-[var(--soft)] uppercase font-bold tracking-wider mb-1">Type</div>
                  <div className="font-medium">
                    {type === "grc" ? "Audit de Conformité (GRC)" : "Mission de Conseil"}
                  </div>
                </div>
                {type === "grc" && selectedFrameworks.length > 0 && (
                  <div>
                    <div className="text-xs text-[var(--soft)] uppercase font-bold tracking-wider mb-1">Référentiels</div>
                    <ul className="list-disc pl-4 text-sm font-medium">
                      {selectedFrameworks.map(id => {
                        const fw = frameworks.find(f => f.id === id);
                        return <li key={id}>{fw?.name || id}</li>;
                      })}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer / Controls */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-[var(--stroke)]">
        <button
          type="button"
          onClick={step === 1 ? onCancel : prevStep}
          className="px-4 py-2 rounded text-sm font-medium text-[var(--soft)] hover:text-[var(--fg)] hover:bg-[var(--bg2)] transition-colors"
        >
          {step === 1 ? "Annuler" : "Retour"}
        </button>
        <button
          type="button"
          onClick={step === 4 ? handleFinish : nextStep}
          disabled={step === 1 && !name.trim()}
          className="flex items-center gap-2 px-6 py-2 rounded bg-[var(--accent)] text-white text-sm font-bold hover:bg-opacity-90 disabled:opacity-50 transition-all"
        >
          {step === 4 ? (
            <>
              Créer la mission <Check size={16} />
            </>
          ) : (
            <>
              Suivant <ChevronRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
