import { motion } from "framer-motion";
import { Search, Bell, ChevronRight, Boxes, Layers, Lock, MonitorSmartphone } from "lucide-react";
import type { ModuleInfo } from "../types";
import { iconFor } from "../components/Sidebar";

interface Props {
  modules: ModuleInfo[];
  onOpen: (id: string) => void;
}

export function Home({ modules, onOpen }: Props) {
  const active = modules.filter((m) => m.status === "active");
  const kpis = [
    { icon: Boxes, tile: "tile-green", value: String(active.length), label: "Module(s) actif(s)" },
    { icon: Layers, tile: "tile-violet", value: String(modules.length), label: "Au catalogue" },
    { icon: Lock, tile: "tile-sky", value: "100%", label: "Hors-ligne" },
    { icon: MonitorSmartphone, tile: "tile-amber", value: "Linux · Win", label: "Portable (Docker)" },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <header className="mb-5 flex items-center gap-4">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">Bonjour, Dorian 👋</h2>
          <p className="mt-0.5 text-sm text-[var(--soft)]">Voici l'état de ta plateforme d'audit.</p>
        </div>
        <div className="ml-auto flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white/[0.045] px-4 py-2.5 text-sm text-[var(--faint)]">
          <Search size={15} /> Rechercher un module, un constat…
        </div>
        <button className="grid h-[42px] w-[42px] place-items-center rounded-2xl border border-[var(--stroke)] bg-white/[0.045] text-[var(--soft)]">
          <Bell size={16} />
        </button>
      </header>

      <div className="mb-6 grid grid-cols-2 gap-3.5 md:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="glass p-4">
            <div className={`tile ${k.tile} mb-3 h-11 w-11`}>
              <k.icon size={20} strokeWidth={2.2} />
            </div>
            <div className="text-2xl font-extrabold tracking-tight">{k.value}</div>
            <div className="mt-0.5 text-xs text-[var(--soft)]">{k.label}</div>
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
              <div className="min-w-0">
                <h3 className="text-[15px] font-bold">{m.name}</h3>
                <p className="truncate text-[12.5px] text-[var(--soft)]">{m.description}</p>
                {isActive ? (
                  <span className="mt-1.5 inline-block rounded-full bg-[rgba(46,230,160,0.12)] px-2.5 py-0.5 text-[10.5px] font-bold text-[var(--g1)]">
                    {m.category} · Actif
                  </span>
                ) : (
                  <span className="mt-1.5 inline-block rounded-full bg-white/5 px-2.5 py-0.5 text-[10.5px] font-bold text-[var(--faint)]">
                    À venir
                  </span>
                )}
              </div>
              {isActive && <ChevronRight className="ml-auto text-[var(--g3)]" size={20} />}
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
