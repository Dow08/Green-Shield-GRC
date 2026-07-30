import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FolderKanban, Plus, ArrowLeft, Trash2, Save, Shield, Check, FlaskConical, Clock, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";
import { formatDuree } from "../lib/duree";
import { IsoPivotView } from "../components/IsoPivotView";
import { TempsPanel } from "../components/TempsPanel";
import { ArchivePanel } from "../components/ArchivePanel";
import { HistoriquePanel } from "../components/HistoriquePanel";
import { RgpdPanel } from "../components/RgpdPanel";
import { SoclePanel } from "../components/SoclePanel";
import { PhaseCadrage } from "../components/phases/PhaseCadrage";
import { PhaseDiagnostic } from "../components/phases/PhaseDiagnostic";
import { PhaseTprm } from "../components/phases/PhaseTprm";
import { PhaseEbios } from "../components/phases/PhaseEbios";
import { PhaseResilience } from "../components/phases/PhaseResilience";
import { PhaseTraitement } from "../components/phases/PhaseTraitement";
import type { ProjectState, Framework, PhaseTemps, RevueExportResult, SnapshotInfo, EcheanceRgpdMission, CouvertureTechnique } from "../types";

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
  const [revue, setRevue] = useState<RevueExportResult | null>(null);
  const [revueEnCours, setRevueEnCours] = useState(false);
  const [instantanes, setInstantanes] = useState<SnapshotInfo[]>([]);
  const [echeanceRgpd, setEcheanceRgpd] = useState<EcheanceRgpdMission | null>(null);
  // Alertes d'échéances RGPD sur tout le portefeuille — auparavant il fallait
  // ouvrir chaque mission une à une pour découvrir une échéance dépassée.
  const [echeancesPortefeuille, setEcheancesPortefeuille] = useState<EcheanceRgpdMission[]>([]);
  const [couverture, setCouverture] = useState<CouvertureTechnique | null>(null);
  const [saving, setSaving] = useState(false);
  const [auditing, setAuditing] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Help slideout state

  // Copilot AI state

  // --- Dynamic triggerable popover dropdown states (The instant selection request) ---



  // Quick form states for other steps

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
    // Best-effort : une alerte RGPD manquante ne doit jamais bloquer le
    // chargement du registre.
    api.projects.echeancesRgpd().then(setEcheancesPortefeuille).catch(() => setEcheancesPortefeuille([]));
  };

  useEffect(() => {
    loadProjectsAndFrameworks();
  }, []);

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
        chargerRevue(proj.id);
        // L'état d'interface propre à chaque phase (menus ouverts, brouillons
        // de formulaire) est réinitialisé par le remontage des composants de
        // phase, dont la `key` est l'identifiant de mission.
      })
      .catch((err) => alert(err instanceof Error ? err.message : "Échec d'ouverture"));
  };

  // La revue reflète l'état enregistré : on la recharge à l'ouverture d'une
  // mission et après chaque sauvegarde, pas à chaque frappe.
  const chargerRevue = (id: string) => {
    setRevueEnCours(true);
    api.projects.revue(id)
      .then(setRevue)
      .catch(() => setRevue(null))
      .finally(() => setRevueEnCours(false));
    api.projects.snapshots(id).then(setInstantanes).catch(() => setInstantanes([]));
    api.projects.couverture(id).then(setCouverture).catch(() => setCouverture(null));
    api.projects.echeancesRgpd()
      .then((toutes) => setEcheanceRgpd(toutes.find((e) => e.project_id === id) ?? null))
      .catch(() => setEcheanceRgpd(null));
  };

  const handleRestaurerInstantane = async (nom: string) => {
    if (!activeProject) return;
    const restaure = await api.projects.restoreSnapshot(activeProject.id, nom);
    setActiveProject(restaure);
    loadProjectsAndFrameworks();
    chargerRevue(restaure.id);
  };

  const handleEnregistrerRgpd = async (politique: { duree_conservation_mois: number; date_fin_mission: string }) => {
    if (!activeProject) return;
    const maj = await api.projects.updateRgpd(activeProject.id, politique);
    setActiveProject(maj);
    chargerRevue(maj.id);
  };

  const handlePurgerRgpd = async () => {
    if (!activeProject) return;
    const resultat = await api.projects.purgerRgpd(activeProject.id);
    setActiveProject(resultat.state);
    chargerRevue(resultat.state.id);
  };

  const handleCreerDemo = () => {
    api.projects.createDemo()
      .then((demo) => {
        loadProjectsAndFrameworks();
        setActiveProject(demo);
        setCurrentStep(1);
        chargerRevue(demo.id);
      })
      .catch((err) => alert("Échec de la création de la démo : " + err.message));
  };

  const handleSaveProject = () => {
    if (!activeProject) return;
    setSaving(true);
    api.projects.update(activeProject.id, activeProject)
      .then((updated) => {
        setActiveProject(updated);
        loadProjectsAndFrameworks();
        chargerRevue(updated.id);
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

  // Le backend renvoie la mission entière après mutation : on réaligne l'état
  // local dessus plutôt que de recalculer le journal de temps côté client.
  const handleAddTemps = async (entry: { phase: PhaseTemps; minutes: number; note: string }) => {
    if (!activeProject) return;
    setActiveProject(await api.projects.addTemps(activeProject.id, entry));
  };

  const handleDeleteTemps = async (entryId: string) => {
    if (!activeProject) return;
    try {
      setActiveProject(await api.projects.deleteTemps(activeProject.id, entryId));
    } catch (err) {
      alert("Échec de la suppression : " + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleExportArchive = async (password: string) => {
    if (!activeProject) return;
    const blob = await api.projects.exportArchive(activeProject.id, password);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mission_${activeProject.id}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImportArchive = async (file: File, password: string) => {
    const restauree = await api.projects.importArchive(file, password);
    loadProjectsAndFrameworks();
    setActiveProject(restauree);
  };


  // --- Step mutations helper ---
  const updateStepData = (stepKey: string, fieldKey: string, value: unknown) => {
    if (!activeProject) return;
    // steps est hétérogène par construction (chaque étape a sa propre forme) :
    // ce pont dynamique est le seul endroit qui a besoin de s'en abstraire.
    const steps = { ...activeProject.steps } as Record<string, Record<string, unknown>>;
    steps[stepKey] = { ...steps[stepKey], [fieldKey]: value };
    setActiveProject({ ...activeProject, steps } as ProjectState);
  };

  // TPRM Calculator helper

  // Global project statistics calculation
  const totalProjects = projects.length;
  const avgCompletion = totalProjects > 0 
    ? Math.round(projects.reduce((acc, p) => acc + p.progress, 0) / totalProjects)
    : 0;
  const grcCount = projects.filter(p => p.type === "grc").length;
  const consultingCount = projects.filter(p => p.type === "consulting").length;
  // Alertes d'échéances RGPD : échue en priorité, sinon imminente (≤30 jours).
  const echeancesEchues = echeancesPortefeuille.filter((e) => e.statut === "echue");
  const echeancesImminentes = echeancesPortefeuille.filter(
    (e) => e.statut === "en_conservation" && e.jours_restants !== null && e.jours_restants <= 30
  );
  // Charges consommées sur l'ensemble du portefeuille (reste de F19) : le
  // cumul n'était visible qu'une mission à la fois.
  const minutesPortefeuille = projects.reduce(
    (acc, p) => acc + (p.socle?.temps?.entrees ?? []).reduce((s, e) => s + (e.minutes || 0), 0),
    0,
  );
  const missionsAvecTemps = projects.filter(
    (p) => (p.socle?.temps?.entrees ?? []).length > 0,
  ).length;

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

            {/* Charges consommées sur le portefeuille (reste de F19) */}
            <div className="glass-2 p-4 flex flex-col justify-between min-h-[120px]">
              <div className="text-xs">
                <h4 className="font-bold text-[var(--ink)] flex items-center gap-1.5">
                  <Clock size={13} className="text-[var(--g1)]" /> Charges consommées
                </h4>
                <p className="text-[var(--soft)] mt-0.5">
                  {missionsAvecTemps} mission(s) sur {totalProjects} avec du temps saisi.
                </p>
              </div>
              <div className="mt-2">
                <span className="text-xl font-extrabold text-[var(--g1)]">{formatDuree(minutesPortefeuille)}</span>
                {minutesPortefeuille === 0 && (
                  <p className="text-[10px] text-[var(--faint)] mt-1">
                    Saisissez le temps passé dans chaque mission pour suivre vos charges face au budget vendu.
                  </p>
                )}
              </div>
            </div>

          </div>

          {/* Alertes d'échéances RGPD (F17) — proactives, sur tout le
              portefeuille : auparavant il fallait ouvrir chaque mission une à
              une pour découvrir une échéance dépassée. */}
          {(echeancesEchues.length > 0 || echeancesImminentes.length > 0) && (
            <div className="glass-2 p-3 border border-[rgba(255,107,107,0.25)] rounded-2xl flex flex-col gap-1.5">
              {echeancesEchues.length > 0 && (
                <div className="flex items-start gap-2 text-xs">
                  <AlertTriangle size={14} className="text-[var(--rose)] flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[var(--rose)]">
                      {echeancesEchues.length} mission(s) avec une échéance de conservation dépassée
                    </span>
                    <span className="text-[var(--soft)]"> — les données personnelles des personnes interrogées devraient être purgées : </span>
                    {echeancesEchues.map((e, i) => (
                      <span key={e.project_id}>
                        {i > 0 && ", "}
                        <button
                          type="button"
                          onClick={() => handleSelectProject(e.project_id)}
                          className="underline decoration-dotted text-[var(--ink)] hover:text-[var(--rose)]"
                        >
                          {e.project_name}
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {echeancesImminentes.length > 0 && (
                <div className="flex items-start gap-2 text-xs">
                  <AlertTriangle size={14} className="text-[var(--amber)] flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[var(--amber)]">
                      {echeancesImminentes.length} mission(s) avec une échéance de conservation à moins de 30 jours
                    </span>
                    <span className="text-[var(--soft)]"> : </span>
                    {echeancesImminentes.map((e, i) => (
                      <span key={e.project_id}>
                        {i > 0 && ", "}
                        <button
                          type="button"
                          onClick={() => handleSelectProject(e.project_id)}
                          className="underline decoration-dotted text-[var(--ink)] hover:text-[var(--amber)]"
                        >
                          {e.project_name}
                        </button>
                        {" "}({e.jours_restants} j)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-between items-center mt-2">
            <div className="text-xs font-bold text-[var(--faint)]">Projets en cours ({projects.length})</div>
            <div className="flex items-center gap-2">
              {/* F16 — démontrer l'outil sans jamais ouvrir une mission cliente. */}
              <button
                onClick={handleCreerDemo}
                title="Crée une mission fictive pour démonstration (aucune donnée client)"
                className="flex items-center gap-1.5 rounded-full border border-[var(--stroke)] bg-white/[0.04] px-3.5 py-1.5 text-xs font-bold text-[var(--soft)] transition hover:bg-white/[0.08] hover:text-[var(--ink)]"
              >
                <FlaskConical size={14} /> Mission de démo
              </button>
              <button
                onClick={() => setShowCreate(true)}
                className="flex items-center gap-1.5 rounded-full bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-3.5 py-1.5 text-xs font-bold text-[#04150e] transition hover:opacity-90"
              >
                <Plus size={14} /> Nouveau Projet
              </button>
            </div>
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
                    aria-label={`Supprimer définitivement la mission ${p.name}`}
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
                const isStepValidated = (activeProject.steps as Record<string, { validated?: boolean }>)[stepKey]?.validated;
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

          {/* SOCLE DE MISSION — cadrage contractuel repris au rapport d'audit.
              Modélisé depuis le jalon 1, sans écran jusqu'au 30/07/2026. */}
          <SoclePanel
            key={`socle-${activeProject.id}`}
            socle={activeProject.socle ?? {}}
            onChange={(socle) => setActiveProject({ ...activeProject, socle })}
          />

          {/* SUIVI DU TEMPS CONSOMMÉ (F19) — charges consommées vs budget vendu */}
          <TempsPanel
            entrees={activeProject.socle?.temps?.entrees ?? []}
            budget={activeProject.socle?.qualification?.budget}
            onAdd={handleAddTemps}
            onDelete={handleDeleteTemps}
          />

          {/* SAUVEGARDE / PORTABILITÉ (F14, F15) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ArchivePanel
              missionName={activeProject.name}
              onExport={handleExportArchive}
              onImport={handleImportArchive}
            />
            <HistoriquePanel instantanes={instantanes} onRestaurer={handleRestaurerInstantane} />
          </div>

          {/* F17 — conservation des données personnelles collectées en entretien */}
          <RgpdPanel
            key={activeProject.id}
            echeance={echeanceRgpd}
            donneesPersonnelles={echeanceRgpd?.donnees_personnelles ?? 0}
            onEnregistrer={handleEnregistrerRgpd}
            onPurger={handlePurgerRgpd}
          />

          {/* ACTIVE STEP WORKSPACE */}
          <div className="flex-1 min-h-0 bg-white/[0.01] border border-[var(--stroke)] rounded-2xl p-5 overflow-y-auto">
            
            {/* ========================================================
                PHASE 1: CADRAGE ET PATRIMOINE
                ======================================================== */}
            {currentStep === 1 && (
              <PhaseCadrage
              key={activeProject.id}
                activeProject={activeProject}
                updateStepData={updateStepData}
                handleSaveProject={handleSaveProject}
              />
            )}

            {/* ========================================================
                PHASE 2: DIAGNOSTIC ET RGPD (WITH INTERACTIVE INSTRUCTION PANELS)
                ======================================================== */}
            {currentStep === 2 && (
              <PhaseDiagnostic
              key={activeProject.id}
                activeProject={activeProject}
                updateStepData={updateStepData}
                handleSaveProject={handleSaveProject}
              />
            )}

            {/* ========================================================
                PHASE 3: ECOSYSTEME ET RISQUES TIERS (TPRM) - WITH SLIDER VALUE INDICATION
                ======================================================== */}
            {currentStep === 3 && (
              <PhaseTprm
              key={activeProject.id}
                activeProject={activeProject}
                updateStepData={updateStepData}
                handleSaveProject={handleSaveProject}
                onProjectReplaced={setActiveProject}
              />
            )}

            {/* ========================================================
                PHASE 4: ANALYSE DES MENACES (EBIOS RM / REAL AUTOMATED CONFIG AUDIT)
                ======================================================== */}
            {currentStep === 4 && (
              <PhaseEbios
              key={activeProject.id}
              couverture={couverture}
                activeProject={activeProject}
                updateStepData={updateStepData}
                handleSaveProject={handleSaveProject}
                handleFileUpload={handleFileUpload}
                handleTriggerAudit={handleTriggerAudit}
                uploading={uploading}
                auditing={auditing}
              />
            )}

            {/* ========================================================
                PHASE 5: RESILIENCE ET CRUISE (E3R / MANUAL COMPLIANCE CHECKLIST)
                ======================================================== */}
            {currentStep === 5 && (
              <PhaseResilience
              key={activeProject.id}
                activeProject={activeProject}
                updateStepData={updateStepData}
                handleSaveProject={handleSaveProject}
              />
            )}

            {/* ========================================================
                PHASE 6: TRAITEMENT ET COPILOTE
                ======================================================== */}
            {currentStep === 6 && (
              <PhaseTraitement
              key={activeProject.id}
              revue={revue}
              revueEnCours={revueEnCours}
              onAllerALaPhase={setCurrentStep}
                activeProject={activeProject}
                updateStepData={updateStepData}
                handleSaveProject={handleSaveProject}
                handleExportDoc={handleExportDoc}
              />
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
