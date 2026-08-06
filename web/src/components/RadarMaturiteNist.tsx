import { useCallback, useEffect, useState } from "react";
import { Loader2, Info } from "lucide-react";
import { api } from "../lib/api";
import type { ProjectState, ProfilMaturiteNist, FonctionMaturite } from "../types";
import { polaire } from "../lib/svgPolar";

interface Props {
  projectId: string;
  /** Réaligne la mission du parent après chaque mutation. */
  onProjectUpdate: (state: ProjectState) => void;
}

/**
 * Radar de maturité NIST CSF 2.0 — auto-évaluation déclarative du consultant,
 * un Tier (1-4) par fonction. Distinct de la roue de rattachement
 * (`NistCsfWheel.tsx`) : la roue mesure une couverture calculée, ce radar
 * restitue un jugement professionnel que rien dans la mission ne peut
 * deviner — d'où deux composants séparés, jamais fusionnés.
 *
 * Rendu en SVG pur (aucune bibliothèque de graphes, comme la roue). Un
 * sommet n'existe que pour une fonction effectivement évaluée : une fonction
 * non renseignée n'est jamais tracée au centre (ce qui suggérerait « pire
 * tier possible », une valeur inventée) — la ligne saute directement au
 * sommet suivant évalué.
 */

const ORDRE: FonctionMaturite["code"][] = ["GV", "ID", "PR", "DE", "RS", "RC"];

// Cité verbatim depuis references/nist-csf.md (skill grc-agent-hermes de
// l'utilisateur) — même source que api/modules/maturite_nist.py::TIERS,
// dupliquée ici pour l'affichage des 4 boutons de saisie (même motif que les
// libellés de fonction, déjà dupliqués entre nist_csf_map.py et ce module).
const TIERS: { valeur: 1 | 2 | 3 | 4; nom: string; description: string }[] = [
  { valeur: 1, nom: "Partial", description: "Pratiques ad hoc, réactives, peu de partage d'information" },
  { valeur: 2, nom: "Risk Informed", description: "Conscience du risque, mais pas de processus formel à l'échelle de l'organisation" },
  { valeur: 3, nom: "Repeatable", description: "Politiques formelles, application cohérente, processus de gestion des risques formalisé" },
  { valeur: 4, nom: "Adaptive", description: "Apprend de l'expérience, partage info, adaptation continue" },
];

