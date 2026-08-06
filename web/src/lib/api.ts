import type {
  AuditResult, ModuleInfo, ProjectState, Framework,
  CopilotContext, CopilotAskResult, FingerprintResult, SuggestedAsset, PhaseTemps,
  RevueExportResult, SnapshotInfo, EcheanceRgpdMission, CouvertureTechnique,
  FrameworkDetail, Exigence, ReferenceObligationAIPD,
  PratiqueControle, EtatControlesTechniques,
  MaterielInfo, MesureModele,
  RegistreDemandesPreuves, ControleLie, StatutDemande, CarteNist,
  SuggestionPreuve, LoginResult, UserProfile, MessageResponse,
  FonctionMaturite, ProfilMaturiteNist,
} from "../types";
import { safeGetItem } from "./storage";
import type { Workflow } from "../types/workflow";

// --- API LOGGER SYSTEM ---
export interface ApiLog {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  status?: number;
  durationMs?: number;
  error?: string;
}

export const apiLogs: ApiLog[] = [];
const logSubscribers = new Set<() => void>();

export function subscribeToApiLogs(callback: () => void) {
  logSubscribers.add(callback);
  return () => {
    logSubscribers.delete(callback);
  };
}

function notifySubscribers() {
  logSubscribers.forEach((cb) => cb());
}

function addApiLog(log: ApiLog) {
  apiLogs.unshift(log);
  if (apiLogs.length > 50) {
    apiLogs.pop(); // Keep only last 50 requests
  }
  notifySubscribers();
}
// -----------------------

function getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = localStorage.getItem("greenshield_token");
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// --- Expiration de session (recette du 31/07/2026) ---
// Un token périmé ou signé par un secret désormais différent faisait échouer
// tous les appels en 401, sans que l'application ne s'en rende compte : elle
// se croyait connectée et affichait « Token invalide » sans issue. Toutes les
// requêtes passant par `handleResponse`, c'est le seul endroit à instrumenter.
const sessionExpiredSubscribers = new Set<() => void>();

export function subscribeToSessionExpired(callback: () => void) {
  sessionExpiredSubscribers.add(callback);
  return () => {
    sessionExpiredSubscribers.delete(callback);
  };
}

export function clearSession() {
  try {
    localStorage.removeItem("greenshield_token");
    localStorage.removeItem("greenshield_premium");
  } catch {
    // Navigation privée / quota : la purge mémoire suffit à sortir de l'impasse.
  }
}

async function handleResponse(res: Response) {
  if (res.status === 401) {
    // Un 401 *sans* token stocké est un échec d'identification normal
    // (mot de passe erroné) : ce n'est pas une session expirée, et prévenir
    // l'application ferait clignoter l'écran de connexion pour rien.
    const avaitUnToken = !!localStorage.getItem("greenshield_token");
    if (avaitUnToken) {
      clearSession();
      sessionExpiredSubscribers.forEach((cb) => cb());
    }
  }
  if (!res.ok) throw new Error(await errorDetail(res));
}

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
  const logId = crypto.randomUUID();
  const startTime = performance.now();
  let status: number | undefined;
  let errorMsg: string | undefined;

  try {
    // `no-store` : ces routes décrivent un état vivant (missions en cours,
    // matériel du poste, modèles installés). Sans cette consigne, le
    // navigateur ressert sa copie et l'utilisateur voit un état périmé après
    // avoir cliqué — constaté en recette le 05/08/2026 sur la détection
    // matérielle, qui renvoyait la réponse précédente.
    const res = await fetch(path, { headers: getHeaders(), cache: "no-store" });
    status = res.status;
    await handleResponse(res);
    return res.json() as Promise<T>;
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    addApiLog({
      id: logId,
      timestamp: new Date().toLocaleTimeString("fr-FR"),
      method: "GET",
      url: path,
      status,
      durationMs: Math.round(performance.now() - startTime),
      error: errorMsg,
    });
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const logId = crypto.randomUUID();
  const startTime = performance.now();
  let status: number | undefined;
  let errorMsg: string | undefined;

  try {
    const res = await fetch(path, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    });
    status = res.status;
    await handleResponse(res);
    return res.json() as Promise<T>;
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    addApiLog({
      id: logId,
      timestamp: new Date().toLocaleTimeString("fr-FR"),
      method: "POST",
      url: path,
      status,
      durationMs: Math.round(performance.now() - startTime),
      error: errorMsg,
    });
  }
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const logId = crypto.randomUUID();
  const startTime = performance.now();
  let status: number | undefined;
  let errorMsg: string | undefined;

  try {
    const res = await fetch(path, {
      method: "PUT",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    });
    status = res.status;
    await handleResponse(res);
    return res.json() as Promise<T>;
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    addApiLog({
      id: logId,
      timestamp: new Date().toLocaleTimeString("fr-FR"),
      method: "PUT",
      url: path,
      status,
      durationMs: Math.round(performance.now() - startTime),
      error: errorMsg,
    });
  }
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const logId = crypto.randomUUID();
  const startTime = performance.now();
  let status: number | undefined;
  let errorMsg: string | undefined;

  try {
    const res = await fetch(path, {
      method: "PATCH",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    });
    status = res.status;
    await handleResponse(res);
    return res.json() as Promise<T>;
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    addApiLog({
      id: logId,
      timestamp: new Date().toLocaleTimeString("fr-FR"),
      method: "PATCH",
      url: path,
      status,
      durationMs: Math.round(performance.now() - startTime),
      error: errorMsg,
    });
  }
}

