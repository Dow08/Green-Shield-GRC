import { ClipboardCheck, CheckCircle2, AlertTriangle, Info, Loader2 } from "lucide-react";
import type { RevueExportResult } from "../types";

interface Props {
  revue: RevueExportResult | null;
  chargement: boolean;
  onAllerALaPhase: (phase: number) => void;
}

/**
 * Revue de complétude avant génération d'un livrable.
 *
 * Les exports remplacent toute donnée absente par « N/A » : sans cette vue, un
 * rapport peut partir chez un client criblé de trous sans que personne ne le
 * remarque. Rendre le manque visible sert directement la promesse « zéro
 * invention » — on ne comble rien, on signale.
 */
export function RevueExport({ revue, chargement, onAllerALaPhase }: Props) {
  if (chargement) {
    return (
      <div className="glass-2 p-3 text-[11px] text-[var(--soft)] flex items-center gap-2">
        <Loader2 size={13} className="animate-spin" /> Analyse de la complétude…
      </div>
    );
  }
  if (!revue) return null;

  if (revue.complet) {
    return (
      <div className="glass-2 p-3 text-[11px] text-[var(--g1)] flex items-center gap-2">
        <CheckCircle2 size={14} /> Mission complète : tous les champs repris dans les livrables sont renseignés.
      </div>
    );
  }

  const bloquants = revue.manques.filter((m) => m.gravite === "bloquant");
  const recommandes = revue.manques.filter((m) => m.gravite === "recommande");

  return (
    <div className="glass-2 p-3 flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide flex items-center gap-1.5">
          <ClipboardCheck size={12} /> Revue avant export
        </span>
        <span
          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            revue.pret_pour_export
              ? "bg-[rgba(255,207,107,0.12)] text-[var(--amber)]"
              : "bg-[rgba(255,111,145,0.12)] text-[var(--rose)]"
          }`}
        >
          {revue.bloquants > 0
            ? `${revue.bloquants} manque(s) bloquant(s)`
            : `${revue.total} point(s) à compléter`}
        </span>
      </div>

      <p className="text-[11px] text-[var(--soft)]">
        Les livrables remplacent les champs vides par «&nbsp;N/A&nbsp;». Complétez ces points
        avant de transmettre un document au client.
      </p>

      <div className="flex flex-col gap-1 max-h-52 overflow-y-auto pr-1">
        {[...bloquants, ...recommandes].map((m) => (
          <button
            key={`${m.phase}-${m.champ}`}
            type="button"
            onClick={() => onAllerALaPhase(m.phase)}
            className="text-left flex items-start gap-2 bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] rounded-lg px-2.5 py-1.5 transition"
          >
            {m.gravite === "bloquant" ? (
              <AlertTriangle size={12} className="text-[var(--rose)] shrink-0 mt-0.5" />
            ) : (
              <Info size={12} className="text-[var(--amber)] shrink-0 mt-0.5" />
            )}
            <span className="min-w-0">
              <span className="block text-[11px] text-[var(--ink)]">{m.champ}</span>
              <span className="block text-[10px] text-[var(--faint)]">
                Phase {m.phase} — {m.phase_libelle}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
