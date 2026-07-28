import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FolderKanban, Plus, ArrowLeft, Trash2, CheckCircle2, 
  RefreshCw, FileDown, Save, Bot, BookOpen, Shield,
  PlusCircle, Award, Target, Activity, HelpCircle, AlertCircle, Check
} from "lucide-react";
import { api } from "../lib/api";
import { IsoPivotView } from "../components/IsoPivotView";
import { CopilotSourceBadge } from "../components/CopilotSourceBadge";
import type {
  ProjectState, Framework, AssetMetier, AssetSupport,
  RGPDRegister, Tiers, Remediation, ManualControl, CopilotSource
} from "../types";

// Extensible and enriched dictionaries of standard cybersecurity assets
const SUGGESTED_METIER = [
  { id: "VM-BDD", name: "Base de données Clients", description: "Contient les identités, contrats et coordonnées.", is_personal_data: true },
  { id: "VM-RD", name: "Fichier de R&D / Brevets", description: "Données de propriété intellectuelle stratégique.", is_personal_data: false },
  { id: "VM-FACT", name: "Système de Facturation", description: "Données de transactions bancaires et comptables.", is_personal_data: true },
  { id: "VM-RH", name: "Dossiers RH & Fiches de Paie", description: "Données confidentielles sur les collaborateurs.", is_personal_data: true },
  { id: "VM-WEB", name: "Portail Client (E-commerce)", description: "Service web hébergeant l'expérience client active.", is_personal_data: true }
];

const SUGGESTED_SUPPORT = [
  { id: "BS-AD", name: "Active Directory (AD)", type: "Logiciel", description: "Annuaire d'identité d'administration centralisé.", owner: "Administrateur SI" },
  { id: "BS-BK", name: "Serveur de Sauvegardes", type: "Matériel", description: "Héberge les sauvegardes immuables locales.", owner: "Administrateur SI" },
  { id: "BS-FW", name: "Pare-feu de périmètre", type: "Réseau", description: "Contrôle d'accès et filtrage de flux.", owner: "Équipe Réseau" },
  { id: "BS-WORK", name: "Postes de travail", type: "Matériel", description: "Flotte d'ordinateurs d'utilisateurs avec EDR.", owner: "RSSI / SecOps" },
  { id: "BS-VPN", name: "Passerelle VPN d'accès", type: "Réseau", description: "Tunnel d'accès sécurisé pour les télétravailleurs.", owner: "Équipe Réseau" },
  { id: "BS-SIEM", name: "Console SIEM (Logs)", type: "Logiciel", description: "Centralisation et analyse des journaux d'audit.", owner: "Équipe SOC/SecOps" }
];

const SUGGESTED_RGPD = [
  { id: "RG-PAYE", name: "Gestion de la paie &amp; RH", purpose: "Virement des salaires et suivi de carrières.", data_categories: "NIR, Coordonnées bancaires, Échelon", retention: "5 ans" },
  { id: "RG-CRM", name: "Gestion de la Relation Client (CRM)", purpose: "Suivi commercial et prospection.", data_categories: "Nom, Prénom, Téléphone, Email", retention: "Fin de relation + 3 ans" },
  { id: "RG-MESS", name: "Messagerie Professionnelle (Email)", purpose: "Communication interne et externe des collaborateurs.", data_categories: "Email, Logs de connexion, Contenu des flux", retention: "1 an (logs)" }
];

