import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { api } from "../lib/api";
import type { AIPDData, ObligationAIPD, ReferenceObligationAIPD, RisqueResiduel } from "../types";

interface Props {
  aipd: AIPDData;
  onChange: (aipd: AIPDData) => void;
}

const RISQUES: { valeur: RisqueResiduel; libelle: string }[] = [
  { valeur: "non_evalue", libelle: "Non encore qualifié" },
  { valeur: "acceptable", libelle: "Acceptable après mesures" },
  { valeur: "eleve", libelle: "Élevé malgré les mesures" },
];

/** Obligations de procédure de l'AIPD (§14.2.1).
 *
 *  Les quatre volets d'analyse voisins portent le *contenu* de l'AIPD ; ceux-ci
 *  portent sa conduite. Une analyse solide sur le fond reste irrégulière sans
 *  avis du DPO, et une mise en œuvre malgré un risque résiduel élevé non soumis
 *  à la CNIL est une infraction — d'où l'avertissement explicite.
 */
export function ObligationsAIPD({ aipd, onChange }: Props) {
  const [reference, setReference] = useState<ReferenceObligationAIPD[]>([]);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    api.aipd
      .obligations()
      .then(setReference)
      .catch(() => setErreur("Référentiel des obligations indisponible."));
  }, []);

  const risque = aipd.risque_residuel ?? "non_evalue";
  const art36Requise = risque === "eleve";
  const saisies = new Map((aipd.obligations ?? []).map((o) => [o.id, o]));

  const majObligation = (id: string, champs: Partial<ObligationAIPD>) => {
    const existantes = aipd.obligations ?? [];
    const connue = existantes.some((o) => o.id === id);
    const obligations = connue
      ? existantes.map((o) => (o.id === id ? { ...o, ...champs } : o))
      : [...existantes, { id, satisfait: false, commentaire: "", ...champs }];
    onChange({ ...aipd, obligations });
  };

  const dues = reference.filter((o) => !o.conditionnelle || art36Requise);
  const satisfaites = dues.filter((o) => saisies.get(o.id)?.satisfait).length;
  const art36Manquante = art36Requise && !saisies.get("ART36")?.satisfait;

  return (
    <div className="flex flex-col gap-3 border-t border-white/[0.04] pt-3 mt-1">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <span className="text-[11px] font-bold text-[var(--soft)] uppercase tracking-wide">
          Obligations organisationnelles (conduite de l'AIPD)
        </span>
        {dues.length > 0 && (
          <span className="text-[10px] text-[var(--faint)]">
            {satisfaites} / {dues.length} traitée(s)
          </span>
        )}
      </div>

      {erreur && <div className="text-[11px] text-[var(--rose)]">{erreur}</div>}

      <div>
        <label htmlFor="aipd-risque" className="block text-[11px] font-bold text-[var(--soft)] mb-1">
          Risque résiduel après mesures d'atténuation
        </label>
        <select
          id="aipd-risque"
          value={risque}
          onChange={(e) => onChange({ ...aipd, risque_residuel: e.target.value as RisqueResiduel })}
          className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-1.5 text-xs text-[var(--ink)] focus:outline-none"
        >
          {RISQUES.map((r) => (
            <option key={r.valeur} value={r.valeur}>{r.libelle}</option>
          ))}
        </select>
        <p className="text-[10px] text-[var(--faint)] mt-1">
          Cette qualification vous appartient : elle détermine si la consultation préalable de la CNIL est due.
        </p>
      </div>

      {art36Manquante && (
        <div className="flex items-start gap-2 text-[11px] text-[var(--rose)] bg-[rgba(255,111,145,0.08)] border border-[rgba(255,111,145,0.2)] rounded-xl px-3 py-2">
          <AlertTriangle size={13} className="flex-shrink-0 mt-0.5" />
          <span>
            Risque résiduel élevé : le traitement ne peut pas être mis en œuvre avant consultation
            de la CNIL (RGPD Art. 36 §1).
          </span>
        </div>
      )}

      <div className="flex flex-col gap-2.5">
        {reference.map((o) => {
          const applicable = !o.conditionnelle || art36Requise;
          const saisie = saisies.get(o.id);
          return (
            <div
              key={o.id}
              className={`bg-white/[0.02] border border-white/[0.05] rounded-xl p-2.5 flex flex-col gap-1.5 ${applicable ? "" : "opacity-45"}`}
            >
              <label className="flex items-start gap-2 cursor-pointer text-[11px] text-[var(--ink)]">
                <input
                  type="checkbox"
                  checked={saisie?.satisfait ?? false}
                  disabled={!applicable}
                  onChange={(e) => majObligation(o.id, { satisfait: e.target.checked })}
                  className="mt-0.5 rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                />
                <span className="flex flex-col gap-0.5">
                  <span className="font-bold">
                    {o.libelle}{" "}
                    <span className="text-[9px] font-normal text-[var(--faint)]">({o.reference})</span>
                  </span>
                  <span className="text-[10px] text-[var(--soft)]">
                    {applicable ? o.aide : "Non applicable tant que le risque résiduel n'est pas élevé."}
                  </span>
                </span>
              </label>
              {applicable && (
                <input
                  type="text"
                  aria-label={`Commentaire — ${o.libelle}`}
                  placeholder="Date, interlocuteur, référence de la preuve…"
                  value={saisie?.commentaire ?? ""}
                  onChange={(e) => majObligation(o.id, { commentaire: e.target.value })}
                  className="w-full bg-white/[0.02] border border-[var(--stroke)] rounded-lg px-2.5 py-1 text-[11px] text-[var(--ink)] focus:outline-none"
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