async function deleteReq<T>(path: string): Promise<T> {
  const logId = crypto.randomUUID();
  const startTime = performance.now();
  let status: number | undefined;
  let errorMsg: string | undefined;

  try {
    const res = await fetch(path, { method: "DELETE", headers: getHeaders() });
    status = res.status;
    await handleResponse(res);
    return res.json() as Promise<T>;
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    addApiLog({
      id: logId,
      timestamp: new Date().toLocaleTimeString("fr-FR"),
      method: "DELETE",
      url: path,
      status,
      durationMs: Math.round(performance.now() - startTime),
      error: errorMsg,
    });
  }
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(path, {
    method: "POST",
    headers: getHeaders(),
    body: formData,
  });
  await handleResponse(res);
  return res.json() as Promise<T>;
}

// Nom de fichier porté par l'en-tête `Content-Disposition` (RFC 5987) — en
// POST + blob, le navigateur ne le déduit plus tout seul comme il le ferait
// pour un simple lien <a href download>.
/**
 * Ouvre un livrable au format « impression » dans un nouvel onglet.
 *
 * Ces vues étaient jusqu'ici ouvertes par `window.open("/api/…/pdf/…")`. Une
 * navigation d'URL ne porte aucun en-tête : depuis que les routes d'export
 * exigent une authentification, l'onglet n'affichait plus qu'un
 * « Jeton d'accès manquant ou invalide ». On récupère donc le document par
 * `fetch` (qui, lui, joint le jeton) avant de l'écrire dans l'onglet.
 *
 * L'onglet est ouvert **avant** le premier `await` : un `window.open` différé
 * n'est plus rattaché au clic de l'utilisateur et se fait bloquer.
 */
