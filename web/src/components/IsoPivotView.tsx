import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { PhaseKanban } from "./PhaseKanban";
import { api } from "../lib/api";
import type { ProjectState } from "../types";
import type { Workflow, StatutEtape, ValeurChamp } from "../types/workflow";

interface Props {
  project: ProjectState;
  onChange: (project: ProjectState) => void;
}

const REFERENTIEL = "iso27001";

/**
 * Parcours GRC pivot (ISO 27001) — pont entre le Kanban générique (§10.3) et
 * la mission courante. L'avancement vit dans project.grc.parcours.iso27001,
 * introduit par la migration v2 (api/modules/schema_migration.py) : une
 * mission plus ancienne l'a déjà via /api/projects/{id} (migration à la lecture).
 */
export function IsoPivotView({ project, onChange }: Props) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.frameworks
      .workflow(REFERENTIEL)
      .then(setWorkflow)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Échec de chargement"));
  }, []);

  if (error) {
    return (
      <div className="glass p-5 text-[var(--rose)]">
        Impossible de charger le parcours ISO 27001 : {error}
      </div>
    );
  }
  if (!workflow) {
    return (
      <div className="glass flex items-center justify-center gap-2 p-8 text-[var(--soft)]">
        <Loader2 className="animate-spin" size={16} /> Chargement du parcours…
      </div>
    );
  }

  const avancement = project.grc?.parcours?.[REFERENTIEL] ?? {};

  function handleStatusChange(etapeId: string, statut: StatutEtape) {
    const grc = project.grc ?? { active: true, referentiels_actifs: [REFERENTIEL], parcours: {} };
    const existant = grc.parcours[REFERENTIEL]?.[etapeId];
    const parcours = {
      ...grc.parcours,
      [REFERENTIEL]: { ...grc.parcours[REFERENTIEL], [etapeId]: { ...existant, statut } },
    };
    onChange({ ...project, grc: { ...grc, parcours } });
  }

  function handleValueChange(etapeId: string, champKey: string, valeur: ValeurChamp) {
    const grc = project.grc ?? { active: true, referentiels_actifs: [REFERENTIEL], parcours: {} };
    const existant = grc.parcours[REFERENTIEL]?.[etapeId] ?? { statut: "a_faire" as const };
    const parcours = {
      ...grc.parcours,
      [REFERENTIEL]: {
        ...grc.parcours[REFERENTIEL],
        [etapeId]: { ...existant, valeurs: { ...existant.valeurs, [champKey]: valeur } },
      },
    };
    onChange({ ...project, grc: { ...grc, parcours } });
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="text-xs text-[var(--soft)]">
        {workflow.metadata.name} — {workflow.metadata.duree_typique}
      </div>
      <PhaseKanban
        workflow={workflow}
        avancement={avancement}
        onStatusChange={handleStatusChange}
        onValueChange={handleValueChange}
      />
    </div>
  );
}
