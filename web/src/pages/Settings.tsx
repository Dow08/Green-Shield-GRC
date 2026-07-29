import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Save, Settings as SettingsIcon, ShieldCheck, Key, User, CloudLightning, AlertTriangle } from "lucide-react";
import { safeGetItem, safeSetItem } from "../lib/storage";

export function Settings() {
  const [name, setName] = useState("Dorian");
  const [company, setCompany] = useState("DP Cyber Consulting");
  const [email, setEmail] = useState("dorian@dp-cyber.fr");
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(false);

  useEffect(() => {
    const savedName = safeGetItem("consultant_name");
    const savedCompany = safeGetItem("consultant_company");
    const savedEmail = safeGetItem("consultant_email");
    const savedKey = safeGetItem("copilot_api_key");

    if (savedName) setName(savedName);
    if (savedCompany) setCompany(savedCompany);
    if (savedEmail) setEmail(savedEmail);
    if (savedKey) setApiKey(savedKey);
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const ok = [
      safeSetItem("consultant_name", name),
      safeSetItem("consultant_company", company),
      safeSetItem("consultant_email", email),
      safeSetItem("copilot_api_key", apiKey),
    ].every(Boolean);
    setSaved(ok);
    setSaveError(!ok);
    setTimeout(() => { setSaved(false); setSaveError(false); }, 2500);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 8 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.3 }}
      className="flex flex-col h-full overflow-y-auto pr-2"
    >
      <header className="mb-5">
        <h2 className="text-xl font-extrabold tracking-tight flex items-center gap-2">
          <SettingsIcon size={20} className="text-[var(--g1)]" /> Réglages &amp; Paramètres
        </h2>
        <p className="text-xs text-[var(--soft)] mt-0.5">
          Configurez vos préférences locales de consultant et les clés d'ingestion d'API
        </p>
      </header>

      <form onSubmit={handleSave} className="flex flex-col gap-4 max-w-xl">
        {/* CONSULTANT IDENTITY */}
        <div className="glass p-5 flex flex-col gap-3">
          <div className="text-xs font-bold text-[var(--g1)] uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <User size={14} /> Profil &amp; Identité de l'auditeur (DP Cyber Consulting)
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Prénom / Nom de l'auditeur</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Cabinet / Entreprise de conseil</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Adresse Email professionnelle</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
            </div>
          </div>
        </div>

        {/* API COPILOTE KEY */}
        <div className="glass p-5 flex flex-col gap-3">
          <div className="text-xs font-bold text-[var(--g3)] uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <Key size={14} /> Clé d'API du Copilote Cyber (LLM)
          </div>
          <p className="text-[11px] text-[var(--soft)] leading-normal">
            Saisissez votre clé API Gemini ou OpenAI pour activer le Copilote cyber génératif en ligne. Sans clé, l'application utilise l'intelligence experte locale pré-configurée (100% hors-ligne).
          </p>
          <div className="text-xs">
            <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Clé d'API Privée (Souveraine)</label>
            <input
              type="password"
              placeholder="AIzaSy..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] font-mono focus:outline-none focus:border-[var(--g3)]"
            />
          </div>
        </div>

        {/* COMPLIANCE AND SOVEREIGNTY NOTIFICATION */}
        <div className="glass-2 p-4 border-[rgba(46,230,160,0.2)] border flex items-start gap-3">
          <ShieldCheck size={20} className="text-[var(--g1)] flex-shrink-0 mt-0.5" />
          <div className="text-xs text-[var(--soft)] leading-relaxed">
            <strong className="text-[var(--ink)]">Données confinées sur votre machine :</strong> Conformément à la charte de confidentialité de GREEN SHIELD, toutes les informations de votre profil et de vos clés d'API sont sauvegardées localement de manière sécurisée dans l'espace de stockage de votre propre navigateur (`localStorage`). Aucune donnée n'est transmise ou collectée par des serveurs tiers externes.
          </div>
        </div>

        <div className="flex items-center gap-4 mt-2">
          <button
            type="submit"
            className="flex items-center gap-2 rounded-full bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-5 py-2.5 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
          >
            <Save size={14} /> Sauvegarder les configurations
          </button>
          
          {saved && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }} 
              animate={{ opacity: 1, x: 0 }} 
              className="text-xs font-bold text-[var(--g1)] flex items-center gap-1"
            >
              <CloudLightning size={13} /> Configurations enregistrées localement !
            </motion.div>
          )}

          {saveError && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-xs font-bold text-[var(--rose)] flex items-center gap-1"
            >
              <AlertTriangle size={13} /> Échec de l'enregistrement local (mode privé ou stockage plein ?)
            </motion.div>
          )}
        </div>
      </form>
    </motion.div>
  );
}