async function openPrintableReport(id: string, docType: string): Promise<void> {
  const onglet = window.open("", "_blank");
  try {
    const params = new URLSearchParams({
      auditeur: safeGetItem("consultant_name") ?? "",
      cabinet: safeGetItem("consultant_company") ?? "",
    });
    const res = await fetch(`/api/projects/${id}/pdf/${docType}?${params}`, {
      headers: getHeaders(),
    });
    await handleResponse(res);
    const html = await res.text();
    if (!onglet) {
      throw new Error("Ouverture de l'onglet bloquée par le navigateur.");
    }
    onglet.document.open();
    onglet.document.write(html);
    onglet.document.close();
  } catch (err) {
    onglet?.close();
    throw err;
  }
}

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
    headers: getHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      auditeur: safeGetItem("consultant_name") ?? "",
      cabinet: safeGetItem("consultant_company") ?? "",
      logo: safeGetItem("consultant_logo") ?? "",
    }),
  });
  await handleResponse(res);
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
    create: (data: { name: string; client: string; type: "grc" | "consulting"; framework_id?: string; framework_ids?: string[] }) =>
      post<ProjectState>("/api/projects", data),
    get: (id: string) => get<ProjectState>(`/api/projects/${id}`),
    update: (id: string, state: ProjectState) => put<ProjectState>(`/api/projects/${id}`, state),
    delete: (id: string) => deleteReq<{ status: string; message: string }>(`/api/projects/${id}`),
    upload: (id: string, file: File) => uploadFile<ProjectState>(`/api/projects/${id}/upload`, file),
    runAudit: (id: string) => post<ProjectState>(`/api/projects/${id}/audit`, {}),
    revue: (id: string) => get<RevueExportResult>(`/api/projects/${id}/revue`),
    couverture: (id: string) => get<CouvertureTechnique>(`/api/projects/${id}/couverture`),
    createDemo: () => post<ProjectState>("/api/projects/demo", {}),
    copilotGenerate: (prompt: string) => post<{ name: string; client: string; type: string; framework_ids?: string[] }>("/api/projects/copilot/generate", { prompt }),
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
    getSuggestions: (id: string) => get<SuggestionPreuve[]>(`/api/projects/${id}/preuves/suggestions`),
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
        headers: getHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ password }),
      });
      await handleResponse(res);
      return res.blob();
    },
    importArchive: async (file: File, password: string): Promise<ProjectState> => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("password", password);
      const res = await fetch("/api/projects/import-archive", { 
        method: "POST", 
        headers: getHeaders(), 
        body: formData 
      });
      await handleResponse(res);
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
    // Vue « impression » (PDF via le navigateur) — authentifiée, cf.
    // `openPrintableReport`.
    openPdf: (id: string, docType: string) => openPrintableReport(id, docType),

    // Registre des demandes de preuves (socle de mission). Chaque mutation
    // renvoie la mission entière, comme le suivi du temps.
    demandesPreuves: (id: string) =>
      get<RegistreDemandesPreuves>(`/api/projects/${id}/demandes-preuves`),
    addDemandePreuve: (
      id: string,
      data: { libelle: string; destinataire?: string; echeance?: string; note?: string; controles_lies?: ControleLie[] },
    ) => post<ProjectState>(`/api/projects/${id}/demandes-preuves`, data),
    updateDemandePreuve: (
      id: string,
      demandeId: string,
      data: { statut: StatutDemande; note?: string; preuve_id?: string },
    ) => patch<ProjectState>(`/api/projects/${id}/demandes-preuves/${demandeId}`, data),
    deleteDemandePreuve: (id: string, demandeId: string) =>
      deleteReq<ProjectState>(`/api/projects/${id}/demandes-preuves/${demandeId}`),

    // Roue NIST CSF : rattachement des contrôles aux six fonctions.
    nistCsf: (id: string) => get<CarteNist>(`/api/projects/${id}/nist-csf`),

    // Radar de maturité NIST CSF : auto-évaluation déclarative (Tier 1-4),
    // distincte de la roue de rattachement ci-dessus.
    maturiteNist: (id: string) => get<ProfilMaturiteNist>(`/api/projects/${id}/maturite-nist`),
    definirMaturiteNist: (id: string, code: FonctionMaturite["code"], data: { tier: 1 | 2 | 3 | 4 | null; justification?: string }) =>
      put<ProjectState>(`/api/projects/${id}/maturite-nist/${code}`, data),
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
    ask: (data: { prompt: string; key: string; fournisseur?: string; modele?: string }) =>
      post<CopilotAskResult>("/api/copilot/ask", data),
    // Capacités du poste et modèle local recommandé. Lecture seule, instantané.
    materiel: () => get<MaterielInfo>("/api/copilot/materiel"),
    // Chronométrage réel d'un modèle local. Peut durer plusieurs minutes au
    // premier appel (chargement du modèle) : prévenir l'utilisateur avant.
    testerModele: (modele: string) =>
      post<MesureModele>("/api/copilot/materiel/test", { modele }),
  },

  collecte: {
    fingerprint: (data: { filename: string; content: string }) =>
      post<FingerprintResult>("/api/collecte/fingerprint", data),
    importAsset: (projectId: string, data: SuggestedAsset) =>
      post<ProjectState>(`/api/projects/${projectId}/collecte/import`, data),
  },

  auth: {
    login: (data: { email: string; password: string }) => post<LoginResult>("/api/auth/login", data),
    register: (data: { email: string; password: string }) => post<MessageResponse>("/api/auth/register", data),
    activate: (data: { license_key: string }) => post<MessageResponse>("/api/auth/activate", data),
    me: () => get<UserProfile>("/api/auth/me"),
  },
};
