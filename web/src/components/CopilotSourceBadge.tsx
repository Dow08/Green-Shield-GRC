import type { CopilotSource, FournisseurLLM } from "../types";

const NOMS_FOURNISSEURS: Record<FournisseurLLM, string> = {
  ollama: "modèle local",
  gemini: "Gemini",
  anthropic: "Claude",
  openai: "ChatGPT",
  kimi: "Kimi",
};

/**
 * Indique d'où vient la réponse affichée.
 *
 * La distinction `local` / `online` porte l'information la plus sensible du
 * produit : une réponse locale n'a produit aucune sortie réseau, une réponse
 * en ligne a transmis la question et le contexte de mission à un tiers. Les
 * deux ne doivent jamais se ressembler à l'écran.
 */
export function CopilotSourceBadge({
  source,
  fournisseur,
}: {
  source: CopilotSource | null;
  fournisseur?: FournisseurLLM;
}) {
  if (!source) return null;

  const nom = fournisseur ? NOMS_FOURNISSEURS[fournisseur] : null;

  const LABELS: Record<CopilotSource, string> = {
    // Nommer le fournisseur réellement sollicité : « en ligne » sans préciser
    // qui laisserait le consultant ignorer chez qui sont parties ses données.
    online: nom ? `En ligne — ${nom}` : "En ligne",
    local: nom ? `Local — ${nom} (aucune sortie réseau)` : "Local — aucune sortie réseau",
    offline_fallback: "Hors-ligne (moteur indisponible, repli local)",
    offline: "Hors-ligne — intelligence locale",
  };

  const STYLES: Record<CopilotSource, string> = {
    online: "bg-amber-500/20 text-amber-300",
    local: "bg-[rgba(46,230,160,0.18)] text-[var(--g1)]",
    offline_fallback: "bg-white/10 text-[var(--faint)]",
    offline: "bg-white/10 text-[var(--faint)]",
  };

  return (
    <div
      className={`mb-2 inline-block rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${STYLES[source]}`}
    >
      {LABELS[source]}
    </div>
  );
}