export function RadarMaturiteNist({ projectId, onProjectUpdate }: Props) {
  const [profil, setProfil] = useState<ProfilMaturiteNist | null>(null);
  const [chargement, setChargement] = useState(true);
  const [busy, setBusy] = useState(false);
  const [erreur, setErreur] = useState("");
  const [selection, setSelection] = useState<FonctionMaturite["code"] | null>(null);

  const [brouillonTier, setBrouillonTier] = useState<1 | 2 | 3 | 4 | null>(null);
  const [brouillonJustification, setBrouillonJustification] = useState("");

  const recharger = useCallback(async () => {
    try {
      setProfil(await api.projects.maturiteNist(projectId));
    } catch {
      setErreur("Radar de maturité indisponible.");
    } finally {
      setChargement(false);
    }
  }, [projectId]);

  useEffect(() => {
    void recharger();
  }, [recharger]);

  if (chargement) {
    return (
      <div className="glass p-4 flex items-center gap-2 text-xs text-[var(--soft)]">
        <Loader2 size={14} className="animate-spin" /> Radar de maturité NIST CSF…
      </div>
    );
  }
  if (erreur || !profil) {
    return <div className="glass p-4 text-xs text-[var(--rose)]">{erreur || "Données absentes."}</div>;
  }

  const parCode = Object.fromEntries(profil.fonctions.map((f) => [f.code, f])) as Record<
    FonctionMaturite["code"],
    FonctionMaturite
  >;

  const cx = 130;
  const cy = 130;
  const rOuter = 100;
  const angleDe = (code: FonctionMaturite["code"]) => ORDRE.indexOf(code) * 60;
  const rDeTier = (tier: number) => (tier / 4) * rOuter;

  const sommetsEvalues = ORDRE.map((c) => parCode[c]).filter((f) => f.tier !== null);
  const points = sommetsEvalues.map((f) => polaire(cx, cy, rDeTier(f.tier as number), angleDe(f.code)));

  const selectionner = (code: FonctionMaturite["code"]) => {
    if (selection === code) {
      setSelection(null);
      return;
    }
    setSelection(code);
    const f = parCode[code];
    setBrouillonTier(f.tier);
    setBrouillonJustification(f.justification);
  };

  const enregistrer = async () => {
    if (!selection) return;
    setBusy(true);
    setErreur("");
    try {
      const state = await api.projects.definirMaturiteNist(projectId, selection, {
        tier: brouillonTier,
        justification: brouillonJustification,
      });
      onProjectUpdate(state);
      await recharger();
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Enregistrement refusé.");
    } finally {
      setBusy(false);
    }
  };

  const fonctionSelectionnee = selection ? parCode[selection] : null;

  return (
    <div className="glass p-5 flex flex-col gap-4">
      <div>
        <div className="text-xs font-bold text-[var(--g3)] uppercase tracking-wide">
          Radar de maturité NIST CSF (auto-déclaré)
        </div>
        <p className="text-[11px] text-[var(--soft)] mt-1 leading-normal">
          Auto-évaluation déclarative du consultant, distincte du rattachement de contrôles
          (roue NIST CSF ci-dessus) : ce radar reflète un jugement professionnel, pas une
          mesure de couverture. Cliquez une fonction pour déclarer son niveau.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row items-center gap-5">
        <svg viewBox="0 0 260 260" width="230" height="230" className="flex-shrink-0" role="img"
             aria-label="Radar de maturité NIST CSF sur les six fonctions">
          {/* Grille de fond : 4 hexagones concentriques (un par Tier) */}
          {[1, 2, 3, 4].map((tier) => (
            <polygon
              key={tier}
              points={ORDRE.map((code) => polaire(cx, cy, rDeTier(tier), angleDe(code)).join(",")).join(" ")}
              fill="none"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth={1}
            />
          ))}

          {/* Rayons */}
          {ORDRE.map((code) => {
            const [x, y] = polaire(cx, cy, rOuter, angleDe(code));
            return <line key={code} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />;
          })}

          {/* Zone de maturité déclarée — jamais un sommet pour une fonction non évaluée */}
          {points.length >= 3 && (
            <polygon
              points={points.map(([x, y]) => `${x},${y}`).join(" ")}
              fill="rgba(107,200,255,0.18)"
              stroke="var(--sky)"
              strokeWidth={2}
            />
          )}
          {points.length === 2 && (
            <line
              x1={points[0][0]} y1={points[0][1]} x2={points[1][0]} y2={points[1][1]}
              stroke="var(--sky)" strokeWidth={2}
            />
          )}
          {points.length === 1 && (
            <circle cx={points[0][0]} cy={points[0][1]} r={4} fill="var(--sky)" />
          )}
          {sommetsEvalues.map((f) => {
            const [x, y] = polaire(cx, cy, rDeTier(f.tier as number), angleDe(f.code));
            return <circle key={f.code} cx={x} cy={y} r={3} fill="var(--sky)" />;
          })}

          {/* Étiquettes de fonction */}
          {ORDRE.map((code) => {
            const f = parCode[code];
            const [x, y] = polaire(cx, cy, rOuter + 24, angleDe(code));
            const actif = selection === code;
            return (
              <g key={code} className="cursor-pointer" onClick={() => selectionner(code)}>
                <text x={x} y={y} textAnchor="middle" dominantBaseline="middle"
                      fontSize="10" fontWeight="700"
                      fill={actif ? "var(--sky)" : "#8a94a6"}>
                  {f.libelle}
                </text>
                <text x={x} y={y + 11} textAnchor="middle" fontSize="8" fill="#8a94a6">
                  {f.tier_nom ?? "— non évalué"}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="flex-1 w-full flex flex-col gap-3">
          {fonctionSelectionnee ? (
            <div className="rounded-xl border border-[var(--stroke)] bg-white/[0.02] p-3 flex flex-col gap-2">
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-bold text-[var(--ink)]">{fonctionSelectionnee.libelle}</span>
                <span className="text-xs text-[var(--soft)]">
                  {fonctionSelectionnee.tier_nom ?? "Non évalué"}
                </span>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {TIERS.map((t) => (
                  <button
                    key={t.valeur}
                    type="button"
                    title={t.description}
                    onClick={() => setBrouillonTier(brouillonTier === t.valeur ? null : t.valeur)}
                    className={`rounded-lg px-2 py-1 text-[10.5px] font-bold transition ${
                      brouillonTier === t.valeur
                        ? "bg-[var(--sky)] text-[#04150e]"
                        : "bg-white/5 text-[var(--soft)] hover:bg-white/10"
                    }`}
                  >
                    {t.valeur} · {t.nom}
                  </button>
                ))}
              </div>

              <textarea
                value={brouillonJustification}
                onChange={(e) => setBrouillonJustification(e.target.value)}
                placeholder="Justification (optionnelle)"
                maxLength={500}
                rows={2}
                className="w-full resize-none bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />

              <button
                type="button"
                onClick={enregistrer}
                disabled={busy}
                className="self-end flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-4 py-2 text-xs font-bold text-[#04150e] transition hover:opacity-90 disabled:opacity-40"
              >
                {busy && <Loader2 size={13} className="animate-spin" />} Enregistrer
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-1.5">
              {profil.fonctions.map((f) => (
                <button
                  key={f.code}
                  type="button"
                  onClick={() => selectionner(f.code)}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left transition hover:bg-white/5"
                >
                  <span className="text-[11px] text-[var(--soft)] truncate">
                    {f.libelle}
                    <span className="text-[var(--faint)]"> {f.tier_nom ?? "—"}</span>
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className="flex items-start gap-2 rounded-xl border border-[var(--stroke)] bg-white/[0.02] p-2.5">
            <Info size={12} className="mt-0.5 flex-shrink-0 text-[var(--faint)]" />
            <p className="text-[10.5px] leading-relaxed text-[var(--faint)]">{profil.note}</p>
          </div>

          {erreur && <p className="text-[11px] font-bold text-[var(--rose)]">{erreur}</p>}
        </div>
      </div>
    </div>
  );
}
