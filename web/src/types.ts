// Types miroir de l'API GREEN SHIELD (api/main.py).

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
