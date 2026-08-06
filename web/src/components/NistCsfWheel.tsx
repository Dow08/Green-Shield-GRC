import { useEffect, useState } from "react";
import { Loader2, Info } from "lucide-react";
import { api } from "../lib/api";
import type { CarteNist, FonctionNist } from "../types";

interface Props {
  projectId: string;
}

/**
 * Roue NIST CSF 2.0 — Govern au centre, les cinq fonctions opérationnelles en
 * couronne, à la manière de CISO Assistant.
 *
 * Rendue en SVG pur, sans bibliothèque de graphes : le projet s'interdit toute
 * dépendance qui alourdirait l'exécutable.
 *
 * Chaque segment est coloré par bandes discrètes (non rattaché / faible /
 * partiel / couvert) plutôt qu'en dégradé continu : afficher « 63 % » sur un
 * rattachement indicatif suggérerait une précision que la donnée n'a pas.
 */

// Palette par bande. « Non rattaché » est gris et non rouge : l'absence de
// rattachement n'est pas un échec, surtout en mode indicatif.
function couleur(taux: number | null): string {
  if (taux === null) return "#3a4150"; // non rattaché
  if (taux >= 67) return "#2ee6a0"; // couvert
  if (taux >= 34) return "#ffcf6b"; // partiel
  return "#ff6f91"; // faible
}

const ORDRE_EXTERIEUR: FonctionNist["code"][] = ["ID", "PR", "DE", "RS", "RC"];

function polaire(cx: number, cy: number, r: number, deg: number): [number, number] {
  const a = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}

function segmentDonut(cx: number, cy: number, ri: number, ro: number, a0: number, a1: number): string {
  const [x0o, y0o] = polaire(cx, cy, ro, a0);
  const [x1o, y1o] = polaire(cx, cy, ro, a1);
  const [x0i, y0i] = polaire(cx, cy, ri, a1);
  const [x1i, y1i] = polaire(cx, cy, ri, a0);
  const large = a1 - a0 > 180 ? 1 : 0;
  return `M${x0o},${y0o} A${ro},${ro} 0 ${large} 1 ${x1o},${y1o} L${x0i},${y0i} A${ri},${ri} 0 ${large} 0 ${x1i},${y1i} Z`;
}

