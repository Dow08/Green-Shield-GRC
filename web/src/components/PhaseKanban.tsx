import { useState } from "react";
import { ChevronDown, ChevronRight, Users, Clock, FileOutput, ExternalLink, Bot, Lock } from "lucide-react";
import type {
  Workflow,
  EtapeWorkflow,
  AvancementWorkflow,
  StatutEtape,
  ValeurChamp,
} from "../types/workflow";
import { STATUTS_ETAPE, STATUT_LABELS } from "../types/workflow";

interface Props {
  workflow: Workflow;
  avancement: AvancementWorkflow;
  onStatusChange: (etapeId: string, statut: StatutEtape) => void;
  onValueChange: (etapeId: string, champKey: string, valeur: ValeurChamp) => void;
}

/**
 * Kanban générique piloté par un workflow.yaml — colonnes = macro-phases,
 * cartes = étapes (spec §10.3). Aucun contenu n'est codé en dur ici : ajouter
 * un référentiel revient à ajouter un fichier YAML, pas à toucher ce composant.
 *
 * Le déplacement se fait par un contrôle de statut (à faire/en cours/fait),
 * pas par glisser-déposer entre colonnes : une étape appartient structurellement
 * à une seule macro-phase, et le drag-and-drop tactile est notoirement peu
 * fiable sur tablette — un tap sur un gros bouton est plus sûr en entretien client.
 */