export function Projects() {
  const [projects, setProjects] = useState<ProjectState[]>([]);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [activeProject, setActiveProject] = useState<ProjectState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Project creation form state
  const [showCreate, setShowCreate] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectClient, setNewProjectClient] = useState("");
  const [newProjectType, setNewProjectType] = useState<"grc" | "consulting">("consulting");
  const [selectedFramework, setSelectedFramework] = useState("iso27001");
  
  // Stepper state
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [auditing, setAuditing] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Help slideout state
  const [activeHelp, setActiveHelp] = useState<string | null>(null);

  // Copilot AI state
  const [copilotPrompt, setCopilotPrompt] = useState("");
  const [copilotResponse, setCopilotResponse] = useState("");
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotSource, setCopilotSource] = useState<CopilotSource | null>(null);

  // --- Dynamic triggerable popover dropdown states (The instant selection request) ---
  const [showMetierMenu, setShowMetierMenu] = useState(false);
  const [showCustomMetier, setShowCustomMetier] = useState(false);
  const [customMetierData, setCustomMetierData] = useState({ name: "", description: "", is_personal_data: false });

  const [showSupportMenu, setShowSupportMenu] = useState(false);
  const [showCustomSupport, setShowCustomSupport] = useState(false);
  const [customSupportData, setCustomSupportData] = useState({ name: "", type: "Logiciel", description: "", owner: "DSI" });

  const [showRgpdMenu, setShowRgpdMenu] = useState(false);
  const [showCustomRgpd, setShowCustomRgpd] = useState(false);
  const [customRgpdData, setCustomRgpdData] = useState({ name: "", purpose: "", data_categories: "", retention: "5 ans" });

  // Quick form states for other steps
  const [newTiers, setNewTiers] = useState({ name: "", dependence: 3, penetration: 3, maturity: 3, trust: 3 });
  const [newRemediation, setNewRemediation] = useState<Remediation>({ id: "REM-05", axe: "Protection", measure: "Durcir la politique de mot de passe administrateur.", priority: "Élevé" });

  useEffect(() => {
    loadProjectsAndFrameworks();
  }, []);

  const loadProjectsAndFrameworks = () => {
    setLoading(true);
    setError(null);
    Promise.all([api.projects.list(), api.frameworks.list()])
      .then(([pList, fList]) => {
        setProjects(pList);
        setFrameworks(fList);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Erreur de chargement");
      })
      .finally(() => setLoading(false));
  };

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    
    api.projects.create({
      name: newProjectName,
      client: newProjectClient || "Client",
      type: newProjectType,
      framework_id: newProjectType === "grc" ? selectedFramework : undefined
    })
    .then((created) => {
      setShowCreate(false);
      setNewProjectName("");
      setNewProjectClient("");
      setActiveProject(created);
      setCurrentStep(1);
      loadProjectsAndFrameworks();
    })
    .catch((err) => alert(err instanceof Error ? err.message : "Échec de la création"));
  };

  const handleDeleteProject = (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Avoid selecting project card
    if (!confirm("Voulez-vous vraiment supprimer définitivement ce rapport d'audit et toutes ses données associées ?")) return;
    
    api.projects.delete(id)
      .then(() => {
        loadProjectsAndFrameworks();
        if (activeProject?.id === id) {
          setActiveProject(null);
        }
      })
      .catch((err) => alert("Échec suppression : " + err.message));
  };

  const handleSelectProject = (id: string) => {
    api.projects.get(id)
      .then((proj) => {
        setActiveProject(proj);
        setCurrentStep(1);
        setCopilotResponse("");
        setCopilotSource(null);
        setActiveHelp(null);
        setShowMetierMenu(false);
        setShowCustomMetier(false);
        setShowSupportMenu(false);
        setShowCustomSupport(false);
        setShowRgpdMenu(false);
        setShowCustomRgpd(false);
      })
      .catch((err) => alert(err instanceof Error ? err.message : "Échec d'ouverture"));
  };

  const handleSaveProject = () => {
    if (!activeProject) return;
    setSaving(true);
    api.projects.update(activeProject.id, activeProject)
      .then((updated) => {
        setActiveProject(updated);
        loadProjectsAndFrameworks();
      })
      .catch((err) => alert("Erreur sauvegarde: " + err.message))
      .finally(() => setSaving(false));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!activeProject || !e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    const file = e.target.files[0];
    api.projects.upload(activeProject.id, file)
      .then((updated) => {
        setActiveProject(updated);
      })
      .catch((err) => alert("Échec téléversement : " + err.message))
      .finally(() => setUploading(false));
  };

  const handleTriggerAudit = () => {
    if (!activeProject) return;
    setAuditing(true);
    api.projects.runAudit(activeProject.id)
      .then((updated) => {
        setActiveProject(updated);
      })
      .catch((err) => alert("Échec audit technique : " + err.message))
      .finally(() => setAuditing(false));
  };

  const handleExportDoc = (docType: string) => {
    if (!activeProject) return;
    api.projects.exportDoc(activeProject.id, docType)
      .then((res) => {
        const blob = new Blob([res.markdown], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = res.title;
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch((err) => alert("Échec de la génération : " + err.message));
  };

  const handleRunCopilot = () => {
    if (!activeProject || !copilotPrompt.trim()) return;
    setCopilotLoading(true);
    setCopilotResponse("");
    setCopilotSource(null);

    // Call custom copilot API — utilise la clé Gemini/OpenAI configurée dans les Réglages
    // si présente (analyse générative en ligne), sinon l'API bascule sur l'intelligence
    // experte locale hors-ligne.
    const storedKey = localStorage.getItem("copilot_api_key") || "";
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

  // --- Step mutations helper ---
  const updateStepData = (stepKey: string, fieldKey: string, value: any) => {
    if (!activeProject) return;
    const steps = { ...activeProject.steps } as any;
    steps[stepKey] = { ...steps[stepKey], [fieldKey]: value };
    setActiveProject({ ...activeProject, steps });
  };

  // TPRM Calculator helper
  const addTiersHelper = () => {
    if (!activeProject || !newTiers.name.trim()) return;
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

  // Global project statistics calculation
  const totalProjects = projects.length;
  const avgCompletion = totalProjects > 0 
    ? Math.round(projects.reduce((acc, p) => acc + p.progress, 0) / totalProjects)
    : 0;
  const grcCount = projects.filter(p => p.type === "grc").length;
  const consultingCount = projects.filter(p => p.type === "consulting").length;

  return (
    <div className="flex flex-col h-full overflow-y-auto pr-2 relative">
      {/* HEADER SECTION */}
      <header className="mb-4 flex items-center gap-3">
        {activeProject ? (
          <button 
            onClick={() => { setActiveProject(null); loadProjectsAndFrameworks(); }}
            className="flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white/[0.045] px-3 py-1.5 text-xs font-bold text-[var(--soft)] transition hover:bg-white/[0.08]"
          >
            <ArrowLeft size={14} /> Retour
          </button>
        ) : null}
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">
            {activeProject ? activeProject.name : "Registre des Missions &amp; Projets"}
          </h2>
          <p className="text-xs text-[var(--soft)] mt-0.5">
            {activeProject 
              ? `${activeProject.client} · Mode ${activeProject.type.toUpperCase()}`
              : "Pilotez vos audits de conformité GRC et missions de conseil cyber en local"
            }
          </p>
        </div>
        
        {activeProject && (
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={handleSaveProject}
              disabled={saving}
              className="flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white/[0.045] px-4 py-2 text-xs font-bold text-[var(--g1)] transition hover:bg-[rgba(46,230,160,0.1)] disabled:opacity-50 animate-pulse"
            >
              <Save size={13} className={saving ? "animate-spin" : ""} /> Enregistrer l'état
            </button>
          </div>
        )}
      </header>

      {error && (
        <div className="glass border-[rgba(255,111,145,0.4)] p-4 text-[var(--rose)] mb-4 text-xs">
          Une erreur est survenue : {error}
        </div>
      )}

      {/* NO ACTIVE PROJECT: MAIN PROJECTS SELECTION DASHBOARD WITH SVG GRAPHICS */}
      {!activeProject && !loading && (
        <div className="flex-1 flex flex-col gap-4">
          
          {/* STATS DIAGRAM DASHBOARD */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* SVG Average Progress Circle */}
            <div className="glass-2 p-4 flex items-center gap-4 min-h-[120px]">
              <svg width="70" height="70" className="flex-shrink-0">
                <circle cx="35" cy="35" r="30" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="6" />
                <circle 
                  cx="35" cy="35" r="30" fill="none" stroke="url(#g1)" strokeWidth="6"
                  strokeDasharray={`${2 * Math.PI * 30}`}
                  strokeDashoffset={`${2 * Math.PI * 30 * (1 - avgCompletion / 100)}`}
                  strokeLinecap="round"
                  transform="rotate(-90 35 35)"
                />
                <defs>
                  <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--g1)" />
                    <stop offset="100%" stopColor="var(--g3)" />
                  </linearGradient>
                </defs>
                <text x="35" y="39" textAnchor="middle" fill="var(--ink)" fontSize="12" fontWeight="bold">
                  {avgCompletion}%
                </text>
              </svg>
              <div className="text-xs">
                <h4 className="font-bold text-[var(--ink)]">Complétion moyenne</h4>
                <p className="text-[var(--soft)] mt-0.5">Avancement général consolidé de toutes les missions en cours.</p>
              </div>
            </div>

            {/* SVG active count bar chart */}
            <div className="glass-2 p-4 flex flex-col justify-between min-h-[120px]">
              <div className="text-xs">
                <h4 className="font-bold text-[var(--ink)]">Répartition des missions</h4>
                <p className="text-[var(--soft)] mt-0.5">{totalProjects} projet(s) au total dans l'application.</p>
              </div>
              <div className="flex items-center gap-2 mt-2 h-[35px]">
                {/* Visual bar graph representation */}
                <div className="flex-1 h-3 rounded-full overflow-hidden flex bg-white/[0.03]">
                  <div className="bg-[var(--sky)] h-full" style={{ width: `${(grcCount / (totalProjects || 1)) * 100}%` }} title="GRC" />
                  <div className="bg-[#b3a8ff] h-full" style={{ width: `${(consultingCount / (totalProjects || 1)) * 100}%` }} title="Conseil" />
                </div>
                <div className="text-[10px] text-[var(--soft)] flex flex-col gap-0.5">
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--sky)]" /> GRC : {grcCount}</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#b3a8ff]" /> Conseil : {consultingCount}</span>
                </div>
              </div>
            </div>

            {/* General helper explanation info card */}
            <div className="glass-2 p-4 flex items-start gap-3 min-h-[120px] border-[rgba(46,230,160,0.15)] border">
              <Shield size={20} className="text-[var(--g1)] flex-shrink-0 mt-0.5" />
              <div className="text-xs">
                <h4 className="font-bold text-[var(--ink)]">Garantie 100 % Réel &amp; Hygiène</h4>
                <p className="text-[var(--soft)] mt-0.5 leading-normal">
                  Chaque rapport d'audit correspond à des configurations réelles éditables. Le « Bouclier » (AuditCraft) réalise des analyses de sécurité authentiques sur vos configurations d'administration.
                </p>
              </div>
            </div>

          </div>

          <div className="flex justify-between items-center mt-2">
            <div className="text-xs font-bold text-[var(--faint)]">Projets en cours ({projects.length})</div>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 rounded-full bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3.5 py-1.5 text-xs font-bold text-[#04150e] transition hover:opacity-90"
            >
              <Plus size={14} /> Nouveau Projet
            </button>
          </div>

          {/* CREATE PROJECT FORM */}
          {showCreate && (
            <motion.form 
              initial={{ opacity: 0, y: -10 }} 
              animate={{ opacity: 1, y: 0 }}
              onSubmit={handleCreateProject}
              className="glass p-5 border-[var(--g3)] border flex flex-col gap-3.5 bg-[var(--bg2)]"
            >
              <div className="text-sm font-bold text-[var(--g3)] mb-1">Paramètres de la Mission</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[var(--soft)] mb-1">Nom de la mission *</label>
                  <input
                    type="text"
                    required
                    placeholder="ex: Accompagnement ISO 27001"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[var(--soft)] mb-1">Client / Entreprise</label>
                  <input
                    type="text"
                    placeholder="ex: Banque Populaire"
                    value={newProjectClient}
                    onChange={(e) => setNewProjectClient(e.target.value)}
                    className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[var(--soft)] mb-1">Type d'Accompagnement</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setNewProjectType("consulting")}
                      className={`flex-1 py-2 rounded-xl border text-xs font-bold transition ${newProjectType === "consulting" ? "bg-[rgba(46,230,160,0.12)] border-[var(--g1)] text-[var(--g1)]" : "border-[var(--stroke)] text-[var(--soft)] bg-white/[0.02]"}`}
                    >
                      Conseil &amp; Analyse EBIOS RM
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setNewProjectType("grc");
                        setSelectedFramework("iso27001");
                      }}
                      className={`flex-1 py-2 rounded-xl border text-xs font-bold transition ${newProjectType === "grc" ? "bg-[rgba(46,230,160,0.12)] border-[var(--g1)] text-[var(--g1)]" : "border-[var(--stroke)] text-[var(--soft)] bg-white/[0.02]"}`}
                    >
                      Audit de Conformité GRC
                    </button>
                  </div>
                </div>

                {newProjectType === "grc" && (
                  <div>
                    <label className="block text-xs font-bold text-[var(--soft)] mb-1">Référentiel GRC principal</label>
                    <select
                      value={selectedFramework}
                      onChange={(e) => setSelectedFramework(e.target.value)}
                      className="w-full bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                    >
                      {frameworks.map((f) => (
                        <option key={f.id} value={f.id}>{f.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div className="flex gap-2 justify-end mt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 border border-[var(--stroke)] rounded-full text-xs text-[var(--soft)] hover:bg-white/5"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-[var(--g1)] text-[#04150e] font-bold rounded-full text-xs hover:opacity-90"
                >
                  Créer la mission
                </button>
              </div>
            </motion.form>
          )}

          {/* PROJECTS GRID */}
          {projects.length === 0 ? (
            <div className="glass p-12 text-center text-[var(--soft)] flex flex-col items-center justify-center gap-3">
              <FolderKanban size={32} className="text-[var(--faint)]" />
              <div>
                <p className="font-bold text-sm text-[var(--ink)]">Aucun projet actif</p>
                <p className="text-xs mt-1">Créez votre première mission pour activer le guidage pas-à-pas.</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map((p) => (
                <div 
                  key={p.id} 
                  onClick={() => handleSelectProject(p.id)}
                  className="glass-2 p-4 flex flex-col gap-3 cursor-pointer hover:bg-white/[0.04] hover:-translate-y-0.5 transition relative group animate-fade-in"
                >
                  <div className="flex justify-between items-start pr-8">
                    <div>
                      <h3 className="font-bold text-sm text-[var(--ink)]">{p.name}</h3>
                      <p className="text-xs text-[var(--soft)] mt-0.5">{p.client}</p>
                    </div>
                    <span className={`rounded-full px-2.5 py-0.5 text-[9px] font-extrabold ${p.type === "grc" ? "bg-[rgba(92,200,255,0.12)] text-[var(--sky)]" : "bg-[rgba(139,123,255,0.12)] text-[#b3a8ff]"}`}>
                      {p.type === "grc" ? "GRC" : "CONSEIL & RISQUES"}
                    </span>
                  </div>

                  {/* Absolute positioning of red delete button inside cards */}
                  <button
                    onClick={(e) => handleDeleteProject(p.id, e)}
                    className="absolute top-4 right-4 text-[var(--soft)] hover:text-[var(--rose)] opacity-0 group-hover:opacity-100 transition p-1 hover:bg-white/5 rounded-lg"
                    title="Supprimer définitivement ce projet"
                  >
                    <Trash2 size={14} />
                  </button>

                  {/* Progress Bar */}
                  <div className="flex items-center gap-3 mt-1.5">
                    <div className="flex-1 bg-white/[0.05] h-1.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-[var(--g1)] to-[var(--g3)] h-full transition-all duration-300" 
                        style={{ width: `${p.progress}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-bold text-[var(--g1)]">{p.progress}%</span>
                  </div>

                  <div className="flex justify-between text-[10px] text-[var(--faint)] border-t border-white/[0.03] pt-2 mt-1">
                    <span>Créé le : {p.created_at.split(" ")[0]}</span>
                    <span>Modifié le : {p.updated_at}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ACTIVE WORKSPACE: GUIDED MANUEL (6 PHASES STEPPER) */}
      {activeProject && (
        <div className="flex-1 flex flex-col gap-4">
          
          {/* STEPPER TOP PROGRESS BAR (6 PHASES) */}
          <div className="glass-2 px-4 py-3 flex flex-col md:flex-row gap-3 md:items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-xs font-bold">Progression Mission :</div>
              <div className="w-[120px] bg-white/[0.05] h-2 rounded-full overflow-hidden">
                <div className="bg-[var(--g1)] h-full" style={{ width: `${activeProject.progress}%` }} />
              </div>
              <span className="text-xs font-bold text-[var(--g1)]">{activeProject.progress}%</span>
            </div>

            {/* Stepper controls */}
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5, 6].map((num) => {
                const stepKey = ["cadrage", "diagnostic", "tprm", "ebios", "resilience", "traitement"][num - 1];
                const isStepValidated = (activeProject.steps as any)[stepKey]?.validated;
                return (
                  <button
                    key={num}
                    onClick={() => setCurrentStep(num)}
                    className={`grid h-7 w-7 place-items-center rounded-lg text-xs font-bold transition relative ${currentStep === num ? "bg-[var(--g1)] text-[#04150e]" : isStepValidated ? "bg-[rgba(46,230,160,0.12)] text-[var(--g1)] border border-[var(--g1)]" : "bg-white/[0.04] text-[var(--soft)] hover:bg-white/10"}`}
                  >
                    {isStepValidated ? <Check size={11} strokeWidth={3} /> : num}
                  </button>
                );
              })}
              {/* 7e onglet : parcours GRC pivot ISO 27001 piloté par workflow.yaml
                  (Jalon 1). Volontairement séparé des 6 étapes historiques ci-dessus
                  plutôt que d'y être mêlé — cf. docs/audit-critique-plan.md F4. */}
              {activeProject.type === "grc" && (
                <button
                  onClick={() => setCurrentStep(7)}
                  className={`ml-1 flex h-7 items-center gap-1 rounded-lg px-2 text-[10.5px] font-bold transition ${currentStep === 7 ? "bg-[var(--g1)] text-[#04150e]" : "bg-white/[0.04] text-[var(--soft)] hover:bg-white/10"}`}
                >
                  <Shield size={11} /> ISO 27001
                </button>
              )}
              <div className="text-[11px] font-bold text-[var(--soft)] ml-2">
                {currentStep === 7 ? (
                  "Parcours GRC pivot — ISO/IEC 27001:2022"
                ) : (
                  <>
                    P{currentStep} : {
                      [
                        "Cadrage & Patrimoine",
                        "Diagnostic & RGPD",
                        "Risques Tiers (TPRM)",
                        "Analyse Menaces (EBIOS)",
                        "Résilience & E3R",
                        "Traitement & Copilote"
                      ][currentStep - 1]
                    }
                  </>
                )}
              </div>
            </div>
          </div>

          {/* ACTIVE STEP WORKSPACE */}
          <div className="flex-1 min-h-0 bg-white/[0.01] border border-[var(--stroke)] rounded-2xl p-5 overflow-y-auto">
            
            {/* ========================================================
                PHASE 1: CADRAGE ET PATRIMOINE
                ======================================================== */}
            {currentStep === 1 && (
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
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setShowMetierMenu(!showMetierMenu)}
                        className="flex items-center gap-1 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-1 text-xs font-bold text-[var(--g1)] transition cursor-pointer"
                      >
                        <Plus size={14} /> Ajouter une valeur métier...
                      </button>

                      {showMetierMenu && (
                        <div className="absolute right-0 mt-1.5 w-64 rounded-xl bg-[#091510] border border-[var(--stroke)] shadow-2xl z-50 p-2 text-xs flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-[var(--faint)] uppercase px-2 py-1">Gabarits types</div>
                          {SUGGESTED_METIER.map((m) => (
                            <button
                              key={m.id}
                              type="button"
                              onClick={() => {
                                const list = [...(activeProject.steps.cadrage?.assets_metier || [])];
                                list.push({
                                  id: m.id + "-" + String(Math.floor(Math.random() * 90) + 10),
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
                              id: "VM-" + String(Math.floor(Math.random() * 90) + 10),
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
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setShowSupportMenu(!showSupportMenu)}
                        className="flex items-center gap-1 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-1 text-xs font-bold text-[var(--g1)] transition cursor-pointer"
                      >
                        <Plus size={14} /> Ajouter un bien support...
                      </button>

                      {showSupportMenu && (
                        <div className="absolute right-0 mt-1.5 w-64 rounded-xl bg-[#091510] border border-[var(--stroke)] shadow-2xl z-50 p-2 text-xs flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-[var(--faint)] uppercase px-2 py-1">Gabarits types</div>
                          {SUGGESTED_SUPPORT.map((s) => (
                            <button
                              key={s.id}
                              type="button"
                              onClick={() => {
                                const list = [...(activeProject.steps.cadrage?.assets_support || [])];
                                list.push({
                                  id: s.id + "-" + String(Math.floor(Math.random() * 90) + 10),
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
                              id: "BS-" + String(Math.floor(Math.random() * 90) + 10),
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
            )}

            {/* ========================================================
                PHASE 2: DIAGNOSTIC ET RGPD (WITH INTERACTIVE INSTRUCTION PANELS)
                ======================================================== */}
            {currentStep === 2 && (
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
                      Gestion des Vulnérabilités (CIS 7)
                    </label>
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
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setShowRgpdMenu(!showRgpdMenu)}
                        className="flex items-center gap-1 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-3 py-1 text-xs font-bold text-[var(--g1)] transition cursor-pointer"
                      >
                        <Plus size={14} /> Ajouter un traitement...
                      </button>

                      {showRgpdMenu && (
                        <div className="absolute right-0 mt-1.5 w-64 rounded-xl bg-[#091510] border border-[var(--stroke)] shadow-2xl z-50 p-2 text-xs flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-[var(--faint)] uppercase px-2 py-1">Traitements standards</div>
                          {SUGGESTED_RGPD.map((r) => (
                            <button
                              key={r.id}
                              type="button"
                              onClick={() => {
                                const list = [...(activeProject.steps.diagnostic?.rgpd_register || [])];
                                list.push({
                                  id: r.id + "-" + String(Math.floor(Math.random() * 90) + 10),
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
                              id: "RGPD-" + String(Math.floor(Math.random() * 90) + 10),
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
            )}

            {/* ========================================================
                PHASE 3: ECOSYSTEME ET RISQUES TIERS (TPRM) - WITH SLIDER VALUE INDICATION
                ======================================================== */}
            {currentStep === 3 && (
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
            )}

            {/* ========================================================
                PHASE 4: ANALYSE DES MENACES (EBIOS RM / REAL AUTOMATED CONFIG AUDIT)
                ======================================================== */}
            {currentStep === 4 && (
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
                    {activeProject.steps.ebios?.operational_scenarios?.map((s: any, idx: number) => (
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
                    {activeProject.steps.ebios?.case_studies?.map((c: any, idx: number) => (
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
            )}

            {/* ========================================================
                PHASE 5: RESILIENCE ET CRUISE (E3R / MANUAL COMPLIANCE CHECKLIST)
                ======================================================== */}
            {currentStep === 5 && (
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
            )}

            {/* ========================================================
                PHASE 6: TRAITEMENT ET COPILOTE
                ======================================================== */}
            {currentStep === 6 && (
              <div className="flex flex-col gap-4">
                <div className="text-sm font-bold text-[var(--g1)] border-b border-white/[0.04] pb-1.5 flex items-center gap-2">
                  <Bot size={15} /> 6. Feuille de Route de Traitement &amp; Copilote Cyber AI
                </div>

                {/* PLAN D'ACTIONS (REMEDIATIONS) */}
                <div>
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-1.5 uppercase tracking-wide">A. Plan d'Action de Remédiation (4 Axes Cyber)</div>
                  <div className="flex flex-col gap-2">
                    {activeProject.steps.traitement?.remediations?.map((r: Remediation, idx: number) => (
                      <div key={idx} className="bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs flex justify-between items-center">
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
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Add Remediation Form */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mt-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
                    <input
                      type="text" placeholder="ID (ex: REM-05)" value={newRemediation.id}
                      onChange={(e) => setNewRemediation({ ...newRemediation, id: e.target.value })}
                      className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                    />
                    <select
                      value={newRemediation.axe}
                      onChange={(e) => setNewRemediation({ ...newRemediation, axe: e.target.value as any })}
                      className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                    >
                      <option value="Gouvernance">Gouvernance</option>
                      <option value="Protection">Protection</option>
                      <option value="Défense">Défense</option>
                      <option value="Résilience">Résilience</option>
                    </select>
                    <select
                      value={newRemediation.priority}
                      onChange={(e) => setNewRemediation({ ...newRemediation, priority: e.target.value as any })}
                      className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2 py-1.5 focus:outline-none text-[var(--ink)]"
                    >
                      <option value="Critique">Critique</option>
                      <option value="Élevé">Élevé</option>
                      <option value="Moyen">Moyen</option>
                      <option value="Faible">Faible</option>
                    </select>
                    <div className="flex gap-2">
                      <input
                        type="text" placeholder="Mesure de sécurité à appliquer" value={newRemediation.measure}
                        onChange={(e) => setNewRemediation({ ...newRemediation, measure: e.target.value })}
                        className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (!newRemediation.id.trim() || !newRemediation.measure.trim()) return;
                          const list = [...(activeProject.steps.traitement?.remediations || [])];
                          list.push(newRemediation);
                          updateStepData("traitement", "remediations", list);
                          setNewRemediation({ id: "REM-" + String(Math.floor(Math.random() * 90) + 10), axe: "Protection", measure: "", priority: "Élevé" });
                        }}
                        className="bg-[var(--g1)] text-[#04150e] p-1.5 rounded-xl hover:opacity-90"
                      >
                        <Plus size={15} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* THE CYBERDEPART (6 PRIORITES) */}
                <div className="mt-2 border-t border-white/[0.04] pt-3">
                  <div className="text-[11px] font-bold text-[var(--soft)] mb-2 uppercase tracking-wide">B. Le Cyberdépart (6 Mesures d'hygiène vitales prioritaires - ANSSI)</div>
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
                  <div className="text-[11px] font-bold text-[var(--soft)] uppercase tracking-wide">C. Téléchargement des rapports multi-formats (Impression PDF / Word)</div>
                  
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handleExportDoc("nda")}
                      className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-4 py-2.5 text-xs font-bold text-[var(--ink)] transition"
                    >
                      <FileDown size={14} /> Exporter NDA (Contrat).md
                    </button>
                    <button
                      onClick={() => handleExportDoc("ebios")}
                      className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-4 py-2.5 text-xs font-bold text-[var(--ink)] transition"
                    >
                      <FileDown size={14} /> Exporter Analyse EBIOS RM.md
                    </button>
                    <button
                      onClick={() => handleExportDoc("pssi_pri")}
                      className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-4 py-2.5 text-xs font-bold text-[var(--ink)] transition"
                    >
                      <FileDown size={14} /> Exporter PSSI &amp; Plan PRI.md
                    </button>
                    <button
                      onClick={() => handleExportDoc("aipd")}
                      className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-4 py-2.5 text-xs font-bold text-[var(--ink)] transition"
                    >
                      <FileDown size={14} /> Exporter AIPD / PIA (RGPD).md
                    </button>
                    {activeProject.type === "grc" && (
                      <button
                        onClick={() => handleExportDoc("audit_report")}
                        className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-[var(--stroke)] hover:bg-white/[0.08] px-4 py-2.5 text-xs font-bold text-[var(--ink)] transition"
                      >
                        <FileDown size={14} /> Exporter Rapport GRC Complet.md
                      </button>
                    )}
                    <a
                      href={api.projects.reportDocxUrl(activeProject.id)}
                      download
                      className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-4 py-2.5 text-xs font-bold text-[#04150e] hover:opacity-90 transition"
                    >
                      <FileDown size={14} /> Rapport d'audit (Word .docx)
                    </a>
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
            )}

            {/* ========================================================
                ONGLET 7 : PARCOURS GRC PIVOT — ISO 27001 (Jalon 1)
                ======================================================== */}
            {currentStep === 7 && (
              <IsoPivotView project={activeProject} onChange={setActiveProject} />
            )}

          </div>
        </div>
      )}
    </div>
  );
}
