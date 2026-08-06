import { useEffect, useState, useCallback } from "react";
import { FileClock, Plus, Trash2, BellRing, CheckCircle2, XCircle, Loader2, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";
import type { ProjectState, RegistreDemandesPreuves, DemandePreuve, StatutDemande } from "../types";

interface Props {
  projectId: string;
  /** Réaligne la mission du parent après chaque mutation. */
  onProjectUpdate: (state: ProjectState) => void;
}

const LIBELLE_STATUT: Record<StatutDemande, string> = {
  demandee: "Demandée",
  relancee: "Relancée",
  recue: "Reçue",
  refusee: "Refusée",
};

const CLASSE_STATUT: Record<StatutDemande, string> = {
  demandee: "bg-amber-500/15 text-amber-400",
  relancee: "bg-[var(--rose)]/15 text-[var(--rose)]",
  recue: "bg-[rgba(46,230,160,0.15)] text-[var(--g1)]",
  refusee: "bg-white/10 text-[var(--faint)]",
};

/**
 * Registre des documents réclamés au client — le point noir d'un audit réel.
 *
 * Vit dans le socle de mission : c'est un fait de conduite, pas un constat.
 * Ne transforme jamais une absence en conformité — une demande sans réponse
 * reste visible comme telle, un refus du client est distingué d'un silence.
 */
export function DemandesPreuvesPanel({ projectId, onProjectUpdate }: Props) {
  const [registre, setRegistre] = useState<RegistreDemandesPreuves | null>(null);
  const [chargement, setChargement] = useState(true);
  const [busy, setBusy] = useState(false);
  const [erreur, setErreur] = useState("");

  const [libelle, setLibelle] = useState("");
  const [destinataire, setDestinataire] = useState("");
  const [echeance, setEcheance] = useState("");

  const recharger = useCallback(async () => {
    try {
      setRegistre(await api.projects.demandesPreuves(projectId));
    } catch {
      setErreur("Registre des demandes indisponible.");
    } finally {
      setChargement(false);
    }
  }, [projectId]);

  useEffect(() => {
    void recharger();
  }, [recharger]);

  // Toute mutation renvoie la mission entière : on réaligne le parent, puis on
  // relit le registre pour rafraîchir la synthèse et les contrôles sans preuve.
  const appliquer = async (mutation: Promise<ProjectState>) => {
    setBusy(true);
    setErreur("");
    try {
      onProjectUpdate(await mutation);
      await recharger();
    } catch (e) {
      setErreur(e instanceof Error ? e.message : "Opération refusée.");
    } finally {
      setBusy(false);
    }
  };

  const ajouter = async () => {
    if (!libelle.trim()) {
      setErreur("Indiquez le document réclamé.");
      return;
    }
    await appliquer(
      api.projects.addDemandePreuve(projectId, {
        libelle: libelle.trim(),
        destinataire: destinataire.trim(),
        echeance: echeance || undefined,
      }),
    );
    setLibelle("");
    setDestinataire("");
    setEcheance("");
  };

  const changerStatut = (d: DemandePreuve, statut: StatutDemande) =>
    appliquer(api.projects.updateDemandePreuve(projectId, d.id, { statut }));

  const supprimer = (d: DemandePreuve) =>
    appliquer(api.projects.deleteDemandePreuve(projectId, d.id));

  if (chargement) {
    return (
      <div className="glass p-4 flex items-center gap-2 text-xs text-[var(--soft)]">
        <Loader2 size={14} className="animate-spin" /> Chargement du registre des preuves…
      </div>
    );
  }

  const s = registre?.synthese;
  const demandes = registre?.demandes ?? [];
  const orphelins = registre?.controles_sans_justificatif ?? [];

  return (
    <div className="glass p-5 flex flex-col gap-4">
      <div>
        <div className="text-xs font-bold text-[var(--g3)] uppercase tracking-wide flex items-center gap-1.5">
          <FileClock size={14} /> Demandes de preuves
        </div>
        <p className="text-[11px] text-[var(--soft)] mt-1 leading-normal">
          Les documents réclamés au client : à qui, depuis quand, relancés ou non. Une demande
          sans réponse reste visible — jamais transformée en preuve tant que le document n'est pas
          reçu.
        </p>
      </div>

      {s && s.total > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <Compteur libelle="En attente" valeur={s.en_attente} accent="amber" />
          <Compteur libelle="À relancer" valeur={s.a_relancer} accent="rose" />
          <Compteur libelle="Reçues" valeur={s.recues} accent="green" />
          <Compteur libelle="Refusées" valeur={s.refusees} accent="neutre" />
        </div>
      )}

      {s && s.plus_ancienne_jours !== null && s.plus_ancienne_jours >= s.delai_relance_jours && (
        <div className="flex items-start gap-2 rounded-xl border border-[var(--rose)]/25 bg-[var(--rose)]/[0.06] p-2.5 text-[11px] text-[var(--rose)]">
          <BellRing size={13} className="mt-0.5 flex-shrink-0" />
          <span>
            Une demande attend une réponse depuis {s.plus_ancienne_jours} jours. Relancez avant la
            restitution, sinon le manque figurera au rapport.
          </span>
        </div>
      )}

      {/* Liste */}
      <div className="flex flex-col gap-2">
        {demandes.length === 0 && (
          <p className="text-[11px] italic text-[var(--faint)]">
            Aucune demande enregistrée. Ajoutez ci-dessous les pièces que vous attendez du client.
          </p>
        )}
        {demandes.map((d) => {
          const enRetard =
            (d.statut === "demandee" || d.statut === "relancee") &&
            !!d.echeance &&
            d.echeance < new Date().toISOString().slice(0, 10);
          return (
            <div
              key={d.id}
              className={`rounded-xl border p-2.5 text-xs flex flex-col gap-1.5 ${
                enRetard ? "border-[var(--rose)]/40" : "border-white/[0.05]"
              } bg-white/[0.02]`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <span className="font-bold text-[var(--ink)]">{d.libelle}</span>
                  <div className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[10.5px] text-[var(--soft)]">
                    {d.destinataire && <span>Auprès de {d.destinataire}</span>}
                    <span>Demandée le {d.date_demande}</span>
                    {d.date_relance && <span>Relancée le {d.date_relance}</span>}
                    {d.echeance && (
                      <span className={enRetard ? "text-[var(--rose)] font-bold" : ""}>
                        Échéance {d.echeance}
                      </span>
                    )}
                  </div>
                  {d.note && <p className="mt-1 text-[10.5px] italic text-[var(--faint)]">{d.note}</p>}
                </div>
                <span
                  className={`flex-shrink-0 rounded-full px-2 py-0.5 text-[9px] font-extrabold uppercase ${CLASSE_STATUT[d.statut]}`}
                >
                  {LIBELLE_STATUT[d.statut]}
                </span>
              </div>

              {/* Actions selon le statut : on ne propose que les transitions
                  qui ont un sens depuis l'état courant. */}
              <div className="flex flex-wrap items-center gap-1.5">
                {(d.statut === "demandee" || d.statut === "relancee") && (
                  <>
                    {d.statut === "demandee" && (
                      <BoutonAction
                        onClick={() => changerStatut(d, "relancee")}
                        disabled={busy}
                        icone={<BellRing size={11} />}
                        texte="Relancer"
                      />
                    )}
                    <BoutonAction
                      onClick={() => changerStatut(d, "recue")}
                      disabled={busy}
                      icone={<CheckCircle2 size={11} />}
                      texte="Reçue"
                      variante="ok"
                    />
                    <BoutonAction
                      onClick={() => changerStatut(d, "refusee")}
                      disabled={busy}
                      icone={<XCircle size={11} />}
                      texte="Refusée"
                    />
                  </>
                )}
                <button
                  type="button"
                  onClick={() => supprimer(d)}
                  disabled={busy}
                  aria-label={`Supprimer la demande ${d.libelle}`}
                  className="ml-auto rounded-lg p-1 text-[var(--rose)] transition hover:bg-white/5 disabled:opacity-40"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Contrôles conformes sans justificatif : l'angle mort que le registre
          sert à fermer. Signalé, jamais corrigé automatiquement. */}
      {orphelins.length > 0 && (
        <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.05] p-3 text-[11px]">
          <div className="flex items-center gap-1.5 font-bold text-amber-400">
            <AlertTriangle size={12} /> {orphelins.length} contrôle(s) conforme(s) sans preuve ni
            demande
          </div>
          <p className="mt-1 text-[10.5px] text-[var(--soft)]">
            Ces contrôles sont jugés conformes mais rien ne l'atteste. Réclamez la pièce
            correspondante, ou assumez le jugement sur déclaratif.
          </p>
          <ul className="mt-1.5 flex flex-col gap-0.5 text-[10.5px] text-[var(--faint)]">
            {orphelins.slice(0, 5).map((o) => (
              <li key={`${o.referentiel_id}-${o.control_id}`}>
                {o.control_id} — {o.titre}
              </li>
            ))}
            {orphelins.length > 5 && <li>(+{orphelins.length - 5} autres)</li>}
          </ul>
        </div>
      )}

      {/* Ajout */}
      <div className="border-t border-[var(--stroke)] pt-3 flex flex-col gap-2">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <input
            type="text"
            placeholder="Document réclamé"
            value={libelle}
            onChange={(e) => setLibelle(e.target.value)}
            className="md:col-span-2 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <input
            type="text"
            placeholder="Auprès de (rôle)"
            value={destinataire}
            onChange={(e) => setDestinataire(e.target.value)}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10.5px] text-[var(--faint)]">Échéance (optionnelle)</label>
          <input
            type="date"
            value={echeance}
            onChange={(e) => setEcheance(e.target.value)}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <button
            type="button"
            onClick={ajouter}
            disabled={busy}
            className="ml-auto flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--g1)] to-[var(--g3)] px-4 py-2 text-xs font-bold text-[#04150e] transition hover:opacity-90 disabled:opacity-40"
          >
            {busy ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />} Ajouter
          </button>
        </div>
      </div>

      {erreur && <p className="text-[11px] font-bold text-[var(--rose)]">{erreur}</p>}
    </div>
  );
}

function Compteur({
  libelle,
  valeur,
  accent,
}: {
  libelle: string;
  valeur: number;
  accent: "amber" | "rose" | "green" | "neutre";
}) {
  const couleur = {
    amber: "text-amber-400",
    rose: "text-[var(--rose)]",
    green: "text-[var(--g1)]",
    neutre: "text-[var(--faint)]",
  }[accent];
  return (
    <div className="rounded-xl bg-white/[0.03] p-2.5 flex flex-col gap-0.5">
      <span className="text-[9px] font-bold uppercase text-[var(--faint)]">{libelle}</span>
      <span className={`text-lg font-extrabold ${couleur}`}>{valeur}</span>
    </div>
  );
}

function BoutonAction({
  onClick,
  disabled,
  icone,
  texte,
  variante,
}: {
  onClick: () => void;
  disabled: boolean;
  icone: React.ReactNode;
  texte: string;
  variante?: "ok";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[10.5px] font-bold transition disabled:opacity-40 ${
        variante === "ok"
          ? "bg-[rgba(46,230,160,0.12)] text-[var(--g1)] hover:bg-[rgba(46,230,160,0.2)]"
          : "bg-white/5 text-[var(--soft)] hover:bg-white/10"
      }`}
    >
      {icone} {texte}
    </button>
  );
}
