// Revue de complétude avant génération d'un livrable (api/modules/revue_export.py).
export interface ManqueExport {
  phase: number;
  phase_libelle: string;
  champ: string;
  gravite: "bloquant" | "recommande";
}

export interface RevueExportResult {
  complet: boolean;
  pret_pour_export: boolean;
  total: number;
  bloquants: number;
  manques: ManqueExport[];
}

// Conservation des données personnelles du consultant (F17, schema_version 4).
export interface EcheanceRgpd {
  duree_conservation_mois: number;
  date_fin_mission: string;
  purge_effectuee_le: string;
  date_purge_prevue: string;
  statut: "mission_en_cours" | "en_conservation" | "echue" | "purgee" | "date_invalide";
  jours_restants: number | null;
}

export interface EcheanceRgpdMission extends EcheanceRgpd {
  project_id: string;
  project_name: string;
  client: string;
  donnees_personnelles: number;
}

// Taux de contrôles appuyés par une preuve technique (F10).
export interface CouvertureTechnique {
  controles_total: number;
  controles_couverts: number;
  taux: number;
  scan_execute: boolean;
  details: { controle: string; titre: string; couvert: boolean; preuves: string[] }[];
  phrase: string;
}

export interface SnapshotInfo {
  nom: string;
  date: string;
  motif: string;
  octets: number;
}

export type CopilotSource = "online" | "offline" | "offline_fallback";

export interface CopilotAskResult {
  status: string;
  response: string;
  source: CopilotSource;
  context?: CopilotContext;
}

export interface TiersCritique {
  project: string;
  project_id: string;
  tiers_name: string;
  score: number;
  rating: string;
}

export interface RedouteEventAgrege {
  project: string;
  project_id: string;
  event: string;
  gravity: number;
}

export interface NonConformiteAgregee {
  project: string;
  project_id: string;
  control: string;
  severity: string;
}

export interface CopilotContext {
  total_projects: number;
  by_type: { grc: number; consulting: number };
  avg_progress: number;
  tiers_critiques: TiersCritique[];
  redoute_events: RedouteEventAgrege[];
  non_conformites: NonConformiteAgregee[];
  quick_wins_en_attente: number;
}

export type CollecteDetectedType =
  | "sshd_config" | "nginx" | "apache" | "mysql" | "postgresql" | "docker_compose" | "os_release" | "inconnu";

export interface SuggestedAsset {
  name: string;
  type: string;
  description: string;
  owner: string;
}

export interface FingerprintResult {
  filename: string;
  detected_type: CollecteDetectedType;
  service: string;
  version: string | null;
  directive_count: number;
  flags: string[];
  suggested_asset: SuggestedAsset;
}

export interface ModuleInfo {
  id: string;
  name: string;
  icon: string;
  category: string;
  description: string;
  status: "active" | "soon";
  endpoint?: string;
}

export type ControlStatus = "CONFORME" | "NON_CONFORME" | "NON_APPLICABLE";

export interface Control {
  id: string;
  title: string;
  file: string;
  key: string;
  expected: string;
  actual: string | null;
  status: ControlStatus;
  severity: "Critique" | "Élevé" | "Moyen" | "Faible";
  evidence: string;
  ebios_event: string;
  ebios_gravity: number;
  frameworks: string[];
  recommendation: string;
  rationale: string;
}

export interface AuditResult {
  referential: string;
  version: string;
  target_dir: string;
  generated_at: string;
  score: number;
  band: "Maîtrisée" | "À surveiller" | "Critique";
  critical_count: number;
  counts: { total: number; evaluated: number; compliant: number; gaps: number };
  controls: Control[];
  report_markdown: string;
}

// --- Interfaces pour la gestion de projets avancée (6 Phases) ---

export interface Exigence {
  id: string;
  title: string;
  description?: string;
}

// Contenu complet d'un référentiel, pour le relire et l'enrichir (F2).
// `personnel` : false pour les référentiels livrés, écrasés à chaque mise à jour.
export interface FrameworkDetail {
  id: string;
  name: string;
  description?: string;
  requirements: Exigence[];
  personnel: boolean;
}

export interface Framework {
  id: string;
  name: string;
  description: string;
  requirements_count: number;
}

export interface AssetMetier {
  id: string;
  name: string;
  description: string;
  is_personal_data: boolean;
}

export interface AssetSupport {
  id: string;
  name: string;
  type: string;
  description: string;
  owner: string;
}

export interface RGPDRegister {
  id: string;
  name: string;
  purpose: string;
  data_categories: string;
  retention: string;
}

export interface AIPDData {
  treatment_description: string;
  necessity_eval: string;
  risks_eval: string;
  mitigation_measures: string;
}

