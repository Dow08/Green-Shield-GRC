import { useState } from "react";
import { AlertTriangle, Plus, ShieldAlert, Trash2 } from "lucide-react";
import { nextId } from "../lib/ids";
import type { ViolationDonnees } from "../types";

interface Props {
  violations: ViolationDonnees[];
  onChange: (violations: ViolationDonnees[]) => void;
}

const NOUVELLE: ViolationDonnees = {
  id: "", date_constat: "", date_notification_cnil: "", nature: "",
  categories_donnees: "", nb_personnes: "", consequences: "", mesures: "",
  notifiee_cnil: false, personnes_informees: false, justification: "",
};

function delaiDepasse(v: ViolationDonnees): boolean {
  if (!v.date_constat) return false;
  if (v.notifiee_cnil && v.date_notification_cnil) {
    const heures = (new Date(v.date_notification_cnil).getTime() - new Date(v.date_constat).getTime()) / 3_600_000;
    return heures > 72;
  }
  if (!v.notifiee_cnil) {
    const heures = (Date.now() - new Date(v.date_constat).getTime()) / 3_600_000;
    return heures > 72 && !v.justification.trim();
  }
  return false;
}

/**
 * Registre interne des violations de données (RGPD Art. 33-34, G5).
 *
 * « Toujours documenter toute violation, même non notifiable, dans un
 * registre interne » (référence RGPD) — obligation distincte de la simple
 * case « notifiée à la CNIL ». Absent de l'application jusqu'au 30/07/2026,
 * identifié en revue GRC senior.
 */
export function ViolationsPanel({ violations, onChange }: Props) {
  const [nouvelle, setNouvelle] = useState<ViolationDonnees>(NOUVELLE);

  return (
    <div className="flex flex-col gap-3">
      <div className="text-xs font-bold text-[var(--rose)] mb-1 flex items-center gap-1.5">
        <ShieldAlert size={14} /> C. Registre des Violations de Données (RGPD Art. 33-34)
      </div>
      <p className="text-[10px] text-[var(--faint)] -mt-1.5 leading-normal">
        Toute violation se documente ici, même jugée non notifiable — la CNIL doit être notifiée sous 72 h
        (Art. 33) si la violation est susceptible d'engendrer un risque pour les droits et libertés.
      </p>

      <div className="flex flex-col gap-2">
        {violations.map((v, idx) => {
          const enRetard = delaiDepasse(v);
          return (
            <div key={v.id} className={`bg-white/[0.02] p-2.5 rounded-xl border text-xs flex flex-col gap-1.5 ${enRetard ? "border-[var(--rose)]/40" : "border-white/[0.05]"}`}>
              <div className="flex justify-between items-start gap-2">
                <div>
                  <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-2">{v.id}</span>
                  <span className="font-bold text-[var(--ink)]">{v.nature || "Nature non renseignée"}</span>
                </div>
                <button
                  type="button"
                  onClick={() => { const list = [...violations]; list.splice(idx, 1); onChange(list); }}
                  className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg flex-shrink-0"
                  aria-label={`Supprimer la violation ${v.id}`}
                >
                  <Trash2 size={13} />
                </button>
              </div>
              {enRetard && (
                <span className="text-[var(--rose)] font-bold text-[9px] flex items-center gap-1">
                  <AlertTriangle size={11} /> Délai de 72 h dépassé sans notification ni justification
                </span>
              )}
              <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[var(--soft)]">
                <span><strong className="text-[var(--faint)]">Constatée le :</strong> {v.date_constat || "—"}</span>
                <span><strong className="text-[var(--faint)]">CNIL :</strong> {v.notifiee_cnil ? `Notifiée le ${v.date_notification_cnil || "—"}` : "Non notifiée"}</span>
                <span><strong className="text-[var(--faint)]">Personnes informées :</strong> {v.personnes_informees ? "Oui" : "Non"}</span>
                {v.nb_personnes && <span><strong className="text-[var(--faint)]">Personnes affectées :</strong> {v.nb_personnes}</span>}
              </div>
            </div>
          );
        })}
        {violations.length === 0 && (
          <p className="text-[10px] text-[var(--g1)] italic">Aucune violation constatée sur cette mission.</p>
        )}
      </div>

      <div className="flex flex-col gap-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <input
            type="text" placeholder="ID (ex: VIO-01)" value={nouvelle.id}
            onChange={(e) => setNouvelle({ ...nouvelle, id: e.target.value })}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
          <input
            type="text" placeholder="Nature de la violation" value={nouvelle.nature}
            onChange={(e) => setNouvelle({ ...nouvelle, nature: e.target.value })}
            className="md:col-span-2 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <input
            type="text" placeholder="Catégories de données concernées" value={nouvelle.categories_donnees}
            onChange={(e) => setNouvelle({ ...nouvelle, categories_donnees: e.target.value })}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
          <input
            type="text" placeholder="Nombre de personnes affectées (approx.)" value={nouvelle.nb_personnes}
            onChange={(e) => setNouvelle({ ...nouvelle, nb_personnes: e.target.value })}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
          <input
            type="text" placeholder="Conséquences probables" value={nouvelle.consequences}
            onChange={(e) => setNouvelle({ ...nouvelle, consequences: e.target.value })}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
        </div>
        <input
          type="text" placeholder="Mesures prises" value={nouvelle.mesures}
          onChange={(e) => setNouvelle({ ...nouvelle, mesures: e.target.value })}
          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
        />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 items-center">
          <div>
            <label className="block text-[9px] font-bold text-[var(--faint)] mb-0.5">Date de constat</label>
            <input
              type="date" value={nouvelle.date_constat}
              onChange={(e) => setNouvelle({ ...nouvelle, date_constat: e.target.value })}
              className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none text-[var(--ink)]"
            />
          </div>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox" checked={nouvelle.notifiee_cnil}
              onChange={(e) => setNouvelle({ ...nouvelle, notifiee_cnil: e.target.checked })}
              className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
            />
            Notifiée CNIL
          </label>
          {nouvelle.notifiee_cnil ? (
            <div>
              <label className="block text-[9px] font-bold text-[var(--faint)] mb-0.5">Date de notification</label>
              <input
                type="date" value={nouvelle.date_notification_cnil}
                onChange={(e) => setNouvelle({ ...nouvelle, date_notification_cnil: e.target.value })}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none text-[var(--ink)]"
              />
            </div>
          ) : (
            <input
              type="text" placeholder="Justification de non-notification" value={nouvelle.justification}
              onChange={(e) => setNouvelle({ ...nouvelle, justification: e.target.value })}
              className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
            />
          )}
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox" checked={nouvelle.personnes_informees}
              onChange={(e) => setNouvelle({ ...nouvelle, personnes_informees: e.target.checked })}
              className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
            />
            Personnes informées
          </label>
        </div>
        <button
          type="button"
          onClick={() => {
            if (!nouvelle.id.trim() || !nouvelle.nature.trim()) return;
            const list = [...violations, nouvelle];
            onChange(list);
            setNouvelle({ ...NOUVELLE, id: nextId("VIO", list.map((v) => v.id)) });
          }}
          className="self-end flex items-center gap-1.5 bg-[var(--g1)] text-[#04150e] px-3 py-1.5 rounded-xl hover:opacity-90 font-bold"
        >
          <Plus size={14} /> Ajouter la violation
        </button>
      </div>
    </div>
  );
}
