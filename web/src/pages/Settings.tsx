import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Save, Settings as SettingsIcon, ShieldCheck, Key, User, CloudLightning, AlertTriangle, Image, X } from "lucide-react";
import { safeGetItem, safeSetItem } from "../lib/storage";
import { api } from "../lib/api";
import { ReferentielsPanel } from "../components/ReferentielsPanel";
import type { Framework } from "../types";

// Formats acceptés par les générateurs de livrables (report_docx.py,
// report_html.py) — même liste des deux côtés, cf. charte.py::_type_image.
const FORMATS_LOGO_ACCEPTES = ["image/png", "image/jpeg"];
const TAILLE_LOGO_MAX_OCTETS = 300 * 1024;

// Le type MIME n'est pas reconservé au rechargement (seul le base64 brut est
// stocké, à l'identique de ce qu'attend charte.logo_bytes()) : on le retrouve
// par la signature binaire, comme le fait le serveur.
function mimeDepuisBase64(base64: string): string {
  if (base64.startsWith("/9j/")) return "image/jpeg";
  return "image/png";
}

export function Settings() {
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [apiKey, setApiKey] = useState("");
  // Base64 brut (sans le préfixe data:...;base64,) : c'est la forme attendue
  // par charte.logo_bytes() côté serveur.
  const [logoBase64, setLogoBase64] = useState("");
  const [logoErreur, setLogoErreur] = useState("");
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const logoInputRef = useRef<HTMLInputElement>(null);

  // Licence
  const [licenseKey, setLicenseKey] = useState("");
  const [licenseStatus, setLicenseStatus] = useState("");
  const [licenseError, setLicenseError] = useState("");
  const isPremium = localStorage.getItem("greenshield_premium") === "1";

  useEffect(() => {
    const savedName = safeGetItem("consultant_name");
    const savedCompany = safeGetItem("consultant_company");
    const savedEmail = safeGetItem("consultant_email");
    const savedKey = safeGetItem("copilot_api_key");
    const savedLogo = safeGetItem("consultant_logo");

    if (savedName) setName(savedName);
    if (savedCompany) setCompany(savedCompany);
    if (savedEmail) setEmail(savedEmail);
    if (savedKey) setApiKey(savedKey);
    if (savedLogo) setLogoBase64(savedLogo);
    api.frameworks.list().then(setFrameworks).catch(() => setFrameworks([]));
    
    // Fetch auth status to get current license if needed
    api.auth.me().then(data => {
        if (data.license_key) setLicenseKey(data.license_key);
    }).catch(console.error);
  }, []);

  const enregistrerReferentiel = async (data: Parameters<typeof api.frameworks.import>[0]) => {
    await api.frameworks.import(data);
    setFrameworks(await api.frameworks.list());
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fichier = e.target.files?.[0];
    e.target.value = ""; // permet de resélectionner le même fichier après un reset
    if (!fichier) return;
    setLogoErreur("");
    if (!FORMATS_LOGO_ACCEPTES.includes(fichier.type)) {
      setLogoErreur("Format non pris en charge — utilisez un PNG ou un JPEG.");
      return;
    }
    if (fichier.size > TAILLE_LOGO_MAX_OCTETS) {
      setLogoErreur(`Fichier trop volumineux (${Math.round(fichier.size / 1024)} ko) — 300 ko maximum.`);
      return;
    }
    const lecteur = new FileReader();
    lecteur.onload = () => {
      const dataUri = String(lecteur.result || "");
      setLogoBase64(dataUri.split(",", 2)[1] || "");
    };
    lecteur.onerror = () => setLogoErreur("Lecture du fichier impossible.");
    lecteur.readAsDataURL(fichier);
  };

  const handleLogoReset = () => {
    setLogoBase64("");
    setLogoErreur("");
    if (logoInputRef.current) logoInputRef.current.value = "";
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const ok = [
      safeSetItem("consultant_name", name),
      safeSetItem("consultant_company", company),
      safeSetItem("consultant_email", email),
      safeSetItem("copilot_api_key", apiKey),
      safeSetItem("consultant_logo", logoBase64),
    ].every(Boolean);
    setSaved(ok);
    setSaveError(!ok);
    setTimeout(() => { setSaved(false); setSaveError(false); }, 2500);
  };
  
  const handleActivateLicense = async () => {
    setLicenseError("");
    setLicenseStatus("");
    try {
        const res = await api.auth.activate({ license_key: licenseKey });
        setLicenseStatus(res.message);
        localStorage.setItem("greenshield_premium", "1");
        setTimeout(() => window.location.reload(), 1500);
    } catch (err: any) {
        setLicenseError(err.message || "Erreur d'activation");
    }
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
          <SettingsIcon size={20} className="text-[var(--g1)]" /> Réglages & Paramètres
        </h2>
        <p className="text-xs text-[var(--soft)] mt-0.5">
          Configurez vos préférences locales de consultant et les clés d'ingestion d'API
        </p>
      </header>

      <form onSubmit={handleSave} className="flex flex-col gap-4 max-w-xl">
        {/* CONSULTANT IDENTITY */}
        <div className="glass p-5 flex flex-col gap-3">
          <div className="text-xs font-bold text-[var(--g1)] uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <User size={14} /> Profil & Identité de l'auditeur
          </div>
          <p className="text-[11px] text-[var(--soft)] leading-normal -mt-1.5">
            Ces informations personnalisent les livrables générés (page de garde, signatures, pied de page) — chaque consultant utilisant GREEN SHIELD renseigne ici sa propre identité.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Prénom / Nom de l'auditeur</label>
              <input
                type="text"
                placeholder="ex : Camille Martin"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Cabinet / Entreprise de conseil</label>
              <input
                type="text"
                placeholder="ex : Martin Cyber Audit"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Adresse Email professionnelle</label>
              <input
                type="email"
                placeholder="ex : contact@martin-cyber-audit.fr"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-[11px] font-bold text-[var(--soft)] mb-1">Logo du cabinet (page de garde des rapports Word)</label>
              <div className="flex items-center gap-3">
                <div className="grid h-12 w-12 flex-shrink-0 place-items-center rounded-xl border border-[var(--stroke)] bg-[#04150e] overflow-hidden">
                  {logoBase64 ? (
                    <img
                      src={`data:${mimeDepuisBase64(logoBase64)};base64,${logoBase64}`}
                      alt="Logo du cabinet"
                      className="h-full w-full object-contain"
                    />
                  ) : (
                    <Image size={16} className="text-[var(--faint)]" />
                  )}
                </div>
                <label className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--ink)] transition cursor-pointer">
                  <Image size={13} /> {logoBase64 ? "Changer le logo" : "Déposer un logo"}
                  <input
                    ref={logoInputRef}
                    type="file"
                    accept="image/png,image/jpeg"
                    onChange={handleLogoChange}
                    className="hidden"
                  />
                </label>
                {logoBase64 && (
                  <button
                    type="button"
                    onClick={handleLogoReset}
                    className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-2 text-xs font-bold text-[var(--soft)] transition"
                  >
                    <X size={13} /> Revenir au logo GREEN SHIELD
                  </button>
                )}
              </div>
              <p className="text-[10px] text-[var(--faint)] mt-1.5">
                PNG ou JPEG, 300 ko maximum. Sans logo déposé, la page de garde porte le logo GREEN SHIELD par défaut.
              </p>
              {logoErreur && (
                <p className="text-[10px] font-bold text-[var(--rose)] mt-1">{logoErreur}</p>
              )}
            </div>
          </div>
        </div>

        {/* SECTION LICENCE */}
        <div className="glass p-5 flex flex-col gap-3 border-l-4 border-amber-500">
          <div className="text-xs font-bold text-amber-500 uppercase tracking-wide flex items-center gap-1.5 mb-1">
            <Key size={14} /> 
            Licence Premium
          </div>
          <p className="text-xs text-[var(--faint)]">
            Activez votre clé de licence professionnelle pour débloquer toutes les fonctionnalités avancées de GREEN SHIELD.
            {isPremium && <span className="ml-2 font-bold text-emerald-500">Statut actuel : PRO</span>}
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ex: GS-PRO-XXXX-YYYY"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              disabled={isPremium}
              className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-amber-500 disabled:opacity-50"
            />
            <button
              type="button"
              onClick={handleActivateLicense}
              disabled={isPremium || !licenseKey}
              className="bg-amber-600/20 text-amber-500 border border-amber-500/30 hover:bg-amber-600/30 font-bold px-4 py-2 rounded-xl text-xs transition disabled:opacity-50"
            >
              {isPremium ? "Activé" : "Activer"}
            </button>
          </div>
          {licenseStatus && <p className="text-[10px] font-bold text-emerald-500 mt-1">{licenseStatus}</p>}
          {licenseError && <p className="text-[10px] font-bold text-[var(--rose)] mt-1">{licenseError}</p>}
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

        {/* RÉFÉRENTIELS PERSONNELS (F2) — enrichissement au fil des missions */}
        <ReferentielsPanel
          frameworks={frameworks}
          onCharger={api.frameworks.detail}
          onEnregistrer={enregistrerReferentiel}
        />

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
