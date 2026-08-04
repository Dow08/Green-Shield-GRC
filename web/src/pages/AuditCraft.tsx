import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw, FileDown, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import type { AuditResult, Control } from "../types";

const SEV_COLOR: Record<string, string> = {
  Critique: "#ff6f91",
  Élevé: "#ffcf6b",
  Moyen: "#5cc8ff",
  Faible: "#8b7bff",
};

function bandColor(band: string): string {
  if (band === "Maîtrisée") return "#2ee6a0";
  if (band === "À surveiller") return "#ffcf6b";
  return "#ff6f91";
}

function dotColor(c: Control): string {
  if (c.status === "CONFORME") return "#2ee6a0";
  if (c.status === "NON_APPLICABLE") return "#5d746e";
  return SEV_COLOR[c.severity] ?? "#8ea6a0";
}

export function AuditCraft() {
  const [data, setData] = useState<AuditResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api
      .runAuditcraft()
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "erreur"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const downloadReport = () => {
    if (!data) return;
    const blob = new Blob([data.report_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rapport_auditcraft_grc.md";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <div className="mb-3 text-xs text-[var(--faint)]">
        GREEN SHIELD / <span className="font-semibold text-[var(--g3)]">AuditCraft-GRC</span>
      </div>

      <header className="mb-4 flex items-center gap-4">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">Audit de conformité</h2>
          <p className="mt-0.5 text-sm text-[var(--soft)]">
            {data ? data.target_dir : "…"} · lecture seule · hors-ligne
          </p>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white/[0.045] px-4 py-2.5 text-sm font-bold text-[var(--g1)] transition hover:bg-white/[0.08] disabled:opacity-50"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Relancer
          </button>
          <button
            onClick={downloadReport}
            disabled={!data}
            className="flex items-center gap-2 rounded-full bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-4 py-2.5 text-sm font-bold text-[#04150e] transition hover:opacity-90 disabled:opacity-40"
          >
            <FileDown size={15} /> Rapport
          </button>
        </div>
      </header>

      {loading && (
        <div className="glass flex items-center justify-center gap-3 py-16 text-[var(--soft)]">
          <Loader2 className="animate-spin" size={20} /> Audit en cours…
        </div>
      )}

      {error && !loading && (
        <div className="glass border-[rgba(255,111,145,0.4)] p-5 text-[var(--rose)]">
          Échec de l'audit : {error} — l'API est-elle démarrée ?
        </div>
      )}

      {data && !loading && (
        <>
          <div className="mb-5 flex flex-wrap items-center gap-4">
            <div
              className="grid h-[124px] w-[124px] place-items-center rounded-full"
              style={{ background: `conic-gradient(${bandColor(data.band)} ${data.score * 3.6}deg, rgba(255,255,255,0.08) 0)` }}
            >
              <div className="grid h-[98px] w-[98px] place-items-center rounded-full bg-[var(--bg2)]">
                <div className="text-3xl font-extrabold" style={{ color: bandColor(data.band) }}>
                  {data.score}%
                </div>
                <div className="text-xs text-[var(--soft)]">{data.band}</div>
              </div>
            </div>
            <div className="flex flex-1 flex-wrap gap-3">
              <Stat value={data.critical_count} label="Failles critiques" color="#ff6f91" />
              <Stat value={data.counts.gaps} label="Écarts identifiés" color="#ffcf6b" />
              <Stat value={`${data.counts.compliant}/${data.counts.evaluated}`} label="Contrôles conformes" color="#2ee6a0" />
            </div>
          </div>

          <div className="mb-3 text-sm font-bold text-[var(--soft)]">Écarts & conformité</div>
          <div className="flex flex-col gap-2.5">
            {data.controls.map((c, i) => (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25, delay: 0.03 * i }}
                className="glass-2 flex items-center gap-3.5 px-4 py-3.5"
              >
                <span className="h-3 w-3 flex-none rounded-full" style={{ background: dotColor(c) }} />
                <div className="min-w-0">
                  <div className="text-[13.5px] font-semibold">{c.title}</div>
                  <div className="truncate font-mono text-[11px] text-[var(--soft)]">
                    {c.key} = {c.actual ?? "absent"}
                    {c.status === "CONFORME" ? " ✓" : ""}
                  </div>
                </div>
                <span
                  className="ml-auto flex-none rounded-full px-2.5 py-1 text-[10.5px] font-bold"
                  style={{ background: `${dotColor(c)}22`, color: dotColor(c) }}
                >
                  {c.status === "CONFORME" ? "Conforme" : c.severity}
                </span>
                <span className="flex-none rounded-full bg-[rgba(92,200,255,0.1)] px-2.5 py-1 text-[11px] text-[var(--sky)]">
                  {c.frameworks[0]?.split("—")[1]?.trim() ?? c.frameworks[0] ?? "—"}
                </span>
              </motion.div>
            ))}
          </div>
        </>
      )}
    </motion.div>
  );
}

function Stat({ value, label, color }: { value: string | number; label: string; color: string }) {
  return (
    <div className="glass-2 min-w-[130px] flex-1 px-4 py-3.5">
      <div className="text-2xl font-extrabold" style={{ color }}>
        {value}
      </div>
      <div className="mt-0.5 text-[11.5px] text-[var(--soft)]">{label}</div>
    </div>
  );
}