export function NistCsfWheel({ projectId }: Props) {
  const [carte, setCarte] = useState<CarteNist | null>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [selection, setSelection] = useState<FonctionNist["code"] | null>(null);

  useEffect(() => {
    let vivant = true;
    api.projects
      .nistCsf(projectId)
      .then((c) => vivant && setCarte(c))
      .catch(() => vivant && setErreur("Roue NIST indisponible."))
      .finally(() => vivant && setChargement(false));
    return () => {
      vivant = false;
    };
  }, [projectId]);

  if (chargement) {
    return (
      <div className="glass p-4 flex items-center gap-2 text-xs text-[var(--soft)]">
        <Loader2 size={14} className="animate-spin" /> Rattachement NIST CSF…
      </div>
    );
  }
  if (erreur || !carte) {
    return <div className="glass p-4 text-xs text-[var(--rose)]">{erreur || "Données absentes."}</div>;
  }

  const parCode = Object.fromEntries(carte.fonctions.map((f) => [f.code, f])) as Record<
    FonctionNist["code"],
    FonctionNist
  >;
  const gv = parCode.GV;

  const cx = 130;
  const cy = 130;
  // Couronne extérieure (5 fonctions) et anneau intérieur (Govern).
  const rExtIn = 78;
  const rExtOut = 120;
  const rGvIn = 46;
  const rGvOut = 74;

  const fonctionSelectionnee = selection ? parCode[selection] : null;

  return (
    <div className="glass p-5 flex flex-col gap-4">
      <div>
        <div className="text-xs font-bold text-[var(--g3)] uppercase tracking-wide">
          Rattachement NIST CSF 2.0
        </div>
        <p className="text-[11px] text-[var(--soft)] mt-1 leading-normal">
          Ce que la mission couvre, fonction par fonction. Cliquez un secteur pour voir les
          contrôles rattachés.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row items-center gap-5">
        <svg viewBox="0 0 260 260" width="230" height="230" className="flex-shrink-0" role="img"
             aria-label="Roue des six fonctions NIST CSF selon leur couverture">
          {/* 5 fonctions opérationnelles en couronne extérieure, 72° chacune */}
          {ORDRE_EXTERIEUR.map((code, i) => {
            const f = parCode[code];
            const a0 = i * 72 + 1;
            const a1 = (i + 1) * 72 - 1;
            const [lx, ly] = polaire(cx, cy, (rExtIn + rExtOut) / 2, a0 + 35);
            const actif = selection === code;
            return (
              <g key={code} className="cursor-pointer"
                 onClick={() => setSelection(actif ? null : code)}>
                <path
                  d={segmentDonut(cx, cy, rExtIn, rExtOut, a0, a1)}
                  fill={couleur(f.taux)}
                  opacity={actif || !selection ? 1 : 0.4}
                  stroke="#0b0f14"
                  strokeWidth={2}
                />
                <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
                      fontSize="10" fontWeight="700" fill="#0b0f14" pointerEvents="none">
                  {f.libelle}
                </text>
              </g>
            );
          })}

          {/* Govern : anneau intérieur cliquable */}
          <g className="cursor-pointer" onClick={() => setSelection(selection === "GV" ? null : "GV")}>
            <circle
              cx={cx}
              cy={cy}
              r={(rGvIn + rGvOut) / 2}
              fill="none"
              stroke={couleur(gv.taux)}
              strokeWidth={rGvOut - rGvIn}
              opacity={selection === "GV" || !selection ? 1 : 0.4}
            />
            <text x={cx} y={cy - (rGvIn + rGvOut) / 2 + 3} textAnchor="middle"
                  fontSize="10" fontWeight="700" fill="#0b0f14" pointerEvents="none">
              {gv.libelle}
            </text>
          </g>

          {/* Cœur */}
          <circle cx={cx} cy={cy} r={rGvIn - 2} fill="#0b0f14" />
          <text x={cx} y={cy - 5} textAnchor="middle" fontSize="9" fontWeight="800" fill="#e8eef5">
            NIST CSF
          </text>
          <text x={cx} y={cy + 8} textAnchor="middle" fontSize="8" fill="#8a94a6">
            {carte.total_rattaches} rattaché{carte.total_rattaches > 1 ? "s" : ""}
          </text>
        </svg>

        <div className="flex-1 w-full flex flex-col gap-3">
          {/* Détail de la fonction sélectionnée, ou vue synthétique des six */}
          {fonctionSelectionnee ? (
            <div className="rounded-xl border border-[var(--stroke)] bg-white/[0.02] p-3">
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-bold text-[var(--ink)]">
                  {fonctionSelectionnee.libelle}
                </span>
                <span className="text-xs text-[var(--soft)]">
                  {fonctionSelectionnee.taux === null
                    ? "Aucun contrôle rattaché"
                    : `${fonctionSelectionnee.couverts}/${fonctionSelectionnee.rattaches} couvert(s)`}
                </span>
              </div>
              {fonctionSelectionnee.codes.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-1">
                  {fonctionSelectionnee.codes.map((c) => (
                    <span key={c} className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] font-mono text-[var(--soft)]">
                      {c}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-[11px] italic text-[var(--faint)]">
                  Le pont vers cette fonction ne relie aucun contrôle décidé de la mission.
                </p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-1.5">
              {carte.fonctions.map((f) => (
                <button
                  key={f.code}
                  type="button"
                  onClick={() => setSelection(f.code)}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left transition hover:bg-white/5"
                >
                  <span
                    className="h-3 w-3 flex-shrink-0 rounded-sm"
                    style={{ backgroundColor: couleur(f.taux) }}
                  />
                  <span className="text-[11px] text-[var(--soft)] truncate">
                    {f.libelle}
                    <span className="text-[var(--faint)]">
                      {" "}
                      {f.taux === null ? "—" : `${f.taux}%`}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className="flex items-start gap-2 rounded-xl border border-[var(--stroke)] bg-white/[0.02] p-2.5">
            <Info size={12} className="mt-0.5 flex-shrink-0 text-[var(--faint)]" />
            <p className="text-[10.5px] leading-relaxed text-[var(--faint)]">{carte.note}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
