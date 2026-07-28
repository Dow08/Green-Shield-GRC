import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Radar, ScanLine, Loader2, PlusCircle, CheckCircle2, FileWarning } from "lucide-react";
import { api } from "../lib/api";
import type { FingerprintResult, ProjectState, SuggestedAsset } from "../types";

const ASSET_TYPES = ["Logiciel", "Matériel", "Réseau", "Locaux", "RH"];

const TYPE_LABEL: Record<string, string> = {
  sshd_config: "OpenSSH (sshd_config)",
  nginx: "Nginx",
  apache: "Apache HTTPD",
  mysql: "MySQL / MariaDB",
  postgresql: "PostgreSQL",
  docker_compose: "Docker Compose",
  os_release: "Système d'exploitation",
  inconnu: "Non reconnu",
};

export function CollecteTechnique() {
  const [filename, setFilename] = useState("");
  const [content, setContent] = useState("");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<FingerprintResult | null>(null);
  const [error, setError] = useState("");

  const [asset, setAsset] = useState<SuggestedAsset>({ name: "", type: "Logiciel", description: "", owner: "" });
  const [projects, setProjects] = useState<ProjectState[]>([]);
  const [targetProjectId, setTargetProjectId] = useState("");
  const [importing, setImporting] = useState(false);
  const [imported, setImported] = useState(false);

  useEffect(() => {
    api.projects.list().then((list) => {
      setProjects(list);
      if (list.length > 0) setTargetProjectId(list[0].id);
    }).catch(() => setProjects([]));
  }, []);

  const handleScan = () => {
    if (!content.trim()) return;
    setScanning(true);
    setError("");
    setResult(null);
    setImported(false);
    api.collecte
      .fingerprint({ filename: filename || "config", content })
      .then((fp) => {
        setResult(fp);
        setAsset(fp.suggested_asset);
      })
      .catch((err) => setError(err.message))
      .finally(() => setScanning(false));
  };

  const handleImport = () => {
    if (!targetProjectId || !asset.name.trim()) return;
    setImporting(true);
    setImported(false);
    api.collecte
      .importAsset(targetProjectId, asset)
      .then(() => setImported(true))
      .catch((err) => alert("Échec de l'import : " + err.message))
      .finally(() => setImporting(false));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col h-full overflow-y-auto pr-2">
      <header className="mb-5">
        <h2 className="text-xl font-extrabold tracking-tight flex items-center gap-2">
          <Radar size={20} className="text-[var(--sky)]" /> Collecte technique
        </h2>
        <p className="text-xs text-[var(--soft)] mt-0.5">
          Empreinte factuelle d'un fichier de configuration (service, version, réglages présents) pour alimenter le registre des Biens Supports d'une mission. Aucun verdict de conformité ici — c'est le rôle d'AuditCraft-GRC.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* INPUT */}
        <div className="glass p-4 flex flex-col gap-3">
          <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">Fichier de configuration à analyser</span>
          <input
            type="text"
            placeholder="Nom du fichier (ex: sshd_config, nginx.conf, docker-compose.yml...)"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] font-mono focus:outline-none focus:border-[var(--g1)]"
          />
          <textarea
            placeholder="Collez ici le contenu réel du fichier de configuration…"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={12}
            className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] font-mono focus:outline-none focus:border-[var(--g1)] resize-none"
          />
          <button
            onClick={handleScan}
            disabled={scanning || !content.trim()}
            className="self-start px-4 py-2 bg-gradient-to-br from-[var(--sky)] to-[var(--g3)] text-[#04150e] font-bold rounded-xl text-xs hover:opacity-90 disabled:opacity-40 flex items-center gap-1.5"
          >
            <ScanLine size={14} className={scanning ? "animate-pulse" : ""} /> {scanning ? "Analyse..." : "Lancer l'empreinte"}
          </button>
          {error && (
            <div className="text-xs text-[var(--rose)] bg-[rgba(255,111,145,0.06)] border border-dashed border-[rgba(255,111,145,0.3)] p-2.5 rounded-xl flex items-center gap-2">
              <FileWarning size={13} /> {error}
            </div>
          )}
        </div>

        {/* RESULT + IMPORT */}
        <div className="glass p-4 flex flex-col gap-3">
          <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">Empreinte relevée</span>
          {!result && (
            <p className="text-xs text-[var(--soft)] italic">Aucune analyse effectuée pour l'instant.</p>
          )}
          {result && (
            <>
              <div className="bg-white/[0.02] border border-white/[0.03] rounded-xl p-3 flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--ink)]">{result.service}</span>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-[rgba(46,230,160,0.12)] text-[var(--g1)]">
                    {TYPE_LABEL[result.detected_type] ?? result.detected_type}
                  </span>
                </div>
                <div className="text-[10px] text-[var(--soft)]">
                  {result.directive_count} directive(s)/champ(s) relevé(s){result.version ? ` · version ${result.version}` : ""}
                </div>
                {result.flags.length > 0 && (
                  <div className="flex flex-col gap-1 mt-1 border-t border-white/[0.04] pt-1.5">
                    {result.flags.map((f) => (
                      <span key={f} className="text-[10px] font-mono text-[var(--faint)]">{f}</span>
                    ))}
                  </div>
                )}
              </div>

              <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide mt-1">Ajouter au registre (Biens Supports)</span>
              <select
                value={targetProjectId}
                onChange={(e) => setTargetProjectId(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              >
                {projects.length === 0 && <option value="">Aucune mission disponible</option>}
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} — {p.client}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Nom de l'actif"
                value={asset.name}
                onChange={(e) => setAsset({ ...asset, name: e.target.value })}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
              />
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={asset.type}
                  onChange={(e) => setAsset({ ...asset, type: e.target.value })}
                  className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                >
                  {ASSET_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                <input
                  type="text"
                  placeholder="Propriétaire (RSSI, DSI...)"
                  value={asset.owner}
                  onChange={(e) => setAsset({ ...asset, owner: e.target.value })}
                  className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
                />
              </div>
              <textarea
                placeholder="Description"
                value={asset.description}
                onChange={(e) => setAsset({ ...asset, description: e.target.value })}
                rows={2}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)] resize-none"
              />
              <button
                onClick={handleImport}
                disabled={importing || !targetProjectId || !asset.name.trim()}
                className="self-start px-4 py-2 bg-[var(--g1)] text-[#04150e] font-bold rounded-xl text-xs hover:opacity-90 disabled:opacity-40 flex items-center gap-1.5"
              >
                {importing ? <Loader2 size={14} className="animate-spin" /> : <PlusCircle size={14} />}
                {importing ? "Ajout..." : "Ajouter au registre"}
              </button>
              {imported && (
                <div className="text-xs text-[var(--g1)] flex items-center gap-1.5">
                  <CheckCircle2 size={13} /> Actif ajouté au registre de la mission.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}
