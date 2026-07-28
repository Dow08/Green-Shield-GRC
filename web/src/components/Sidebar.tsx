import type { ComponentType } from "react";
import { Shield, LayoutGrid, FolderKanban, Bot, Radar, Settings } from "lucide-react";
import type { ModuleInfo } from "../types";

// Correspondance nom d'icône (API) → composant lucide (icônes rondes/modernes).
const ICONS: Record<string, ComponentType<{ size?: number; strokeWidth?: number }>> = {
  shield: Shield,
  missions: FolderKanban,
  copilot: Bot,
  collect: Radar,
};

export function iconFor(name: string): ComponentType<{ size?: number; strokeWidth?: number }> {     
  return ICONS[name] ?? Shield;
}

interface Props {
  view: string;
  onNavigate: (view: string) => void;
  modules: ModuleInfo[];
}

export function Sidebar({ view, onNavigate, modules }: Props) {
  return (
    <aside className="flex w-[76px] flex-col items-center gap-2 border-r border-[var(--stroke)] bg-white/[0.02] py-4 flex-shrink-0">
      <div className="tile tile-green mb-2 h-[42px] w-[42px] shadow-[0_8px_20px_rgba(46,230,160,0.4)]">
        <Shield size={20} strokeWidth={2.2} />
      </div>

      <NavButton active={view === "home"} label="Accueil" onClick={() => onNavigate("home")}>       
        <LayoutGrid size={19} strokeWidth={2} />
      </NavButton>

      {modules.map((m) => {
        const Icon = iconFor(m.icon);
        const disabled = m.status !== "active";
        return (
          <NavButton
            key={m.id}
            active={view === m.id}
            disabled={disabled}
            label={m.name}
            onClick={() => !disabled && onNavigate(m.id)}
          >
            <Icon size={19} strokeWidth={2} />
          </NavButton>
        );
      })}

      <div className="flex-1" />

      {/* Activated Settings cog button */}
      <NavButton active={view === "settings"} label="Réglages &amp; Paramètres" onClick={() => onNavigate("settings")}>
        <Settings size={19} strokeWidth={2} />
      </NavButton>
      <div className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-[#3a4d5a] to-[#22323c] text-sm font-bold text-[#cfe]">
        DP
      </div>
    </aside>
  );
}

function NavButton({
  active,
  disabled,
  label,
  onClick,
  children,
}: {
  active: boolean;
  disabled?: boolean;
  label: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className={[
        "grid h-[46px] w-[46px] place-items-center rounded-2xl transition",
        disabled ? "cursor-not-allowed opacity-40" : "cursor-pointer",
        active
          ? "bg-gradient-to-br from-[rgba(46,230,160,0.22)] to-[rgba(25,198,198,0.12)] text-[var(--g3)] shadow-[inset_0_0_0_1px_rgba(46,230,160,0.3)]"
          : "text-[var(--soft)] hover:bg-white/5 hover:text-[var(--ink)]",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
