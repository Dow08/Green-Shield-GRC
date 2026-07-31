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

// Registre interne des violations de données (RGPD Art. 33-34, G5).
// « Toujours documenter toute violation, même non notifiable » — donc un
// registre distinct du simple statut de notification, pas seulement une
// case à cocher.
export interface ViolationDonnees {
  id: string;
  date_constat: string; // AAAA-MM-JJ
  date_notification_cnil: string; // AAAA-MM-JJ, vide si non notifiée
  nature: string;
  categories_donnees: string;
  nb_personnes: string;
  consequences: string;
  mesures: string;
  notifiee_cnil: boolean;
  personnes_informees: boolean;
  justification: string; // motif si non notifiée (Art. 33) ou personnes non informées (Art. 34)
}

/** Obligation de procédure de l'AIPD — distincte des quatre volets d'analyse
 *  (§14.2.1). Le libellé et la référence vivent côté serveur : ils décrivent le
 *  RGPD, pas l'état de la mission. */
export interface ObligationAIPD {
  id: string;
  satisfait: boolean;
  commentaire: string;
}

export type RisqueResiduel = "non_evalue" | "acceptable" | "eleve";

/** Rattachement d'une pratique à un contrôle de référentiel (§14.2.4). */
export interface MappingControle {
  referentiel: string;
  ref: string;
  intitule: string;
}

export interface PratiqueControle {
  id: string;
  libelle: string;
  phase: number;
  phase_libelle: string;
  mappings: MappingControle[];
  /** Présents seulement sur la route d'état d'une mission. */
  couverte?: boolean;
  justification?: string;
}

export interface EtatControlesTechniques {
  pratiques: PratiqueControle[];
  couvertes: number;
  total: number;
  taux: number;
}

/** Description d'une obligation, servie par l'API — jamais stockée en mission. */
export interface ReferenceObligationAIPD {
  id: string;
  libelle: string;
  reference: string;
  aide: string;
  conditionnelle: boolean;
}

export interface AIPDData {
  treatment_description: string;
  necessity_eval: string;
  risks_eval: string;
  mitigation_measures: string;
  /** Qualifié par le consultant : rien ne le déduit à sa place. */
  risque_residuel?: RisqueResiduel;
  obligations?: ObligationAIPD[];
}

/** Exigence de conformité d'un tiers, volet GRC — remplace le scoring EBIOS,
 *  que ni DORA ni NIS2 ne réclament (§14.1bis). */
export interface ExigenceTiers {
  id: string;
  libelle: string;
  satisfait: boolean;
  preuve: string;
}

