import { useState } from "react";
import { ShieldAlert, Trash2, Save, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import type { EcheanceRgpd } from "../types";

interface Props {
  echeance: EcheanceRgpd | null;
  donneesPersonnelles: number;
  onEnregistrer: (politique: { duree_conservation_mois: number; date_fin_mission: string }) => Promise<void>;
  onPurger: () => Promise<void>;
}

const LIBELLE_STATUT: Record<EcheanceRgpd["statut"], string> = {
  mission_en_cours: "Mission en cours — le délai courra à partir de la date de fin",
  en_conservation: "En conservation",
  echue: "Échéance dépassée — purge attendue",
  purgee: "Données personnelles purgées",
  date_invalide: "Date de fin de mission invalide",
};

/**
 * Conservation des données personnelles collectées par le consultant (F17).
 *
 * Les grilles d'entretien recueillent noms, fonctions et déclarations de
 * personnes physiques : le consultant en est responsable de traitement. Ce
 * panneau lui donne de quoi tenir ses propres obligations — celles-là mêmes
 * qu'il audite chez ses clients.
 */
export function RgpdPanel({ echeance, donneesPersonnelles, onEnregistrer, onPurger }: Props) {
  const [duree, setDuree] = useState(String(echeance?.duree_conservation_mois ?? 36));
  const [dateFin, setDateFin] = useState(echeance?.date_fin_mission ?? "");
  const [busy, setBusy] = useState<"save" | "purge" | null>(null);
  const [confirmation, setConfirmation] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "erreur"; texte: string } | null>(null);

  const enregistrer = async () => {
    const mois = Number(duree);
    if (!Number.isInteger(mois) || mois < 1 || mois > 120) {
      setMessage({ type: "erreur", texte: "La durée doit être un nombre de mois entre 1 et 120." });
      return;
    }
    setBusy("save");
    setMessage(null);
    try {
      await onEnregistrer({ duree_conservation_mois: mois, date_fin_mission: dateFin });
      setMessage({ type: "ok", texte: "Politique de conservation enregistrée." });
    } catch (e) {
      setMessage({ type: "erreur", texte: e instanceof Error ? e.message : "Échec de l'enregistrement." });
    } finally {
      setBusy(null);
    }
  };

  const purger = async () => {
    setBusy("purge");
    setMessage(null);
    try {
      await onPurger();
      setConfirmation(false);
      setMessage({ type: "ok", texte: "Données personnelles effacées. Les constats d'audit sont conservés." });
    } catch (e) {
      setMessage({ type: "erreur", texte: e instanceof Error ? e.message : "Échec de la purge." });
    } finally {
      setBusy(null);
    }
  };

  const echue = echeance?.statut === "echue";

  return (
    <div className="glass p-4 flex flex-col gap-3">
      <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide flex items-center gap-1.5">
        <ShieldAlert size={12} /> Données personnelles — vos obligations
      </span>

      <p className="text-[11px] text-[var(--soft)]">
        Les entretiens recueillent des noms, fonctions et déclarations de personnes physiques.
        Vous en êtes <strong className="text-[var(--ink)]">responsable de traitement</strong> :
        une durée de conservation doit être définie et les données supprimées à son terme.
      </p>

      {echeance && (
        <div
          className={`flex items-start gap-2 rounded-xl border p-2.5 text-[11px] ${
            echue
              ? "border-[rgba(255,111,145,0.3)] bg-[rgba(255,111,145,0.06)] text-[var(--rose)]"
              : "border-white/[0.05] bg-white/[0.02] text-[var(--soft)]"
          }`}
        >
          {echue ? <AlertTriangle size={13} className="shrink-0 mt-0.5" /> : <CheckCircle2 size={13} className="shrink-0 mt-0.5 text-[var(--g1)]" />}
          <span>
            {LIBELLE_STATUT[echeance.statut]}
            {echeance.date_purge_prevue && (
              <> — échéance au <strong className="text-[var(--ink)]">{echeance.date_purge_prevue}</strong></>
            )}
            <br />
            <span className="text-[var(--faint)]">
              {donneesPersonnelles} enregistrement(s) identifiant(s) dans cette mission.
            </span>
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-[auto_auto_auto] gap-2 items-end">
        <label className="flex flex-col gap-1">
          <span className="text-[10px] text-[var(--faint)]">Conservation (mois)</span>
          <input
            type="number"
            min={1}
            max={120}
            value={duree}
            onChange={(e) => setDuree(e.target.value)}
            aria-label="Durée de conservation en mois"
            className="w-28 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] text-[var(--faint)]">Fin de mission</span>
          <input
            type="date"
            value={dateFin}
            onChange={(e) => setDateFin(e.target.value)}
            aria-label="Date de fin de mission"
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
        </label>
        <button
          type="button"
          onClick={enregistrer}
          disabled={busy !== null}
          className="bg-white/[0.06] border border-[var(--stroke)] text-[var(--ink)] font-bold rounded-xl px-3 py-1.5 text-xs hover:bg-white/[0.1] disabled:opacity-40 flex items-center gap-1.5"
        >
          {busy === "save" ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />} Enregistrer
        </button>
      </div>

      <div className="border-t border-white/[0.04] pt-2.5 flex flex-wrap items-center gap-2">
        {confirmation ? (
          <>
            <span className="text-[11px] text-[var(--amber)]">
              Effacer définitivement les {donneesPersonnelles} enregistrement(s) identifiant(s) ?
            </span>
            <button
              type="button"
              onClick={purger}
              disabled={busy !== null}
              className="bg-[var(--rose)] text-[#2a0410] font-bold rounded-xl px-3 py-1.5 text-xs disabled:opacity-40 flex items-center gap-1.5"
            >
              {busy === "purge" ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />} Confirmer la purge
            </button>
            <button
              type="button"
              onClick={() => setConfirmation(false)}
              className="text-[11px] text-[var(--soft)] hover:text-[var(--ink)] px-1"
            >
              Annuler
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmation(true)}
            disabled={donneesPersonnelles === 0}
            className="text-[var(--rose)] hover:bg-white/5 border border-[rgba(255,111,145,0.25)] rounded-xl px-3 py-1.5 text-xs font-bold disabled:opacity-40 flex items-center gap-1.5"
          >
            <Trash2 size={13} /> Purger les données personnelles
          </button>
        )}
      </div>

      <p className="text-[10px] text-[var(--faint)]">
        La purge efface les personnes interrogées, jamais les constats d'audit : la mission
        reste exploitable, elle ne désigne simplement plus personne. Un point de restauration
        est enregistré juste avant.
      </p>

      {message && (
        <div className={`text-[11px] ${message.type === "ok" ? "text-[var(--g1)]" : "text-[var(--rose)]"}`}>
          {message.texte}
        </div>
      )}
    </div>
  );
}
