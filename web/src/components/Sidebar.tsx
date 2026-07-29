import { LayoutGrid, Settings, X } from "lucide-react";
import type { ModuleInfo } from "../types";
import { iconFor } from "../lib/icons";
import { useDismissOnOutsideOrEscape } from "../lib/useDismissOnOutsideOrEscape";

interface Props {
  view: string;
  onNavigate: (view: string) => void;
  modules: ModuleInfo[];
  /** Ouverture du tiroir en dessous du point de rupture `md`. Sans effet au-delà. */
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ view, onNavigate, modules, isOpen, onClose }: Props) {
  const ref = useDismissOnOutsideOrEscape<HTMLElement>(isOpen, onClose);

  // Naviguer referme le tiroir : sur mobile il recouvre le contenu qu'on vient
  // justement de demander.
  const naviguer = (destination: string) => {
    onNavigate(destination);
    onClose();
  };

  return (
    <>
      {/* Voile mobile : rend le clic extérieur évident et isole le tiroir. */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        ref={ref}
        className={[
          "w-[76px] flex-col items-center gap-2 border-r border-[var(--stroke)] py-4 flex-shrink-0",
          // Sous `md` : tiroir superposé. Fond OPAQUE — le fond translucide du
          // bureau laisserait le contenu transparaître à travers le tiroir.
          "fixed inset-y-0 left-0 z-50 bg-[var(--bg2)]",
          // Ouverture par `hidden`/`flex` plutôt que par un glissement.
          // `translate-x-*` (qui écrit la propriété CSS `translate` en
          // Tailwind v4) et les décalages arbitraires négatifs se sont tous
          // deux révélés inopérants ici, vérification navigateur à l'appui :
          // le tiroir restait visible une fois fermé. Cf. CLAUDE.md — vérifier
          // les classes v4 avant de les recopier d'un exemple v3.
          isOpen ? "flex" : "hidden",
          // À partir de `md` : rail statique toujours visible, comme avant.
          "md:static md:z-auto md:flex md:bg-white/[0.02]",
        ].join(" ")}
      >
        <div className="tile mb-2 h-[42px] w-[42px] overflow-hidden shadow-[0_8px_20px_rgba(46,230,160,0.4)]">
          <img src="/logo.png" alt="GREEN SHIELD" className="h-full w-full object-cover" />
        </div>

        {/* Fermeture explicite : le clic extérieur ne suffit pas au clavier. */}
        <NavButton active={false} label="Fermer le menu" onClick={onClose} className="md:hidden">
          <X size={19} strokeWidth={2} />
        </NavButton>

        <NavButton active={view === "home"} label="Accueil" onClick={() => naviguer("home")}>
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
              onClick={() => !disabled && naviguer(m.id)}
            >
              <Icon size={19} strokeWidth={2} />
            </NavButton>
          );
        })}

        <div className="flex-1" />

        <NavButton active={view === "settings"} label="Réglages &amp; Paramètres" onClick={() => naviguer("settings")}>
          <Settings size={19} strokeWidth={2} />
        </NavButton>
        <div className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-[#3a4d5a] to-[#22323c] text-sm font-bold text-[#cfe]">
          DP
        </div>
      </aside>
    </>
  );
}

function NavButton({
  active,
  disabled,
  label,
  onClick,
  className = "",
  children,
}: {
  active: boolean;
  disabled?: boolean;
  label: string;
  onClick: () => void;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
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
        className,
      ].join(" ")}
    >
      {children}
    </button>
  );
}
