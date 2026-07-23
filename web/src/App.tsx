import { useEffect, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Home } from "./pages/Home";
import { AuditCraft } from "./pages/AuditCraft";
import { api } from "./lib/api";
import type { ModuleInfo } from "./types";

// Modules "à venir" (feuille de route) affichés à côté des modules actifs de l'API.
const COMING: ModuleInfo[] = [
  {
    id: "missions",
    name: "Registre de missions",
    icon: "missions",
    category: "Pilotage",
    description: "Système de référence d'audit multi-clients (Mission → Finding → Livrable).",
    status: "soon",
  },
  {
    id: "copilot",
    name: "Copilote GRC",
    icon: "copilot",
    category: "Assistance",
    description: "Assistant IA branché sur les constats : priorise, rédige, pilote les modules.",
    status: "soon",
  },
  {
    id: "collect",
    name: "Collecte technique",
    icon: "collect",
    category: "Reconnaissance",
    description: "Recon & empreinte de configuration alimentant le registre.",
    status: "soon",
  },
];

export default function App() {
  const [modules, setModules] = useState<ModuleInfo[]>(COMING);
  const [view, setView] = useState("home");

  useEffect(() => {
    api
      .modules()
      .then((active) => setModules([...active, ...COMING]))
      .catch(() => setModules(COMING));
  }, []);

  return (
    <div className="mx-auto flex min-h-screen max-w-[1180px] items-stretch p-4">
      <div className="flex w-full overflow-hidden rounded-[30px] border border-[var(--stroke)] bg-white/[0.02] shadow-[0_30px_80px_rgba(0,0,0,0.5)]">
        <Sidebar view={view} onNavigate={setView} modules={modules} />
        <main className="min-h-[560px] flex-1 p-6">
          {view === "home" && <Home modules={modules} onOpen={setView} />}
          {view === "auditcraft_grc" && <AuditCraft />}
        </main>
      </div>
    </div>
  );
}
