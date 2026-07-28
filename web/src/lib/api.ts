import type {
  AuditResult, ModuleInfo, ProjectState, Framework,
  CopilotContext, CopilotAskResult, FingerprintResult, SuggestedAsset,
} from "../types";
import type { Workflow } from "../types/workflow";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: any): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

async function put<T>(path: string, body: any): Promise<T> {
  const res = await fetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

async function deleteReq<T>(path: string): Promise<T> {
  const res = await fetch(path, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(path, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  modules: () => get<ModuleInfo[]>("/api/modules"),
  runAuditcraft: () => get<AuditResult>("/api/auditcraft/run"),
  
  projects: {
    list: () => get<ProjectState[]>("/api/projects"),
    create: (data: { name: string; client: string; type: "grc" | "consulting"; framework_id?: string }) => 
      post<ProjectState>("/api/projects", data),
    get: (id: string) => get<ProjectState>(`/api/projects/${id}`),
    update: (id: string, state: ProjectState) => put<ProjectState>(`/api/projects/${id}`, state),
    delete: (id: string) => deleteReq<{ status: string; message: string }>(`/api/projects/${id}`),
    upload: (id: string, file: File) => uploadFile<ProjectState>(`/api/projects/${id}/upload`, file),
    runAudit: (id: string) => post<ProjectState>(`/api/projects/${id}/audit`, {}),
    exportDoc: (id: string, docType: string) => get<{ title: string; markdown: string }>(`/api/projects/${id}/export/${docType}`),
    // Rapport Word natif : l'identité de l'auditeur vient des Réglages (localStorage),
    // elle n'est pas stockée côté serveur.
    reportDocxUrl: (id: string) => {
      const params = new URLSearchParams({
        auditeur: localStorage.getItem("consultant_name") ?? "",
        cabinet: localStorage.getItem("consultant_company") ?? "",
      });
      return `/api/projects/${id}/report.docx?${params}`;
    },
  },
  
  frameworks: {
    list: () => get<Framework[]>("/api/frameworks"),
    import: (data: any) => post<{ status: string; id: string }>("/api/frameworks/import", data),
    workflow: (fwId: string) => get<Workflow>(`/api/frameworks/${fwId}/workflow`),
  },

  copilot: {
    context: () => get<CopilotContext>("/api/copilot/context"),
    ask: (data: { prompt: string; key: string }) => post<CopilotAskResult>("/api/copilot/ask", data),
  },

  collecte: {
    fingerprint: (data: { filename: string; content: string }) =>
      post<FingerprintResult>("/api/collecte/fingerprint", data),
    importAsset: (projectId: string, data: SuggestedAsset) =>
      post<ProjectState>(`/api/projects/${projectId}/collecte/import`, data),
  },
};