export interface Tiers {
  name: string;
  dependence: number;   // 1-5
  penetration: number;  // 1-5
  maturity: number;     // 1-5
  trust: number;        // 1-5
  /** Ratio ANSSI calculé par le serveur — jamais par le navigateur. */
  score: number;
  rating: "Critique" | "Élevé" | "Moyen" | "Faible";
  /** Trace la formule qui a produit `score` : les notes antérieures au
   *  29/07/2026 ne sont pas recalculées en silence. */
  methode?: "ratio_anssi" | "moyenne_historique";
  /** Volet GRC uniquement. */
  exigences?: ExigenceTiers[];
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

// Stratégie de traitement du risque — les 4 options de la clause ISO 27001
// 6.1.3 : réduire, accepter, transférer ou éviter.
export type StrategieTraitementRisque = "Réduire" | "Accepter" | "Transférer" | "Éviter" | "";
export type StatutTraitementRisque = "Ouvert" | "En traitement" | "Traité" | "Clos" | "";

export interface OperationalScenario {
  id: string;
  event: string;
  gravity: number; // 1-4, niveau inhérent (avant mesures)
  likelihood: number; // 1-5, niveau inhérent (avant mesures)
  mitigation: string;
  // Chaîne risque -> traitement (§14 audit critique, chantier ②) : sans
  // propriétaire ni décision de traitement, un scénario est une observation,
  // pas un risque géré (cf. Hermes, "un risque sans owner n'est pas géré").
  actif_concerne?: string;
  gravite_residuelle?: number; // 1-4, après mesures existantes
  vraisemblance_residuelle?: number; // 1-5, après mesures existantes
  strategie_traitement?: StrategieTraitementRisque;
  owner?: string;
  date_revue?: string; // AAAA-MM-JJ
  statut?: StatutTraitementRisque;
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

// Volet stratégique de la remédiation ANSSI (§14.2.3) : E3R ne porte que la
// séquence technique/opérationnelle. Manquaient les critères d'arbitrage
// Direction entre urgence de redémarrage et coûts/risques induits.
export interface StrategieRemediation {
  urgence_redemarrage: string;
  couts_risques_redemarrage: string;
  decision_direction: string;
}

export type StatutRemediation = "À faire" | "En cours" | "Fait" | "";

export interface Remediation {
  id: string;
  axe: "Gouvernance" | "Protection" | "Défense" | "Résilience";
  measure: string;
  priority: "Critique" | "Élevé" | "Moyen" | "Faible";
  // Sans responsable ni échéance, un plan de traitement dit quoi faire,
  // jamais qui ni quand (chantier ③).
  responsable?: string;
  echeance?: string; // AAAA-MM-JJ
  statut?: StatutRemediation;
  cout_estime?: string;
  risque_lie?: string; // id d'un OperationalScenario
}

export interface ManualControl {
  id: string;
  title: string;
  description: string;
  status: "CONFORME" | "NON_CONFORME" | "A_VERIFIER";
  notes: string;
  // Référentiel d'origine du contrôle — absent sur les missions migrées
  // avant le multi-référentiel (31/07/2026), toujours présent sur les
  // missions créées depuis.
  referentiel_id?: string;
  referentiel_name?: string;
}

// Bibliothèque de preuves multi-référentiels (G3bis, 31/07/2026) : une
// preuve écrite une fois (ex. une politique de sécurité) peut couvrir des
// contrôles de plusieurs référentiels actifs de la même mission.
export interface LienControle {
  referentiel_id: string;
  control_id: string;
}

export interface Preuve {
  id: string;
  libelle: string;
  description: string;
  document_reference: string;
  date: string;
  controles_lies: LienControle[];
}

// Déclaration d'Applicabilité (SoA) — ISO/IEC 27001:2022 Annexe A, clause
// 6.1.3 d. `applicable` démarre à `null` (non statué), jamais `true` : une
// mission ne doit jamais afficher 93 décisions que le consultant n'a pas
// prises comme si elles l'étaient (zéro invention).
export type StatutSoa = "Implémenté" | "Partiel" | "Planifié" | null;
export type ThemeSoa = "Organisationnel" | "Personnel" | "Physique" | "Technologique";

export interface EntreeSoa {
  code: string;
  titre: string;
  theme: ThemeSoa;
  applicable: boolean | null;
  statut: StatutSoa;
  justification: string;
  document_reference: string;
  owner: string;
  date_revue: string;
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

/** Entretien mené avec une partie prenante — la check-list Hermes des 8-10
 *  interlocuteurs à rencontrer. */
export interface Entretien {
  id: string;
  role: string;
  personne: string;
  date: string;
  synthese: string;
}

/** Socle commun aux deux volets (schéma v2).
 *
 *  Modélisé et migré depuis le jalon 1, mais sans aucun écran jusqu'au
 *  30/07/2026 : le cadrage contractuel d'une mission n'était pas saisissable.
 */
export interface Socle {
  qualification?: {
    declencheur?: string;
    sponsor_executif?: string;
    budget?: string;
    maturite_actuelle?: string;
    equipe_interne?: string;
    echeance_cible?: string;
  };
  contractualisation?: {
    perimetre_inclus?: string;
    perimetre_exclu?: string;
    livrables?: string[];
    modalites?: string;
    acces_si?: string;
  };
  kickoff?: {
    date?: string;
    participants?: string[];
    gouvernance?: string;
  };
  entretiens?: Entretien[];
  temps?: { entrees: TempsEntree[] };
  rgpd_consultant?: {
    duree_conservation_mois: number;
    date_fin_mission: string;
    purge_effectuee_le: string;
  };
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
  socle?: Socle;
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
      // Référentiels actifs de la mission (31/07/2026) — framework_id/name
      // restent le référentiel « pivot » (premier choisi), framework_ids
      // porte la liste complète pour les missions multi-référentiel.
      framework_ids?: string[];
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
      violations?: ViolationDonnees[];
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
      strategie_remediation: StrategieRemediation;
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
      soa?: EntreeSoa[];
      preuves?: Preuve[];
    };
    restitution?: {
      exec_summary: string;
      remediation_plan: string[];
    };
  };
}
