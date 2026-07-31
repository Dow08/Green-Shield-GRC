import { useMemo } from "react";
import type { ProjectState } from "../types";
import { Clock, AlertTriangle, CheckCircle2 } from "lucide-react";

interface Props {
  projects: ProjectState[];
}

export function TimelineHorizons({ projects }: Props) {
  const horizons = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const rems = projects.flatMap(p => {
      const remediations = (p.steps?.traitement?.remediations || []) as any[];
      return remediations.map(r => ({
        ...r,
        project_name: p.name,
        project_id: p.id,
      }));
    }).filter(r => r.echeance && r.statut !== "Fait" && r.statut !== "Annulé");

    const courtTerme = [];
    const moyenTerme = [];
    const longTerme = [];

    for (const r of rems) {
      const echeance = new Date(r.echeance);
      const diffTime = echeance.getTime() - today.getTime();
      const diffMonths = diffTime / (1000 * 3600 * 24 * 30);
      
      if (diffMonths <= 3) {
        courtTerme.push(r);
      } else if (diffMonths <= 6) {
        moyenTerme.push(r);
      } else {
        longTerme.push(r);
      }
    }

    const sortByDate = (a: any, b: any) => new Date(a.echeance).getTime() - new Date(b.echeance).getTime();

    courtTerme.sort(sortByDate);
    moyenTerme.sort(sortByDate);
    longTerme.sort(sortByDate);

    return { courtTerme, moyenTerme, longTerme };
  }, [projects]);

  const renderColumn = (title: string, data: any[], color: string, icon: any) => {
    const Icon = icon;
    return (
      <div className="flex flex-col gap-3">
        <div className={`flex items-center gap-2 font-bold text-[11px] uppercase tracking-wider ${color}`}>
          <Icon size={14} /> {title} ({data.length})
        </div>
        <div className="flex flex-col gap-2">
          {data.length === 0 && (
            <div className="text-[10px] text-[var(--faint)] italic bg-white/[0.02] border border-white/5 p-3 rounded-xl text-center">
              Aucune action
            </div>
          )}
          {data.slice(0, 3).map((r, i) => (
            <div key={i} className="bg-white/[0.03] border border-white/5 rounded-xl p-3 flex flex-col gap-1.5 hover:bg-white/[0.05] transition">
              <div className="flex justify-between items-start gap-2">
                <span className="text-xs font-bold text-[var(--ink)] leading-tight">{r.measure}</span>
                <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold shrink-0 ${
                  r.priority === "Critique" || r.priority === "Élevé" ? "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]" : "bg-white/10 text-[var(--soft)]"
                }`}>
                  {r.priority}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[9px] text-[var(--soft)] font-mono">
                <span className="truncate max-w-[120px]">{r.project_name}</span>
                <span className="text-[var(--sky)]">{r.echeance}</span>
              </div>
            </div>
          ))}
          {data.length > 3 && (
            <div className="text-center text-[9px] text-[var(--soft)] font-bold pt-1">
              + {data.length - 3} autre(s) action(s)
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="glass-2 p-5 flex flex-col gap-4 mt-4 mb-4 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 bg-gradient-to-b from-[var(--sky)] to-[var(--g1)] h-full opacity-50" />
      <div className="flex items-center justify-between">
        <div className="text-sm font-extrabold tracking-tight text-[var(--ink)] flex items-center gap-2">
          <Clock size={16} className="text-[var(--sky)]" /> Frise des Remédiations (3 Horizons)
        </div>
        <div className="text-[10px] text-[var(--faint)]">Aperçu transversal des plans de traitement</div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {renderColumn("Court terme (< 3 mois)", horizons.courtTerme, "text-[var(--rose)]", AlertTriangle)}
        {renderColumn("Moyen terme (3-6 mois)", horizons.moyenTerme, "text-[var(--amber)]", Clock)}
        {renderColumn("Long terme (> 6 mois)", horizons.longTerme, "text-[var(--g1)]", CheckCircle2)}
      </div>
    </div>
  );
}