export interface Tiers {
  name: string;
  dependence: number;   // 1-5
  penetration: number;  // 1-5
  maturity: number;     // 1-5
  trust: number;        // 1-5
  score: number;        // auto-calculated
  rating: "Critique" | "Élevé" | "Moyen" | "Faible";
}

export interface RedouteEvent {
  id: string;
  event: string;
  gravity: number; // 1-4
  impact: string;
}

export interface RiskSource {
  id: string;
  name: string;
  objective: string;
}

export interface OperationalScenario {
  id: string;
  event: string;
  gravity: number; // 1-4
  likelihood: number; // 1-5
  mitigation: string;
}

export interface CaseStudy {
  case: string;
  lessons: string;
}

export interface BCPStrategy {
  rto: string;
  rpo: string;
  backup_policy: string;
}

export interface E3R {
  endiguement: string;
  eviction: string;
  eradication: string;
  reconstruction: string;
}

export interface Remediation {
  id: string;
  axe: "Gouvernance" | "Protection" | "Défense" | "Résilience";
  measure: string;
  priority: "Critique" | "Élevé" | "Moyen" | "Faible";
}

export interface ManualControl {
  id: string;
  title: string;
  description: string;
  status: "CONFORME" | "NON_CONFORME" | "A_VERIFIER";
  notes: string;
}

// Suivi du temps consommé (schema_version 3, cf. api/modules/schema_migration.py).
// Phases alignées sur PHASES_TEMPS côté backend — toute valeur hors de cette
// liste est rejetée par l'API.
export type PhaseTemps =
  | "cadrage" | "diagnostic" | "tprm" | "ebios" | "resilience" | "traitement" | "autre";

export interface TempsEntree {
  id: string;
  phase: PhaseTemps;
  minutes: number;
  date: string;
  note: string;
}

export interface ProjectState {
  id: string;
  name: string;
  client: string;
  type: "grc" | "consulting";
  status: "en_cours" | "termine";
  progress: number;
  created_at: string;
  updated_at: string;
  // Socle commun aux volets GRC et Consulting (schema_version 2+). Optionnel
  // côté type le temps que toutes les missions soient passées par la migration.
  // Marqueur de la mission de démonstration (F16) : jamais une vraie mission.
  is_demo?: boolean;
  socle?: {
    qualification?: { budget?: string; [k: string]: unknown };
    temps?: { entrees: TempsEntree[] };
    [k: string]: unknown;
  };
  // Introduit au Jalon 1 (schema_version 2, api/modules/schema_migration.py) :
  // avancement des parcours référentiels pilotés par workflow.yaml, indexé par
  // référentiel puis par id d'étape. Optionnel côté type le temps que toutes
  // les missions soient passées par la migration.
  grc?: {
    active: boolean;
    referentiels_actifs: string[];
    parcours: Record<
      string,
      Record<string, { statut: "a_faire" | "en_cours" | "fait"; valeurs?: Record<string, string | boolean | string[]> }>
    >;
  };
  steps: {
    // Phase 1 : Cadrage & Patrimoine
    cadrage: {
      scope: string;
      client_missions: string;
      nda_signed: boolean;
      nda_text: string;
      assets_metier: AssetMetier[];
      assets_support: AssetSupport[];
      framework_id?: string;
      framework_name?: string;
      validated?: boolean; // Étape validée par le consultant
    };
    // Phase 2 : Diagnostic & RGPD
    diagnostic: {
      pssi_active: boolean;
      governance_active: boolean;
      vulnerabilities_active: boolean;
      rgpd_register: RGPDRegister[];
      aipd_required: boolean;
      aipd: AIPDData;
      validated?: boolean; // Étape validée
    };
    // Phase 3 : TPRM
    tprm: {
      tiers: Tiers[];
      validated?: boolean; // Étape validée
    };
    // Phase 4 : EBIOS RM
    ebios: {
      redoute_events: RedouteEvent[];
      risk_sources: RiskSource[];
      operational_scenarios: OperationalScenario[];
      case_studies: CaseStudy[];
      validated?: boolean; // Étape validée
    };
    // Phase 5 : Résilience (E3R, Continuité)
    resilience: {
      logging_active: boolean;
      bcp_strategy: BCPStrategy;
      e3r: E3R;
      validated?: boolean; // Étape validée
    };
    // Phase 6 : Traitement & Restitution
    traitement: {
      remediations: Remediation[];
      quick_wins: string[];
      validated?: boolean; // Étape validée
    };
    // GRC SPECIFIC STEPS MAPPED IN EVALUATION (OPTIONAL FOR TYPE='grc')
    collecte?: {
      files: string[];
    };
    evaluation?: {
      manual_controls: ManualControl[];
      technical_results: AuditResult | null;
    };
    restitution?: {
      exec_summary: string;
      remediation_plan: string[];
    };
  };
}
