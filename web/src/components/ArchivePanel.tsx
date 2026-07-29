import { useRef, useState } from "react";
import { Archive, Download, Upload, Loader2, ShieldCheck, AlertTriangle } from "lucide-react";

interface Props {
  missionName: string;
  onExport: (password: string) => Promise<void>;
  onImport: (file: File, password: string) => Promise<void>;
}

/**
 * Sauvegarde et restauration d'une mission (F14) sous forme d'archive chiffrée
 * AES-256 (F15). L'archive quitte le disque chiffré du poste : c'est le vecteur
 * le plus exposé, d'où le mot de passe obligatoire.
 */
export function ArchivePanel({ missionName, onExport, onImport }: Props) {
  const [exportPwd, setExportPwd] = useState("");
  const [importPwd, setImportPwd] = useState("");
  const [fichier, setFichier] = useState<File | null>(null);
  const [busy, setBusy] = useState<"export" | "import" | null>(null);
  const [message, setMessage] = useState<{ type: "ok" | "erreur"; texte: string } | null>(null);
  const inputFichier = useRef<HTMLInputElement>(null);

  const handleExport = async () => {
    if (exportPwd.length < 8) {
      setMessage({ type: "erreur", texte: "Le mot de passe doit faire au moins 8 caractères." });
      return;
    }
    setBusy("export");
    setMessage(null);
    try {
      await onExport(exportPwd);
      setExportPwd("");
      setMessage({ type: "ok", texte: "Archive chiffrée téléchargée. Conservez le mot de passe : il est indispensable pour la restaurer." });
    } catch (e) {
      setMessage({ type: "erreur", texte: e instanceof Error ? e.message : "Échec de l'export." });
    } finally {
      setBusy(null);
    }
  };

  const handleImport = async () => {
    if (!fichier) {
      setMessage({ type: "erreur", texte: "Sélectionnez une archive à restaurer." });
      return;
    }
    setBusy("import");
    setMessage(null);
    try {
      await onImport(fichier, importPwd);
      setFichier(null);
      setImportPwd("");
      if (inputFichier.current) inputFichier.current.value = "";
      setMessage({ type: "ok", texte: "Mission restaurée depuis l'archive." });
    } catch (e) {
      setMessage({ type: "erreur", texte: e instanceof Error ? e.message : "Échec de l'import." });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="glass p-4 flex flex-col gap-3">
      <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide flex items-center gap-1.5">
        <Archive size={12} /> Sauvegarde &amp; portabilité
      </span>

      <div className="flex items-start gap-2 text-[11px] text-[var(--soft)] bg-[rgba(46,230,160,0.05)] border border-[rgba(46,230,160,0.15)] rounded-xl p-2.5">
        <ShieldCheck size={14} className="text-[var(--g1)] shrink-0 mt-0.5" />
        <span>
          L'archive contient l'intégralité de la mission (données, configurations importées, rapports)
          et sort du disque chiffré de ce poste. Elle est donc <strong className="text-[var(--ink)]">chiffrée en AES-256</strong> :
          sans le mot de passe, elle est illisible — y compris par vous.
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Export */}
        <div className="flex flex-col gap-2">
          <span className="text-[11px] font-bold text-[var(--ink)]">Exporter « {missionName} »</span>
          <input
            type="password"
            placeholder="Mot de passe de chiffrement (8 caractères min.)"
            value={exportPwd}
            onChange={(e) => setExportPwd(e.target.value)}
            aria-label="Mot de passe de chiffrement de l'archive"
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <button
            type="button"
            onClick={handleExport}
            disabled={busy !== null}
            className="self-start bg-[var(--g1)] text-[#04150e] font-bold rounded-xl px-3 py-1.5 text-xs hover:opacity-90 disabled:opacity-40 flex items-center gap-1.5"
          >
            {busy === "export" ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
            {busy === "export" ? "Chiffrement…" : "Exporter l'archive"}
          </button>
        </div>

        {/* Import */}
        <div className="flex flex-col gap-2 md:border-l md:border-white/[0.05] md:pl-4">
          <span className="text-[11px] font-bold text-[var(--ink)]">Restaurer une mission</span>
          <input
            ref={inputFichier}
            type="file"
            accept=".zip"
            onChange={(e) => setFichier(e.target.files?.[0] ?? null)}
            aria-label="Fichier archive à sélectionner"
            className="text-[11px] text-[var(--soft)] file:mr-2 file:rounded-lg file:border-0 file:bg-white/[0.06] file:px-2.5 file:py-1 file:text-[11px] file:text-[var(--ink)]"
          />
          <input
            type="password"
            placeholder="Mot de passe de l'archive"
            value={importPwd}
            onChange={(e) => setImportPwd(e.target.value)}
            aria-label="Mot de passe de déchiffrement"
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <button
            type="button"
            onClick={handleImport}
            disabled={busy !== null}
            className="self-start bg-white/[0.06] border border-[var(--stroke)] text-[var(--ink)] font-bold rounded-xl px-3 py-1.5 text-xs hover:bg-white/[0.1] disabled:opacity-40 flex items-center gap-1.5"
          >
            {busy === "import" ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
            {busy === "import" ? "Restauration…" : "Restaurer"}
          </button>
        </div>
      </div>

      {message && (
        <div
          role="status"
          className={`text-[11px] flex items-start gap-1.5 ${
            message.type === "ok" ? "text-[var(--g1)]" : "text-[var(--rose)]"
          }`}
        >
          {message.type === "erreur" && <AlertTriangle size={13} className="shrink-0 mt-0.5" />}
          <span>{message.texte}</span>
        </div>
      )}
    </div>
  );
}
