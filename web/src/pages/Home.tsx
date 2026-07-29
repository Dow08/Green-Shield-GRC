import { motion } from "framer-motion";
import { Search, Bell, ChevronRight, Boxes, Layers, Lock, MonitorSmartphone } from "lucide-react";
import type { ModuleInfo } from "../types";
import { iconFor } from "../lib/icons";

interface Props {
  modules: ModuleInfo[];
  onOpen: (id: string) => void;
}

export function Home({ modules, onOpen }: Props) {
  const active = modules.filter((m) => m.status === "active");
  const kpis = [
    { 
      icon: Boxes, 
      tile: "tile-green", 
      value: String(active.length), 
      label: "Module(s) actif(s)",
      desc: "Moteurs d'analyse statique et de conformité chargés dans la mémoire locale."
    }, 
    { 
      icon: Layers, 
      tile: "tile-violet", 
      value: String(modules.length), 
      label: "Au catalogue",
      desc: "Missions, audits de conformité réglementaire et assistants GRC prévus dans la roadmap."
    },    
    { 
      icon: Lock, 
      tile: "tile-sky", 
      value: "100%", 
      label: "Hors-ligne",
      desc: "Zéro télémétrie. Toutes les données, scans et documents restent confinés sur votre machine."
    },
    { 
      icon: MonitorSmartphone, 
      tile: "tile-amber", 
      value: "Linux · Win", 
      label: "Portable (Docker)",
      desc: "Environnement d'exécution isolé, étanche et hautement disponible par conteneur."
    },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <header className="mb-5 flex items-center gap-4">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">Bonjour, Dorian 👋</h2>
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

      {/* KPIS WITH SPECIFIC DESCRIPTIONS */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((k) => (
          <div key={k.label} className="glass p-4 flex flex-col justify-between min-h-[145px]">
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

      <div className="mb-3 text-sm font-bold text-[var(--soft)]">Modules de la plateforme</div>     
      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2">
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
                "glass flex items-center gap-3.5 p-4 text-left transition",
                isActive
                  ? "cursor-pointer hover:-translate-y-0.5 hover:bg-white/[0.07]"
                  : "cursor-default border-dashed opacity-55",
              ].join(" ")}
            >
              <div className={`tile h-[52px] w-[52px] ${isActive ? "tile-green" : "tile-muted"}`}>  
                <Icon size={24} strokeWidth={2} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-[15px] font-bold">{m.name}</h3>
                <p className="text-[12px] text-[var(--soft)] leading-normal mt-0.5">{m.description}</p>        
                {isActive ? (
                  <span className="mt-2 inline-block rounded-full bg-[rgba(46,230,160,0.12)] px-2.5 py-0.5 text-[10px] font-bold text-[var(--g1)]">
                    {m.category} · Actif
                  </span>
                ) : (
                  <span className="mt-2 inline-block rounded-full bg-white/5 px-2.5 py-0.5 text-[10px] font-bold text-[var(--faint)]">
                    À venir
                  </span>
                )}
              </div>
              {isActive && <ChevronRight className="ml-auto text-[var(--g3)] flex-shrink-0" size={18} />}
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
