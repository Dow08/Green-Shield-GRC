// Types miroir de api/modules/workflow_loader.py (workflow.yaml).
// Source unique alimentant Kanban, Agenda et grille d'entretien (spec §10.3, §13.1).

export type ChampType = "text" | "list" | "boolean" | "preuve_technique";

export interface ChampWorkflow {
  key: string;
  label: string;
  type: ChampType;
  source_automatique?: string;
  note?: string;
}

export interface SourceWorkflow {
  label: string;
  url?: string;
}

export interface EtapeWorkflow {
  id: string;
  titre: string;
  jour_relatif?: number;
  duree?: string;
  role_a_rencontrer?: string[];
  questions?: string[];
  champs?: ChampWorkflow[];
  livrables?: string[];
  sources?: SourceWorkflow[];
  avertissement?: string;
}

export interface MacroPhaseWorkflow {
  id: string;
  titre: string;
  jour_relatif_debut?: number;
  duree?: string;
  etapes: EtapeWorkflow[];
}

export interface WorkflowMetadata {
  id: string;
  name: string;
  version: string;
  duree_typique?: string;
  referentiels?: string[];
  source?: string;
}

export interface Workflow {
  metadata: WorkflowMetadata;
  macro_phases: MacroPhaseWorkflow[];
  checklist_auditeur?: string[];
}

// Statut d'une étape à l'intérieur de sa colonne (macro-phase) — c'est ce qui
// se déplace, pas l'étape entre colonnes : une étape appartient structurellement
// à une seule macro-phase (cf. spec, décision "Kanban par macro-phase").
export type StatutEtape = "a_faire" | "en_cours" | "fait";

export const STATUTS_ETAPE: StatutEtape[] = ["a_faire", "en_cours", "fait"];

export const STATUT_LABELS: Record<StatutEtape, string> = {
  a_faire: "À faire",
  en_cours: "En cours",
  fait: "Fait",
};

// Valeur d'un champ saisi par le consultant. "preuve_technique" n'a pas de
// saisie manuelle : source_automatique l'alimente (AuditCraft-GRC).
export type ValeurChamp = string | boolean | string[];

// Avancement stocké côté mission : une entrée par étape effectivement démarrée.
// Une étape absente de la map est implicitement "à faire", sans aucune valeur.
export type AvancementWorkflow = Record<
  string,
  { statut: StatutEtape; valeurs?: Record<string, ValeurChamp> }
>;
