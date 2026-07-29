import { useState } from "react";
import { History, RotateCcw, Loader2 } from "lucide-react";
import type { SnapshotInfo } from "../types";

interface Props {
  instantanes: SnapshotInfo[];
  onRestaurer: (nom: string) => Promise<void>;
}

/**
 * Historique versionné d'une mission (F9).
 *
 * Un instantané est pris à chaque validation de phase : c'est le jalon métier
 * qui mérite d'être versionné. Restaurer instantane d'abord l'état courant —
 * un retour en arrière ne doit jamais être un aller sans retour.
 */
export function HistoriquePanel({ instantanes, onRestaurer }: Props) {
  const [enCours, setEnCours] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const [erreur, setErreur] = useState("");

  const restaurer = async (nom: string) => {
    setEnCours(nom);
    setErreur("");
    try {
      await onRestaurer(nom);
      setConfirmation(null);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Échec de la restauration.");
    } finally {
      setEnCours(null);
    }
  };

  return (
    <div className="glass p-4 flex flex-col gap-2.5">
      <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide flex items-center gap-1.5">
        <History size={12} /> Historique de la mission
      </span>

      {instantanes.length === 0 ? (
        <p className="text-[11px] text-[var(--soft)] italic">
          Aucun point de restauration. Un instantané est enregistré automatiquement
          à chaque validation de phase.
        </p>
      ) : (
        <div className="flex flex-col gap-1 max-h-52 overflow-y-auto pr-1">
          {instantanes.map((s) => (
            <div
              key={s.nom}
              className="flex items-center justify-between gap-2 bg-white/[0.02] border border-white/[0.04] rounded-lg px-2.5 py-1.5 text-[11px]"
            >
              <div className="min-w-0">
                <span className="block text-[var(--ink)] truncate">{s.motif}</span>
                <span className="block text-[10px] text-[var(--faint)] font-mono">{s.date}</span>
              </div>

              {confirmation === s.nom ? (
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="text-[10px] text-[var(--amber)]">Écraser l'état actuel ?</span>
                  <button
                    type="button"
                    onClick={() => restaurer(s.nom)}
                    disabled={enCours !== null}
                    className="bg-[var(--g1)] text-[#04150e] font-bold rounded px-2 py-0.5 text-[10px] disabled:opacity-40"
                  >
                    {enCours === s.nom ? <Loader2 size={11} className="animate-spin" /> : "Confirmer"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmation(null)}
                    className="text-[var(--soft)] hover:text-[var(--ink)] text-[10px] px-1"
                  >
                    Annuler
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirmation(s.nom)}
                  aria-label={`Restaurer l'état du ${s.date}`}
                  className="shrink-0 flex items-center gap-1 text-[var(--soft)] hover:text-[var(--g1)] hover:bg-white/5 rounded px-1.5 py-1 transition"
                >
                  <RotateCcw size={12} /> <span className="text-[10px]">Restaurer</span>
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {erreur && <div className="text-[11px] text-[var(--rose)]">{erreur}</div>}

      <p className="text-[10px] text-[var(--faint)]">
        L'état actuel est lui-même sauvegardé avant toute restauration.
      </p>
    </div>
  );
}
