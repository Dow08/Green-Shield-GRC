import { useState } from "react";
import { Clock, Plus, Trash2, Loader2 } from "lucide-react";
import { formatDuree } from "../lib/duree";
import type { PhaseTemps, TempsEntree } from "../types";

const PHASES: { value: PhaseTemps; label: string }[] = [
  { value: "cadrage", label: "1. Cadrage" },
  { value: "diagnostic", label: "2. Diagnostic & RGPD" },
  { value: "tprm", label: "3. Risques Tiers" },
  { value: "ebios", label: "4. EBIOS RM" },
  { value: "resilience", label: "5. Résilience" },
  { value: "traitement", label: "6. Traitement" },
  { value: "autre", label: "Autre (coordination, déplacement…)" },
];

const LABEL_PAR_PHASE = Object.fromEntries(PHASES.map((p) => [p.value, p.label])) as Record<PhaseTemps, string>;

interface Props {
  entrees: TempsEntree[];
  budget?: string;
  onAdd: (entry: { phase: PhaseTemps; minutes: number; note: string }) => Promise<void> | void;
  onDelete: (entryId: string) => Promise<void> | void;
}

export function TempsPanel({ entrees, budget, onAdd, onDelete }: Props) {
  const [phase, setPhase] = useState<PhaseTemps>("cadrage");
  const [duree, setDuree] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [erreur, setErreur] = useState("");

  const total = entrees.reduce((sum, e) => sum + (e.minutes || 0), 0);

  const parMoisPhase = PHASES.map((p) => ({
    ...p,
    minutes: entrees.filter((e) => e.phase === p.value).reduce((s, e) => s + (e.minutes || 0), 0),
  })).filter((p) => p.minutes > 0);

  const handleAdd = async () => {
    const minutes = Number(duree);
    if (!Number.isFinite(minutes) || minutes <= 0) {
      setErreur("Saisissez une durée en minutes (nombre supérieur à 0).");
      return;
    }
    setErreur("");
    setBusy(true);
    try {
      await onAdd({ phase, minutes, note });
      setDuree("");
      setNote("");
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Échec de l'enregistrement.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="glass p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide flex items-center gap-1.5">
          <Clock size={12} /> Temps consommé
        </span>
        <div className="flex items-center gap-3 text-xs">
          <span className="font-extrabold text-[var(--g1)]">{formatDuree(total)}</span>
          {budget ? (
            <span className="text-[var(--soft)]">
              Budget vendu : <strong className="text-[var(--ink)]">{budget}</strong>
            </span>
          ) : null}
        </div>
      </div>

      {parMoisPhase.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {parMoisPhase.map((p) => (
            <span key={p.value} className="text-[10px] bg-white/5 text-[var(--soft)] rounded-full px-2 py-0.5">
              {p.label} · <strong className="text-[var(--ink)]">{formatDuree(p.minutes)}</strong>
            </span>
          ))}
        </div>
      )}

      {/* Saisie */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr_auto] gap-2 items-center">
        <select
          value={phase}
          onChange={(e) => setPhase(e.target.value as PhaseTemps)}
          aria-label="Phase concernée"
          className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
        >
          {PHASES.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
        <input
          type="number"
          min={1}
          placeholder="minutes"
          value={duree}
          onChange={(e) => setDuree(e.target.value)}
          aria-label="Durée en minutes"
          className="w-24 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
        />
        <input
          type="text"
          placeholder="Note (optionnel)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          aria-label="Note"
          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
        />
        <button
          type="button"
          onClick={handleAdd}
          disabled={busy}
          className="bg-[var(--g1)] text-[#04150e] font-bold rounded-xl px-3 py-1.5 text-xs hover:opacity-90 disabled:opacity-40 flex items-center gap-1"
        >
          {busy ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />} Ajouter
        </button>
      </div>

      {erreur && <div className="text-[11px] text-[var(--rose)]">{erreur}</div>}

      {/* Journal */}
      {entrees.length === 0 ? (
        <p className="text-[11px] text-[var(--soft)] italic">
          Aucun temps saisi pour l'instant. Les durées enregistrées ici alimentent le suivi « charges consommées vs budget ».
        </p>
      ) : (
        <div className="flex flex-col gap-1 max-h-44 overflow-y-auto pr-1">
          {[...entrees].reverse().map((e) => (
            <div key={e.id} className="flex items-center justify-between gap-2 bg-white/[0.02] border border-white/[0.04] rounded-lg px-2.5 py-1.5 text-[11px]">
              <div className="min-w-0 flex items-center gap-2">
                <span className="font-mono text-[var(--faint)] shrink-0">{e.date}</span>
                <span className="text-[var(--ink)] shrink-0">{LABEL_PAR_PHASE[e.phase] ?? e.phase}</span>
                {e.note && <span className="text-[var(--soft)] truncate">— {e.note}</span>}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="font-bold text-[var(--g1)]">{formatDuree(e.minutes)}</span>
                <button
                  type="button"
                  onClick={() => onDelete(e.id)}
                  aria-label={`Supprimer l'entrée de temps du ${e.date}`}
                  className="text-[var(--rose)] hover:bg-white/5 p-1 rounded"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
