import { motion } from "framer-motion";
import { Search, Bell, ChevronRight, Boxes, Lock, Activity, FolderKanban } from "lucide-react";
import { useEffect, useState } from "react";
import type { ModuleInfo, ProjectState } from "../types";
import { iconFor } from "../lib/icons";
import { safeGetItem } from "../lib/storage";
import { api } from "../lib/api";
import { NeuralMap } from "../components/NeuralMap";

interface Props {
  modules: ModuleInfo[];
  onOpen: (id: string) => void;
}

export function Home({ modules, onOpen }: Props) {
  const [projects, setProjects] = useState<ProjectState[]>([]);
  const activeModules = modules.filter((m) => m.status === "active");
  const prenom = (safeGetItem("consultant_name") ?? "").trim().split(" ")[0];

  useEffect(() => {
    api.projects.list().then(setProjects).catch(console.error);
  }, []);

  const kpis = [
    { 
      icon: FolderKanban, 
      tile: "tile-green", 
      value: String(projects.length), 
      label: "Missions en cours",
      desc: "Audits et accompagnements GRC actuellement pilotés."
    }, 
    { 
      icon: Activity, 
      tile: "tile-violet", 
      value: `${projects.filter(p => p.type === "grc").length}`, 
      label: "Missions ISO 27001",
      desc: "Projets utilisant le parcours pivot de conformité."
    },    
    { 
      icon: Lock, 
      tile: "tile-sky", 
      value: "100%", 
      label: "Confidentialité locale",
      desc: "Data masking actif sur tous vos projets."
    },
    { 
      icon: Boxes, 
      tile: "tile-amber", 
      value: String(activeModules.length), 
      label: "Modules IA",
      desc: "Copilote et moteurs d'analyse disponibles."
    },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="h-full flex flex-col">
      <header className="mb-5 flex items-center gap-4 flex-none">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">{prenom ? `Bonjour, ${prenom}` : "Bonjour"} 👋</h2>
          <p className="mt-0.5 text-sm text-[var(--soft)]">Voici l'état de votre plateforme d'audit et de conseil cyber.</p>
        </div>
        <div className="ml-auto flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white/[0.045] px-4 py-2.5 text-sm text-[var(--faint)]">
          <Search size={15} /> Rechercher un module, un constat…
        </div>
        <button
          type="button"
          className="grid h-[42px] w-[42px] place-items-center rounded-2xl border border-[var(--stroke)] bg-white/[0.045] text-[var(--soft)]"
          aria-label="Notifications"
        >
          <Bell size={16} />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto pr-2 pb-4 flex flex-col xl:flex-row gap-6">
        
        {/* Colonne de gauche : KPIs & Modules */}
        <div className="flex-1 flex flex-col gap-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {kpis.map((k) => (
              <div key={k.label} className="glass p-4 flex flex-col justify-between min-h-[140px]">
                <div>
                  <div className={`tile ${k.tile} mb-2.5 h-10 w-10`}>
                    <k.icon size={18} strokeWidth={2.2} />
                  </div>
                  <div className="text-xl font-extrabold tracking-tight">{k.value}</div>
                  <div className="text-xs font-bold text-[var(--ink)] mt-0.5">{k.label}</div>
                </div>
                <div className="text-[10px] text-[var(--soft)] leading-normal border-t border-white/[0.02] pt-2 mt-2">
                  {k.desc}
                </div>
              </div>
            ))}
          </div>

          <div>
            <div className="mb-3 text-sm font-bold text-[var(--soft)] flex items-center justify-between">
              <span>Modules de la plateforme</span>
            </div>     
            <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
              {modules.map((m, i) => {
                const Icon = iconFor(m.icon);
                const isActive = m.status === "active";
                return (
                  <motion.button
                    key={m.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.28, delay: 0.04 * i }}
                    onClick={() => isActive && onOpen(m.id)}
                    disabled={!isActive}
                    className={[
                      "glass flex flex-col gap-2 p-4 text-left transition h-[150px]",
                      isActive
                        ? "cursor-pointer hover:-translate-y-0.5 hover:bg-white/[0.07]"
                        : "cursor-default border-dashed opacity-55",
                    ].join(" ")}
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div className={`tile h-[42px] w-[42px] shrink-0 ${isActive ? "tile-green" : "tile-muted"}`}>  
                        <Icon size={20} strokeWidth={2} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-[14px] font-bold truncate">{m.name}</h3>
                        {isActive && (
                          <span className="inline-block rounded-full bg-[rgba(46,230,160,0.12)] px-2 py-0.5 text-[9px] font-bold text-[var(--g1)] mt-0.5">
                            {m.category}
                          </span>
                        )}
                      </div>
                      {isActive && <ChevronRight className="text-[var(--g3)] flex-shrink-0" size={16} />}
                    </div>
                    
                    <p className="text-[11px] text-[var(--soft)] leading-relaxed flex-1 mt-1">
                      {m.description}
                    </p>        
                  </motion.button>
                );
              })}
            </div>
          </div>

        </div>

        {/* Colonne de droite : Carte Neurale */}
        <div className="xl:w-[450px] shrink-0 flex flex-col gap-4">
          <NeuralMap />
          
          <div className="glass-2 p-5 rounded-2xl flex-1 border border-white/5 bg-gradient-to-b from-white/[0.02] to-transparent">
            <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-[var(--soft)]">
              <Activity size={16} /> Activité Récente
            </h3>
            {projects.length > 0 ? (
              <div className="flex flex-col gap-3">
                {projects.slice(0, 4).map((p) => (
                  <div key={p.id} onClick={() => onOpen("missions")} className="group cursor-pointer flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-[var(--stroke)] hover:bg-white/[0.05] transition">
                    <div className="w-2 h-2 rounded-full bg-[var(--g1)] shrink-0 shadow-[0_0_8px_var(--g1)]" />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold text-[var(--ink)] truncate">{p.name}</div>
                      <div className="text-[10px] text-[var(--faint)]">{p.client}</div>
                    </div>
                    <ChevronRight size={14} className="text-[var(--soft)] opacity-0 group-hover:opacity-100 transition -translate-x-2 group-hover:translate-x-0" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-[var(--faint)] italic text-center py-10">
                Aucune mission en cours. Lancez le Registre de missions ou utilisez le Copilote pour démarrer.
              </div>
            )}
          </div>
        </div>

      </div>
    </motion.div>
  );
}
