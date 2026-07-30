import { useState } from "react";
import { FileCheck2 } from "lucide-react";
import type { EntreeSoa, ThemeSoa } from "../types";

interface Props {
  soa: EntreeSoa[];
  onChange: (soa: EntreeSoa[]) => void;
}

const THEMES: ThemeSoa[] = ["Organisationnel", "Personnel", "Physique", "Technologique"];

/**
 * Déclaration d'Applicabilité (SoA) — ISO/IEC 27001:2022 Annexe A.
 *
 * Manque identifié en revue GRC senior le 30/07/2026 : sans SoA, une mission
 * ISO 27001 ne peut pas passer un audit de certification (clause 6.1.3 d).
 * Les 93 contrôles sont fixes (catalogue importé, cf. api/frameworks/
 * soa_iso27001.yaml) — seule leur évaluation est éditable, il ne s'agit pas
 * d'une liste à laquelle on ajoute des lignes comme les autres collections.
 *
 * `applicable` démarre à `null` (non statué) : ne jamais présumer une
 * décision d'applicabilité à la place du consultant.
 */
export function SoaPanel({ soa, onChange }: Props) {
  const [filtreTheme, setFiltreTheme] = useState<ThemeSoa | "Tous">("Tous");

  const statues = soa.filter((e) => e.applicable !== null).length;
  const applicables = soa.filter((e) => e.applicable === true).length;
  const taux = soa.length ? Math.round((statues / soa.length) * 100) : 0;

  const visibles = filtreTheme === "Tous" ? soa : soa.filter((e) => e.theme === filtreTheme);

  const majEntree = (code: string, patch: Partial<EntreeSoa>) => {
    onChange(soa.map((e) => (e.code === code ? { ...e, ...patch } : e)));
  };

  if (soa.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="text-xs font-bold text-[var(--sky)] flex items-center gap-1.5">
          <FileCheck2 size={14} /> Déclaration d'Applicabilité (SoA) — ISO/IEC 27001:2022 Annexe A
        </div>
        <div className="text-[10px] text-[var(--soft)]">
          <strong className="text-[var(--ink)]">{statues}/{soa.length}</strong> contrôle(s) statué(s) ({taux} %) ·{" "}
          <strong className="text-[var(--ink)]">{applicables}</strong> applicable(s)
        </div>
      </div>
      <div className="w-full h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
        <div className="h-full bg-gradient-to-r from-[var(--g1)] to-[var(--g3)]" style={{ width: `${taux}%` }} />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {(["Tous", ...THEMES] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setFiltreTheme(t)}
            className={`px-2.5 py-1 rounded-full text-[10px] font-bold border transition ${
              filtreTheme === t
                ? "bg-[rgba(46,230,160,0.15)] text-[var(--g1)] border-[var(--g1)]/40"
                : "bg-white/[0.02] text-[var(--soft)] border-white/5 hover:bg-white/[0.05]"
            }`}
          >
            {t}{t !== "Tous" && ` (${soa.filter((e) => e.theme === t).length})`}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-1.5 max-h-[420px] overflow-y-auto pr-1">
        {visibles.map((entree) => (
          <div key={entree.code} className="bg-white/[0.02] p-2 rounded-xl border border-white/[0.05] flex flex-col gap-1.5 text-[10px]">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-1.5">{entree.code}</span>
                <span className="font-bold text-[var(--ink)]">{entree.titre}</span>
              </div>
              <div className="flex gap-1 flex-shrink-0">
                <button
                  type="button"
                  onClick={() => majEntree(entree.code, { applicable: true })}
                  className={`px-2 py-0.5 rounded text-[9px] font-bold transition ${entree.applicable === true ? "bg-[rgba(46,230,160,0.15)] text-[var(--g1)]" : "bg-white/[0.03] text-[var(--soft)]"}`}
                >
                  Applicable
                </button>
                <button
                  type="button"
                  onClick={() => majEntree(entree.code, { applicable: false, statut: null })}
                  className={`px-2 py-0.5 rounded text-[9px] font-bold transition ${entree.applicable === false ? "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]" : "bg-white/[0.03] text-[var(--soft)]"}`}
                >
                  Exclu
                </button>
              </div>
            </div>
            {entree.applicable === null && (
              <span className="text-[var(--amber)] text-[9px] font-bold">Non statué</span>
            )}
            {entree.applicable !== null && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-1.5">
                {entree.applicable === true && (
                  <select
                    value={entree.statut ?? ""}
                    onChange={(e) => majEntree(entree.code, { statut: (e.target.value || null) as EntreeSoa["statut"] })}
                    className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-lg px-1.5 py-1 focus:outline-none text-[var(--ink)]"
                  >
                    <option value="">Statut</option>
                    <option value="Implémenté">Implémenté</option>
                    <option value="Partiel">Partiel</option>
                    <option value="Planifié">Planifié</option>
                  </select>
                )}
                <input
                  type="text" placeholder="Justification"
                  value={entree.justification}
                  onChange={(e) => majEntree(entree.code, { justification: e.target.value })}
                  className={`bg-white/[0.03] border border-white/5 rounded-lg px-1.5 py-1 focus:outline-none ${entree.applicable === true ? "" : "md:col-span-2"}`}
                />
                <input
                  type="text" placeholder="Document de référence"
                  value={entree.document_reference}
                  onChange={(e) => majEntree(entree.code, { document_reference: e.target.value })}
                  className="bg-white/[0.03] border border-white/5 rounded-lg px-1.5 py-1 focus:outline-none"
                />
                <input
                  type="text" placeholder="Owner"
                  value={entree.owner}
                  onChange={(e) => majEntree(entree.code, { owner: e.target.value })}
                  className="bg-white/[0.03] border border-white/5 rounded-lg px-1.5 py-1 focus:outline-none"
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
