import type { CopilotSource } from "../types";

const LABELS: Record<CopilotSource, string> = {
  online: "En ligne — Gemini",
  offline_fallback: "Hors-ligne (clé indisponible, repli local)",
  offline: "Hors-ligne — intelligence locale",
};

export function CopilotSourceBadge({ source }: { source: CopilotSource | null }) {
  if (!source) return null;
  return (
    <div
      className={`mb-2 inline-block rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
        source === "online" ? "bg-purple-500/20 text-purple-300" : "bg-white/10 text-[var(--faint)]"
      }`}
    >
      {LABELS[source]}
    </div>
  );
}
