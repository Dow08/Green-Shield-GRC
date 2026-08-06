import { useEffect, useState, lazy, Suspense } from "react";
import { Menu, Loader2 } from "lucide-react";
import { Sidebar } from "./components/Sidebar";
import { Home } from "./pages/Home";
import { api, clearSession, subscribeToSessionExpired } from "./lib/api";
import type { ModuleInfo } from "./types";

// L'accueil est chargé d'emblée (c'est la première vue) ; les modules ne le
// sont qu'à leur ouverture. Sans découpage, ouvrir l'accueil téléchargeait
// aussi le registre de mission et ses six phases — l'essentiel du poids.
const AuditCraft = lazy(() => import("./pages/AuditCraft").then((m) => ({ default: m.AuditCraft })));
const Projects = lazy(() => import("./pages/Projects").then((m) => ({ default: m.Projects })));
const Settings = lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings })));
const CopilotGRC = lazy(() => import("./pages/CopilotGRC").then((m) => ({ default: m.CopilotGRC })));
const CollecteTechnique = lazy(() =>
  import("./pages/CollecteTechnique").then((m) => ({ default: m.CollecteTechnique })));
const BugTracker = lazy(() => import("./pages/BugTracker").then((m) => ({ default: m.BugTracker })));

function ChargementVue() {
  return (
    <div className="flex items-center gap-2 p-6 text-xs text-[var(--soft)]">
      <Loader2 size={14} className="animate-spin" /> Chargement du module…
    </div>
  );
}

// Modules "à venir" (feuille de route). Les trois sont désormais actifs !
const COMING: ModuleInfo[] = [
  {
    id: "missions",
    name: "Registre de missions",
    icon: "missions",
    category: "Pilotage",
    description: "Système de référence d'audit multi-clients (Mission → Finding → Livrable). Manuel autoguidé GRC & Conseil.",
    status: "active",
  },
  {
    id: "copilot",
    name: "Copilote GRC",
    icon: "copilot",
    category: "Assistance",
    description: "Assistant IA branché sur les constats : priorise, rédige, pilote les modules.",
    status: "active",
  },
  {
    id: "collect",
    name: "Collecte technique",
    icon: "collect",
    category: "Reconnaissance",
    description: "Recon & empreinte de configuration alimentant le registre.",
    status: "active",
  },
];

import { Auth } from "./pages/Auth";

export default function App() {
  const [modules, setModules] = useState<ModuleInfo[]>(COMING);
  const [view, setView] = useState("home");
  const [menuOuvert, setMenuOuvert] = useState(false);
  const [authView, setAuthView] = useState<"login"|"register">("login");
  // Trois états, pas un booléen : la simple présence d'un token ne prouve pas
  // qu'il est encore valide. Avant cette distinction (recette du 31/07/2026),
  // un token périmé faisait croire à l'application qu'elle était connectée,
  // tous les appels échouaient en 401 et l'utilisateur restait bloqué sur
  // « Token invalide » sans pouvoir revenir à l'écran de connexion.
  const [authState, setAuthState] = useState<"verification" | "connecte" | "deconnecte">(() => {
    try {
      return localStorage.getItem("greenshield_token") ? "verification" : "deconnecte";
    } catch {
      return "deconnecte";
    }
  });
  const isAuthenticated = authState === "connecte";

  const handleLogout = () => {
    // Révocation côté serveur en best-effort (V-03) : la déconnexion locale
    // ne doit jamais rester bloquée par un réseau coupé ou un jeton déjà
    // expiré — `clearSession()` s'exécute dans tous les cas.
    api.auth.logout().catch(() => {});
    clearSession();
    setAuthState("deconnecte");
    setView("home");
  };

  // Un 401 sur n'importe quel appel (token expiré, secret changé, compte
  // supprimé) ramène immédiatement à l'écran de connexion.
  useEffect(() => subscribeToSessionExpired(() => {
    setAuthState("deconnecte");
    setView("home");
  }), []);

  // Validation du token au démarrage — `/api/auth/me` est la route la moins
  // coûteuse qui exige une authentification.
  useEffect(() => {
    if (authState !== "verification") return;
    let annule = false;
    api.auth
      .me()
      .then(() => { if (!annule) setAuthState("connecte"); })
      .catch(() => { if (!annule) { clearSession(); setAuthState("deconnecte"); } });
    return () => { annule = true; };
  }, [authState]);

  useEffect(() => {
    if (!isAuthenticated) return;

    api
      .modules()
      .then((active) => {
        const merged = [...active];
        const hasMissions = active.some((m) => m.id === "missions");
        if (!hasMissions) {
          merged.push(COMING[0]);
        }
        merged.push(COMING[1]); // copilot
        merged.push(COMING[2]); // collect
        setModules(merged);
      })
      .catch(() => setModules(COMING));
  }, [isAuthenticated]);

  if (authState === "verification") {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--bg)] text-sm text-[var(--soft)]">
        Vérification de la session…
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Auth view={authView} setView={setAuthView} onLogin={() => setAuthState("connecte")} />;
  }

  return (
    // Sur petit écran l'application occupe toute la surface : la marge et les
    // coins arrondis du bureau y gaspilleraient une largeur déjà rare.
    <div className="mx-auto flex min-h-screen max-w-[1180px] items-stretch p-0 sm:p-4">
      <div className="flex w-full overflow-hidden border-[var(--stroke)] bg-white/[0.02] sm:rounded-[30px] sm:border sm:shadow-[0_30px_80px_rgba(0,0,0,0.5)]">
        <Sidebar
          view={view}
          onNavigate={setView}
          modules={modules}
          isOpen={menuOuvert}
          onClose={() => setMenuOuvert(false)}
          onLogout={handleLogout}
        />
        <main className="min-h-[560px] min-w-0 flex-1 overflow-hidden p-4 sm:p-6">
          {/* Déclencheur du tiroir : le rail latéral est masqué sous `md`. */}
          <button
            type="button"
            onClick={() => setMenuOuvert(true)}
            aria-label="Ouvrir le menu de navigation"
            aria-expanded={menuOuvert}
            className="mb-3 grid h-10 w-10 place-items-center rounded-2xl border border-[var(--stroke)] bg-white/[0.045] text-[var(--soft)] md:hidden"
          >
            <Menu size={18} />
          </button>

          {view === "home" && <Home modules={modules} onOpen={setView} />}
          <Suspense fallback={<ChargementVue />}>
            {view === "auditcraft_grc" && <AuditCraft />}
            {view === "missions" && <Projects />}
            {view === "copilot" && <CopilotGRC onNavigate={setView} />}
            {view === "collect" && <CollecteTechnique />}
            {view === "settings" && <Settings />}
            {view === "bugs" && <BugTracker />}
          </Suspense>
        </main>
      </div>
    </div>
  );
}
