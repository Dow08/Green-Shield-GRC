import { useState, useEffect } from "react";
import { Bug, Download, Trash2, PlusCircle, AlertCircle, Activity } from "lucide-react";
import { apiLogs, subscribeToApiLogs, type ApiLog } from "../lib/api";

interface BugReport {
  id: string;
  titre: string;
  description: string;
  severite: "Basse" | "Moyenne" | "Haute" | "Critique";
  etapes: string;
  date: string;
}

export function BugTracker() {
  const [bugs, setBugs] = useState<BugReport[]>([]);
  const [logs, setLogs] = useState<ApiLog[]>([...apiLogs]);
  const [nouveauTitre, setNouveauTitre] = useState("");
  const [nouvelleDescription, setNouvelleDescription] = useState("");
  const [nouvelleSeverite, setNouvelleSeverite] = useState<BugReport["severite"]>("Moyenne");
  const [nouvellesEtapes, setNouvellesEtapes] = useState("");

  // Charger depuis LocalStorage et s'abonner aux logs API
  useEffect(() => {
    const saved = localStorage.getItem("green_shield_bugs");
    if (saved) {
      try {
        setBugs(JSON.parse(saved));
      } catch (e) {
        console.error("Erreur lecture bugs", e);
      }
    }

    const unsubscribe = subscribeToApiLogs(() => {
      setLogs([...apiLogs]);
    });
    return () => unsubscribe();
  }, []);

  // Sauvegarder dans LocalStorage à chaque modification
  useEffect(() => {
    localStorage.setItem("green_shield_bugs", JSON.stringify(bugs));
  }, [bugs]);

  const handleAddBug = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nouveauTitre.trim()) return;

    const newBug: BugReport = {
      id: crypto.randomUUID(),
      titre: nouveauTitre,
      description: nouvelleDescription,
      severite: nouvelleSeverite,
      etapes: nouvellesEtapes,
      date: new Date().toLocaleString("fr-FR"),
    };

    setBugs([newBug, ...bugs]);
    setNouveauTitre("");
    setNouvelleDescription("");
    setNouvelleSeverite("Moyenne");
    setNouvellesEtapes("");
  };

  const handleDelete = (id: string) => {
    if (confirm("Supprimer ce bug ?")) {
      setBugs(bugs.filter((b) => b.id !== id));
    }
  };

  const handleDownload = () => {
    if (bugs.length === 0) {
      alert("Aucun bug à exporter.");
      return;
    }

    let contenu = "RAPPORT DE BUGS - GREEN SHIELD\n";
    contenu += `Généré le: ${new Date().toLocaleString("fr-FR")}\n`;
    contenu += `Total des bugs: ${bugs.length}\n`;
    contenu += "=========================================\n\n";

    bugs.forEach((b, index) => {
      contenu += `BUG #${index + 1}: ${b.titre}\n`;
      contenu += `Date: ${b.date}\n`;
      contenu += `Sévérité: ${b.severite}\n`;
      contenu += `Description:\n${b.description || "N/A"}\n`;
      contenu += `Étapes pour reproduire:\n${b.etapes || "N/A"}\n`;
      contenu += "-----------------------------------------\n\n";
    });

    contenu += "\n=== DERNIERS APPELS API (CONTEXTE RÉSEAU) ===\n";
    logs.slice(0, 50).forEach((l) => {
      contenu += `[${l.timestamp}] ${l.method} ${l.url} - Statut: ${l.status || "Erreur"} (${l.durationMs}ms)\n`;
      if (l.error) contenu += `   Erreur: ${l.error}\n`;
    });

    const blob = new Blob([contenu], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `rapport_bugs_${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-full flex-col gap-6 overflow-hidden">
      <div className="flex-none flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2 text-[var(--ink)]">
            <Bug className="text-[var(--rose)]" /> Journalisation des Bugs
          </h2>
          <p className="text-sm text-[var(--faint)]">
            Consignez les comportements inattendus pendant vos scénarios de test.
          </p>
        </div>
        <button
          onClick={handleDownload}
          className="flex items-center gap-2 rounded-xl bg-[var(--g1)] px-4 py-2 text-sm font-bold text-[#04150e] shadow-[0_0_15px_rgba(46,230,160,0.3)] transition hover:scale-105"
        >
          <Download size={16} /> Exporter le Rapport (.txt)
        </button>
      </div>

      <div className="flex flex-1 gap-6 overflow-hidden flex-col md:flex-row">
        {/* Formulaire */}
        <div className="glass-2 p-5 md:w-1/3 flex flex-col gap-4 overflow-y-auto rounded-2xl">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <PlusCircle size={18} className="text-[var(--sky)]" /> Signaler un bug
          </h3>
          <form onSubmit={handleAddBug} className="flex flex-col gap-3">
            <div>
              <label className="text-xs font-bold text-[var(--soft)] mb-1 block">Titre (Court)</label>
              <input
                required
                value={nouveauTitre}
                onChange={(e) => setNouveauTitre(e.target.value)}
                placeholder="Ex: Crash bouton IA"
                className="w-full rounded-lg border border-[var(--stroke)] bg-[var(--bg2)] px-3 py-2 text-sm text-[var(--ink)] placeholder:text-white/20 focus:border-[var(--g1)] focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-[var(--soft)] mb-1 block">Sévérité</label>
              <select
                value={nouvelleSeverite}
                onChange={(e) => setNouvelleSeverite(e.target.value as BugReport["severite"])}
                className="w-full rounded-lg border border-[var(--stroke)] bg-[var(--bg2)] px-3 py-2 text-sm text-[var(--ink)] focus:border-[var(--g1)] focus:outline-none"
              >
                <option value="Basse">Basse (Cosmétique)</option>
                <option value="Moyenne">Moyenne (Gênant)</option>
                <option value="Haute">Haute (Fonction cassée)</option>
                <option value="Critique">Critique (Crash de l'app)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-[var(--soft)] mb-1 block">Description détaillée</label>
              <textarea
                value={nouvelleDescription}
                onChange={(e) => setNouvelleDescription(e.target.value)}
                placeholder="Que s'est-il passé ?"
                className="w-full h-24 resize-none rounded-lg border border-[var(--stroke)] bg-[var(--bg2)] px-3 py-2 text-sm text-[var(--ink)] placeholder:text-white/20 focus:border-[var(--g1)] focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-[var(--soft)] mb-1 block">Étapes pour reproduire</label>
              <textarea
                value={nouvellesEtapes}
                onChange={(e) => setNouvellesEtapes(e.target.value)}
                placeholder="1. Clic sur le bouton\n2. Saisie texte\n3. Erreur"
                className="w-full h-24 resize-none rounded-lg border border-[var(--stroke)] bg-[var(--bg2)] px-3 py-2 text-sm text-[var(--ink)] placeholder:text-white/20 focus:border-[var(--g1)] focus:outline-none font-mono text-xs"
              />
            </div>

            <button
              type="submit"
              className="mt-2 w-full rounded-lg bg-[rgba(255,255,255,0.05)] py-2 text-sm font-bold transition hover:bg-[rgba(255,255,255,0.1)] border border-[var(--stroke)]"
            >
              Enregistrer le Bug
            </button>
          </form>
        </div>

        {/* Liste des bugs */}
        <div className="glass-2 p-5 flex-1 flex flex-col gap-4 overflow-hidden rounded-2xl">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <AlertCircle size={18} className="text-[var(--rose)]" /> Bugs Consignés ({bugs.length})
          </h3>
          <div className="flex-1 overflow-y-auto flex flex-col gap-3 pr-2">
            {bugs.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm italic text-[var(--faint)]">
                Aucun bug signalé pour le moment. Tout va bien !
              </div>
            ) : (
              bugs.map((b) => (
                <div key={b.id} className="rounded-xl border border-[var(--stroke)] bg-white/[0.02] p-4 flex flex-col gap-2 relative group hover:bg-white/[0.04] transition">
                  <div className="flex items-start justify-between">
                    <h4 className="font-bold text-[var(--ink)] text-sm">{b.titre}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                      b.severite === "Critique" || b.severite === "Haute" ? "bg-[rgba(255,111,145,0.15)] text-[var(--rose)]" : 
                      b.severite === "Moyenne" ? "bg-[rgba(255,207,107,0.15)] text-[var(--amber,#ffcf6b)]" : 
                      "bg-white/10 text-[var(--soft)]"
                    }`}>
                      {b.severite}
                    </span>
                  </div>
                  <div className="text-[10px] text-[var(--faint)]">{b.date}</div>
                  
                  {b.description && (
                    <div className="mt-1">
                      <div className="text-[10px] font-bold text-[var(--soft)]">Description:</div>
                      <div className="text-xs text-[var(--faint)] whitespace-pre-wrap">{b.description}</div>
                    </div>
                  )}

                  {b.etapes && (
                    <div className="mt-1">
                      <div className="text-[10px] font-bold text-[var(--soft)]">Reproduction:</div>
                      <div className="text-xs font-mono text-[var(--faint)] whitespace-pre-wrap p-2 bg-black/20 rounded mt-1">{b.etapes}</div>
                    </div>
                  )}

                  <button
                    onClick={() => handleDelete(b.id)}
                    className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition text-[var(--soft)] hover:text-[var(--rose)] p-1 rounded hover:bg-white/5"
                    title="Supprimer ce bug"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Section des logs réseau en direct */}
      <div className="flex-none h-48 glass-2 p-5 flex flex-col gap-3 rounded-2xl">
        <h3 className="text-sm font-bold flex items-center gap-2 text-[var(--soft)]">
          <Activity size={16} /> Console API Live (50 dernières requêtes)
        </h3>
        <div className="flex-1 overflow-y-auto bg-black/40 rounded-xl p-3 font-mono text-[10px] leading-tight flex flex-col gap-1 border border-white/5">
          {logs.length === 0 ? (
            <div className="text-[var(--faint)] italic">Aucune requête réseau détectée pour le moment...</div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex gap-2 whitespace-nowrap">
                <span className="text-[var(--faint)]">[{log.timestamp}]</span>
                <span className={`font-bold ${
                  log.method === "GET" ? "text-blue-400" :
                  log.method === "POST" ? "text-green-400" :
                  log.method === "DELETE" ? "text-red-400" :
                  "text-purple-400"
                }`}>{log.method}</span>
                <span className="text-white/80">{log.url}</span>
                <span className={`ml-auto font-bold ${
                  log.status && log.status >= 200 && log.status < 300 ? "text-[var(--g1)]" : "text-[var(--rose)]"
                }`}>
                  {log.status || "ERR"}
                </span>
                <span className="text-[var(--faint)] w-12 text-right">{log.durationMs}ms</span>
                {log.error && <span className="text-[var(--rose)] truncate ml-2">({log.error})</span>}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
