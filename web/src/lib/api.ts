import type {
  AuditResult, ModuleInfo, ProjectState, Framework,
  CopilotContext, CopilotAskResult, FingerprintResult, SuggestedAsset, PhaseTemps,
  RevueExportResult, SnapshotInfo, EcheanceRgpdMission, CouvertureTechnique,
  FrameworkDetail, Exigence, ReferenceObligationAIPD,
  PratiqueControle, EtatControlesTechniques,
} from "../types";
import { safeGetItem } from "./storage";
import type { Workflow } from "../types/workflow";

/**
 * Extrait le message d'erreur métier renvoyé par FastAPI (champ `detail`).
 * Sans ça l'utilisateur ne voit que « HTTP 400 » là où l'API dit précisément
 * « Mot de passe incorrect » ou « Une mission « acme » existe déjà ».
 */
export async function errorDetail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data && typeof data.detail === "string") return data.detail;
  } catch {
    // Corps vide ou non-JSON : on retombe sur le code HTTP.
  }
  return `HTTP ${res.status}`;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

async function deleteReq<T>(path: string): Promise<T> {
  const res = await fetch(path, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(path, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

// Nom de fichier porté par l'en-tête `Content-Disposition` (RFC 5987) — en
// POST + blob, le navigateur ne le déduit plus tout seul comme il le ferait
// pour un simple lien <a href download>.
function nomDepuisContentDisposition(res: Response, repli: string): string {
  const entete = res.headers.get("Content-Disposition") ?? "";
  const utf8 = entete.match(/filename\*=UTF-8''([^;]+)/);
  if (utf8) return decodeURIComponent(utf8[1]);
  const ascii = entete.match(/filename="([^"]+)"/);
  return ascii ? ascii[1] : repli;
}

// Déclenche le téléchargement d'un export Word : même identité auditeur /
// cabinet / logo (Réglages) pour les cinq livrables, factorisée pour ne pas
// la répéter à chaque helper. En POST (et non un simple lien GET) depuis le
// 30/07/2026 : le logo personnalisé en base64 dépasserait une longueur
// d'URL sûre en paramètre de requête.
async function downloadDocx(id: string, route: string): Promise<void> {
  const res = await fetch(`/api/projects/${id}/${route}.docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      auditeur: safeGetItem("consultant_name") ?? "",
      cabinet: safeGetItem("consultant_company") ?? "",
      logo: safeGetItem("consultant_logo") ?? "",
    }),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  const blob = await res.blob();
  const nom = nomDepuisContentDisposition(res, `${route}.docx`);
  const url = URL.createObjectURL(blob);
  const lien = document.createElement("a");
  lien.href = url;
  lien.download = nom;
  document.body.appendChild(lien);
  lien.click();
  lien.remove();
  URL.revokeObjectURL(url);
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
    revue: (id: string) => get<RevueExportResult>(`/api/projects/${id}/revue`),
    couverture: (id: string) => get<CouvertureTechnique>(`/api/projects/${id}/couverture`),
    createDemo: () => post<ProjectState>("/api/projects/demo", {}),
    echeancesRgpd: () => get<EcheanceRgpdMission[]>("/api/rgpd/echeances"),
    updateRgpd: (id: string, politique: { duree_conservation_mois: number; date_fin_mission: string }) =>
      put<ProjectState>(`/api/projects/${id}/rgpd`, politique),
    purgerRgpd: (id: string) =>
      post<{ status: string; efface: number; state: ProjectState }>(`/api/projects/${id}/rgpd/purge`, {}),
    snapshots: (id: string) => get<SnapshotInfo[]>(`/api/projects/${id}/snapshots`),
    restoreSnapshot: (id: string, nom: string) =>
      post<ProjectState>(`/api/projects/${id}/snapshots/${nom}/restore`, {}),
    addTemps: (id: string, entry: { phase: PhaseTemps; minutes: number; date?: string; note?: string }) =>
      post<ProjectState>(`/api/projects/${id}/temps`, entry),
    // TPRM : le navigateur n'envoie que les curseurs. La notation appartient au
    // serveur, sans quoi deux copies de la formule finissent par diverger.
    addTiers: (id: string, tiers: { name: string; dependence: number; penetration: number; maturity: number; trust: number }) =>
      post<ProjectState>(`/api/projects/${id}/tprm/tiers`, tiers),
    setExigenceTiers: (id: string, index: number, exigenceId: string, valeur: { satisfait: boolean; preuve?: string }) =>
      put<ProjectState>(`/api/projects/${id}/tprm/tiers/${index}/exigences/${exigenceId}`, valeur),
    recalculerTprm: (id: string) =>
      post<{ status: string; recalcules: number; state: ProjectState }>(`/api/projects/${id}/tprm/recalculer`, {}),
    // Archive chiffrée : le mot de passe passe par le corps de la requête,
    // jamais par l'URL (qui finirait dans les journaux d'accès).
    exportArchive: async (id: string, password: string): Promise<Blob> => {
      const res = await fetch(`/api/projects/${id}/archive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) throw new Error(await errorDetail(res));
      return res.blob();
    },
    importArchive: async (file: File, password: string): Promise<ProjectState> => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("password", password);
      const res = await fetch("/api/projects/import-archive", { method: "POST", body: formData });
      if (!res.ok) throw new Error(await errorDetail(res));
      return res.json() as Promise<ProjectState>;
    },
    deleteTemps: (id: string, entryId: string) =>
      deleteReq<ProjectState>(`/api/projects/${id}/temps/${entryId}`),
    exportDoc: (id: string, docType: string) => {
      const params = new URLSearchParams({
        auditeur: safeGetItem("consultant_name") ?? "",
        cabinet: safeGetItem("consultant_company") ?? "",
      });
      return get<{ title: string; markdown: string }>(`/api/projects/${id}/export/${docType}?${params}`);
    },
    // Rapport Word natif : l'identité de l'auditeur (et son logo) vient des
    // Réglages (localStorage), elle n'est pas stockée côté serveur.
    downloadReportDocx: (id: string) => downloadDocx(id, "report"),
    // NDA, EBIOS RM, PSSI/PRI, AIPD : même identité Word que le rapport de
    // mission, mêmes conventions d'auditeur/cabinet/logo issues des Réglages.
    downloadNdaDocx: (id: string) => downloadDocx(id, "nda"),
    downloadEbiosDocx: (id: string) => downloadDocx(id, "ebios"),
    downloadPssiDocx: (id: string) => downloadDocx(id, "pssi"),
    downloadAipdDocx: (id: string) => downloadDocx(id, "aipd"),
    // Déclaration d'Applicabilité (SoA) : n'existe que sur une mission ISO
    // 27001 — l'API répond 404 sinon, remonté via l'erreur du fetch.
    downloadSoaDocx: (id: string) => downloadDocx(id, "soa"),
  },
  
  frameworks: {
    list: () => get<Framework[]>("/api/frameworks"),
    detail: (fwId: string) => get<FrameworkDetail>(`/api/frameworks/${fwId}/detail`),
    import: (data: { id: string; name: string; description?: string; requirements?: Exigence[] }) =>
      post<{ status: string; id: string }>("/api/frameworks/import", data),
    workflow: (fwId: string) => get<Workflow>(`/api/frameworks/${fwId}/workflow`),
  },

  aipd: {
    obligations: () => get<ReferenceObligationAIPD[]>("/api/aipd/obligations"),
  },

  controles: {
    referentiel: () => get<PratiqueControle[]>("/api/controles-techniques"),
    etat: (id: string) => get<EtatControlesTechniques>(`/api/projects/${id}/controles-techniques`),
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
