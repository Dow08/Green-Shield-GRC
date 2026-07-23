import type { AuditResult, ModuleInfo } from "../types";

// En dev, Vite proxifie /api vers l'API FastAPI. En prod, nginx fait de même.
async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  modules: () => get<ModuleInfo[]>("/api/modules"),
  runAuditcraft: () => get<AuditResult>("/api/auditcraft/run"),
};