export function PhaseKanban({ workflow, avancement, onStatusChange, onValueChange }: Props) {
  return (
    <div className="flex gap-3.5 overflow-x-auto pb-2" data-testid="phase-kanban">
      {workflow.macro_phases.map((phase) => {
        const statuts = phase.etapes.map((e) => avancement[e.id]?.statut ?? "a_faire");
        const nbFaites = statuts.filter((s) => s === "fait").length;

        return (
          <section
            key={phase.id}
            className="glass flex w-[300px] flex-none flex-col gap-2.5 p-3.5"
            aria-label={phase.titre}
          >
            <header className="flex items-center justify-between">
              <h3 className="text-sm font-bold">{phase.titre}</h3>
              <span className="text-[11px] font-bold text-[var(--soft)]">
                {nbFaites}/{phase.etapes.length}
              </span>
            </header>
            {phase.duree && (
              <div className="text-[10.5px] text-[var(--faint)]">{phase.duree}</div>
            )}

            <div className="flex flex-col gap-2">
              {phase.etapes.map((etape) => (
                <EtapeCard
                  key={etape.id}
                  etape={etape}
                  statut={avancement[etape.id]?.statut ?? "a_faire"}
                  valeurs={avancement[etape.id]?.valeurs ?? {}}
                  onStatusChange={(s) => onStatusChange(etape.id, s)}
                  onValueChange={(k, v) => onValueChange(etape.id, k, v)}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function EtapeCard({
  etape,
  statut,
  valeurs,
  onStatusChange,
  onValueChange,
}: {
  etape: EtapeWorkflow;
  statut: StatutEtape;
  valeurs: Record<string, ValeurChamp>;
  onStatusChange: (s: StatutEtape) => void;
  onValueChange: (champKey: string, valeur: ValeurChamp) => void;
}) {
  const [ouvert, setOuvert] = useState(false);
  const hasDetail =
    (etape.questions?.length ?? 0) > 0 ||
    (etape.champs?.length ?? 0) > 0 ||
    (etape.livrables?.length ?? 0) > 0 ||
    (etape.sources?.length ?? 0) > 0;

  const isApiValidated = typeof valeurs.source === "string" && valeurs.source.startsWith("api:");

  function cyclerStatut() {
    if (isApiValidated) return; // Ne peut pas être modifié manuellement si validé par API
    const i = STATUTS_ETAPE.indexOf(statut);
    onStatusChange(STATUTS_ETAPE[(i + 1) % STATUTS_ETAPE.length]);
  }

  return (
    <div className="glass-2 flex flex-col gap-1.5 p-2.5">
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={() => hasDetail && setOuvert((o) => !o)}
          className="flex min-w-0 flex-1 items-start gap-1.5 text-left"
          aria-expanded={ouvert}
        >
          {hasDetail &&
            (ouvert ? (
              <ChevronDown size={14} className="mt-0.5 flex-none text-[var(--soft)]" />
            ) : (
              <ChevronRight size={14} className="mt-0.5 flex-none text-[var(--soft)]" />
            ))}
          <span className="text-[12.5px] font-semibold leading-snug">{etape.titre}</span>
        </button>

        {/* Gros bouton tap-friendly : cible tactile large (tablette en entretien). */}
        <button
          type="button"
          role="button"
          disabled={isApiValidated}
          aria-label={`Statut de « ${etape.titre} » : ${STATUT_LABELS[statut]} — appuyer pour changer`}
          onClick={cyclerStatut}
          className={[
            "flex-none rounded-full px-3 py-2 text-[10.5px] font-bold transition flex items-center gap-1",
            isApiValidated 
              ? "bg-[rgba(46,230,160,0.18)] text-[var(--g1)] border border-[var(--g1)] cursor-not-allowed opacity-90"
              : statut === "fait"
              ? "bg-[rgba(46,230,160,0.18)] text-[var(--g1)] cursor-pointer"
              : statut === "en_cours"
                ? "bg-[rgba(255,207,107,0.18)] text-[var(--amber,#ffcf6b)] cursor-pointer"
                : "bg-white/[0.05] text-[var(--faint)] cursor-pointer",
          ].join(" ")}
        >
          {isApiValidated && <Lock size={10} />}
          {isApiValidated ? "Validé par API" : STATUT_LABELS[statut] || statut}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-[var(--faint)]">
        {(etape.duree || etape.jour_relatif !== undefined) && (
          <span className="flex items-center gap-1">
            <Clock size={11} />
            {etape.duree ?? `J+${etape.jour_relatif}`}
          </span>
        )}
        {(etape.role_a_rencontrer?.length ?? 0) > 0 && (
          <span className="flex items-center gap-1">
            <Users size={11} />
            {etape.role_a_rencontrer!.join(", ")}
          </span>
        )}
      </div>

      {ouvert && (
        <div className="mt-1 flex flex-col gap-2 border-t border-white/[0.06] pt-2 text-[11.5px]">
          {(etape.champs?.length ?? 0) > 0 && (
            <div className="flex flex-col gap-2">
              {etape.champs!.map((champ) => (
                <ChampInput
                  key={champ.key}
                  id={`${etape.id}__${champ.key}`}
                  champ={champ}
                  valeur={valeurs[champ.key]}
                  onChange={(v) => onValueChange(champ.key, v)}
                />
              ))}
            </div>
          )}

          {(etape.questions?.length ?? 0) > 0 && (
            <div>
              <div className="mb-1 font-bold text-[var(--soft)]">
                Questions à poser
              </div>
              <ul className="flex flex-col gap-1 pl-3">
                {etape.questions!.map((q, i) => (
                  <li key={i} className="list-disc text-[var(--ink)]">
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(etape.livrables?.length ?? 0) > 0 && (
            <div className="flex items-start gap-1.5">
              <FileOutput size={12} className="mt-0.5 flex-none text-[var(--sky)]" />
              <span>{etape.livrables!.join(" · ")}</span>
            </div>
          )}

          {(etape.sources?.length ?? 0) > 0 && (
            <div className="flex flex-col gap-1">
              {etape.sources!.map((s, i) => (
                <span key={i} className="flex items-center gap-1 text-[var(--faint)]">
                  <ExternalLink size={11} />
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noreferrer" className="underline">
                      {s.label}
                    </a>
                  ) : (
                    <span>
                      {s.label} — <em>source à consulter, hors couverture</em>
                    </span>
                  )}
                </span>
              ))}
            </div>
          )}

          {etape.avertissement && (
            <div className="rounded-lg bg-[rgba(255,111,145,0.1)] px-2 py-1.5 text-[var(--rose)]">
              {etape.avertissement}
            </div>
          )}
          
          {isApiValidated && (
            <div className="mt-3 p-2.5 rounded-lg bg-[rgba(46,230,160,0.05)] border border-[var(--g1)]/20 text-[11px] text-[var(--g1)] flex items-start gap-2">
              <Bot size={14} className="shrink-0 mt-0.5" />
              <div>
                <strong>Validation automatisée :</strong> {valeurs.commentaire || "Cette mesure a été validée par un connecteur Continuous Compliance."}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ChampInput({
  id,
  champ,
  valeur,
  onChange,
}: {
  id: string;
  champ: NonNullable<EtapeWorkflow["champs"]>[number];
  valeur: ValeurChamp | undefined;
  onChange: (v: ValeurChamp) => void;
}) {
  if (champ.type === "preuve_technique") {
    // Jamais de saisie manuelle ici : la valeur vient du scan technique réel
    // (AuditCraft-GRC), sans quoi une preuve pourrait être déclarée sans exister.
    return (
      <div className="flex flex-col gap-0.5">
        <span className="text-[10.5px] font-bold text-[var(--soft)]">{champ.label}</span>
        <div className="rounded-lg bg-white/[0.03] px-2 py-1.5 text-[var(--faint)]">
          {champ.note ?? "Alimenté automatiquement par le scan technique."}
        </div>
      </div>
    );
  }

  if (champ.type === "boolean") {
    return (
      <label htmlFor={id} className="flex items-center gap-2 text-[var(--ink)]">
        <input
          id={id}
          type="checkbox"
          checked={Boolean(valeur)}
          onChange={(e) => onChange(e.target.checked)}
          className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
        />
        {champ.label}
      </label>
    );
  }

  if (champ.type === "list") {
    const lignes = Array.isArray(valeur) ? valeur.join("\n") : "";
    return (
      <div className="flex flex-col gap-0.5">
        <label htmlFor={id} className="text-[10.5px] font-bold text-[var(--soft)]">{champ.label}</label>
        <textarea
          id={id}
          value={lignes}
          onChange={(e) => onChange(e.target.value.split("\n"))}
          rows={2}
          placeholder="une entrée par ligne"
          className="w-full rounded-lg border border-[var(--stroke)] bg-white/[0.03] px-2 py-1.5 text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
        />
      </div>
    );
  }

  // type "text"
  return (
    <div className="flex flex-col gap-0.5">
      <label htmlFor={id} className="text-[10.5px] font-bold text-[var(--soft)]">{champ.label}</label>
      <input
        id={id}
        type="text"
        value={typeof valeur === "string" ? valeur : ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-[var(--stroke)] bg-white/[0.03] px-2 py-1.5 text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
      />
    </div>
  );
}
