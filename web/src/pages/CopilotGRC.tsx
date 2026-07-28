import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bot, ShieldAlert, AlertTriangle, XCircle, ArrowUpRight, Gauge, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import { CopilotSourceBadge } from "../components/CopilotSourceBadge";
import type { CopilotContext, CopilotSource } from "../types";

interface Props {
  onNavigate: (view: string) => void;
}

const RATING_COLOR: Record<string, string> = {
  Critique: "text-[var(--rose)] bg-[rgba(255,111,145,0.12)]",
  Élevé: "text-[var(--amber)] bg-[rgba(255,207,107,0.12)]",
};

export function CopilotGRC({ onNavigate }: Props) {
  const [context, setContext] = useState<CopilotContext | null>(null);
  const [loadingContext, setLoadingContext] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [source, setSource] = useState<CopilotSource | null>(null);
  const [asking, setAsking] = useState(false);

  const loadContext = () => {
    setLoadingContext(true);
    api.copilot
      .context()
      .then(setContext)
      .catch(() => setContext(null))
      .finally(() => setLoadingContext(false));
  };

  useEffect(loadContext, []);

  const handleAsk = () => {
    if (!prompt.trim()) return;
    setAsking(true);
    setResponse("");
    setSource(null);
    const storedKey = localStorage.getItem("copilot_api_key") || "";
    api.copilot
      .ask({ prompt, key: storedKey })
      .then((data) => {
        setResponse(data.response);
        setSource(data.source);
        if (data.context) setContext(data.context);
      })
      .catch((err) => alert("Copilote indisponible : " + err.message))
      .finally(() => setAsking(false));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col h-full overflow-y-auto pr-2">
      <header className="mb-5">
        <h2 className="text-xl font-extrabold tracking-tight flex items-center gap-2">
          <Bot size={20} className="text-purple-400" /> Copilote GRC
        </h2>
        <p className="text-xs text-[var(--soft)] mt-0.5">
          Synthèse transverse de tout le portefeuille de missions : priorise les constats réels, rédige des recommandations, pilote les modules.
        </p>
      </header>

      {loadingContext && (
        <div className="text-xs text-[var(--soft)] flex items-center gap-2 mb-4"><Loader2 size={14} className="animate-spin" /> Analyse du portefeuille…</div>
      )}

      {context && (
        <>
          {/* KPI OVERVIEW */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
            <div className="glass p-3 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--faint)] uppercase">Missions</span>
              <span className="text-lg font-extrabold">{context.total_projects}</span>
            </div>
            <div className="glass p-3 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--faint)] uppercase">GRC / Conseil</span>
              <span className="text-lg font-extrabold">{context.by_type.grc} / {context.by_type.consulting}</span>
            </div>
            <div className="glass p-3 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--faint)] uppercase flex items-center gap-1"><Gauge size={11} /> Progression</span>
              <span className="text-lg font-extrabold">{context.avg_progress}%</span>
            </div>
            <div className="glass p-3 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--rose)] uppercase flex items-center gap-1"><ShieldAlert size={11} /> Tiers à risque</span>
              <span className="text-lg font-extrabold">{context.tiers_critiques.length}</span>
            </div>
            <div className="glass p-3 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--amber)] uppercase flex items-center gap-1"><AlertTriangle size={11} /> Évén. graves</span>
              <span className="text-lg font-extrabold">{context.redoute_events.length}</span>
            </div>
            <div className="glass p-3 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--rose)] uppercase flex items-center gap-1"><XCircle size={11} /> Non-conformités</span>
              <span className="text-lg font-extrabold">{context.non_conformites.length}</span>
            </div>
          </div>

          {/* PRIORITIZED LISTS */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
            <PriorityColumn
              title="Tiers TPRM à risque"
              empty="Aucun tiers Critique/Élevé sur le portefeuille."
              items={context.tiers_critiques.map((t) => ({
                key: `${t.project_id}-${t.tiers_name}`,
                project: t.project,
                label: t.tiers_name,
                badge: t.rating,
                badgeClass: RATING_COLOR[t.rating] ?? "text-[var(--soft)] bg-white/5",
              }))}
              onNavigate={onNavigate}
            />
            <PriorityColumn
              title="Événements redoutés EBIOS RM"
              empty="Aucun événement de gravité ≥ 3 remonté."
              items={context.redoute_events.map((e) => ({
                key: `${e.project_id}-${e.event}`,
                project: e.project,
                label: e.event,
                badge: `Gravité ${e.gravity}/4`,
                badgeClass: "text-[var(--rose)] bg-[rgba(255,111,145,0.12)]",
              }))}
              onNavigate={onNavigate}
            />
            <PriorityColumn
              title="Non-conformités techniques"
              empty="Aucun écart technique détecté (AuditCraft-GRC)."
              items={context.non_conformites.map((c) => ({
                key: `${c.project_id}-${c.control}`,
                project: c.project,
                label: c.control,
                badge: c.severity,
                badgeClass: RATING_COLOR[c.severity] ?? "text-[var(--soft)] bg-white/5",
              }))}
              onNavigate={onNavigate}
            />
          </div>
        </>
      )}

      {/* CHAT */}
      <div className="glass p-4 border-[var(--stroke)] flex flex-col gap-3 bg-[var(--bg2)] rounded-2xl mt-auto">
        <div className="flex items-center gap-2">
          <Bot size={15} className="text-purple-400" />
          <span className="text-xs font-bold text-[var(--ink)]">Demander une synthèse ou une priorisation</span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="ex: Quelles sont mes 3 priorités cette semaine ?"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            className="flex-1 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <button
            onClick={handleAsk}
            disabled={asking}
            className="px-4 py-2 bg-gradient-to-br from-purple-600 to-indigo-600 font-bold rounded-xl text-xs hover:opacity-90 disabled:opacity-40"
          >
            {asking ? "Analyse..." : "Demander au Copilote"}
          </button>
        </div>
        {response && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white/[0.01] border border-white/5 rounded-xl p-3 text-xs font-mono text-[var(--soft)] whitespace-pre-line leading-relaxed">
            <CopilotSourceBadge source={source} />
            {response}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

function PriorityColumn({
  title, empty, items, onNavigate,
}: {
  title: string;
  empty: string;
  items: { key: string; project: string; label: string; badge: string; badgeClass: string }[];
  onNavigate: (view: string) => void;
}) {
  return (
    <div className="glass-2 p-3 flex flex-col gap-2">
      <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">{title}</span>
      {items.length === 0 ? (
        <p className="text-[11px] text-[var(--soft)] italic">{empty}</p>
      ) : (
        <div className="flex flex-col gap-1.5 max-h-[220px] overflow-y-auto pr-1">
          {items.map((item) => (
            <button
              key={item.key}
              onClick={() => onNavigate("missions")}
              className="text-left bg-white/[0.02] hover:bg-white/[0.05] p-2 rounded-lg border border-white/[0.03] transition flex flex-col gap-1"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-bold text-[var(--soft)] truncate">{item.project}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ${item.badgeClass}`}>{item.badge}</span>
              </div>
              <div className="text-[11px] text-[var(--ink)] flex items-center gap-1">
                {item.label} <ArrowUpRight size={10} className="text-[var(--faint)] flex-shrink-0" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
