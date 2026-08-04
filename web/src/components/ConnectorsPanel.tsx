import { useState, useRef } from "react";
import { Link2, CheckCircle2, AlertCircle, Loader2, ShieldAlert, Upload } from "lucide-react";
import { api } from "../lib/api";
import type { ProjectState } from "../types";

interface Props {
  project: ProjectState;
  onChange: (project: ProjectState) => void;
}

/**
 * Import Red Shield uniquement (31/07/2026) — trois autres « connecteurs »
 * (Microsoft 365, AWS, GitHub) ont été retirés : ils ne faisaient jamais
 * d'appel réel à ces API et écrivaient un texte de preuve entièrement
 * fabriqué dans les contrôles ISO 27001 de la mission, contraire à la
 * philosophie « zéro invention » du projet. Red Shield reste légitime :
 * il importe des données réellement parsées depuis un fichier déposé.
 */
export function ConnectorsPanel({ project, onChange }: Props) {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<{ status: string; count: number; details: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setScanning(true);
    try {
      const text = await file.text();
      const payload = JSON.parse(text);

      const res = await fetch(`/api/connectors/${project.id}/redshield`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error("Erreur import Red Shield");
      const data = await res.json();

      setResult({ status: data.status, count: data.updates_count, details: data.details });
      const updatedProject = await api.projects.get(project.id);
      onChange(updatedProject);
    } catch (e) {
      console.error(e);
      alert("Fichier JSON invalide ou erreur réseau.");
    } finally {
      setScanning(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="text-xl font-bold flex items-center gap-2">
          <Link2 className="text-[var(--accent)]" /> Import Red Shield
        </h3>
        <p className="text-sm text-[var(--soft)]">
          Importez les découvertes techniques (CVE, hôtes, HIDS) réellement remontées par un export Red Shield.
        </p>
      </div>

      <input
        type="file"
        accept=".json"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
      />

      <div className="glass p-5 border border-white/10 flex flex-col justify-between max-w-sm">
        <div>
          <div className="flex items-start justify-between mb-3">
            <div className="p-3 rounded-lg bg-red-500/10 text-red-500">
              <ShieldAlert size={24} />
            </div>
            {result && (
              <div className="text-[var(--accent)] flex items-center gap-1 text-xs font-bold bg-[var(--accent)]/10 px-2 py-1 rounded">
                <CheckCircle2 size={12} /> Sync
              </div>
            )}
          </div>
          <h4 className="font-bold text-[var(--ink)] mb-1">Red Shield</h4>
          <p className="text-xs text-[var(--faint)] leading-relaxed h-10">
            Importez les découvertes techniques (CVE, Hôtes, HIDS) depuis Red Shield.
          </p>
        </div>

        <div className="mt-5 pt-4 border-t border-white/5">
          {result ? (
            <div className="flex flex-col gap-2">
              <div className="text-xs text-[var(--soft)] flex items-center gap-2">
                <AlertCircle size={14} className="text-[var(--sky)]" />
                {result.count} élément(s) importé(s)
              </div>
              <div className="text-[10px] text-[var(--faint)] italic truncate">
                {result.details}
              </div>
            </div>
          ) : (
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={scanning}
              className="w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {scanning ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Import...
                </>
              ) : (
                <>
                  <Upload size={16} /> Importer SXF
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
