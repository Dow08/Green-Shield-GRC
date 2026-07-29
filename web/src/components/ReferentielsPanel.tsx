import { useState } from "react";
import { BookOpen, Plus, Trash2, Save, Loader2, Lock, AlertTriangle } from "lucide-react";
import type { Framework, FrameworkDetail, Exigence } from "../types";

interface Props {
  frameworks: Framework[];
  onCharger: (id: string) => Promise<FrameworkDetail>;
  onEnregistrer: (data: { id: string; name: string; description: string; requirements: Exigence[] }) => Promise<void>;
}

/**
 * Édition des référentiels personnels — chaînon manquant de F2.
 *
 * L'audit prescrit d'enrichir les référentiels **au fil des missions réelles**
 * plutôt qu'en amont. La route d'import existait depuis le début côté serveur,
 * mais aucune interface ne l'appelait : le consultant n'avait aucun moyen
 * d'ajouter une exigence sans éditer un YAML à la main.
 *
 * Rappel de F3 : on saisit un identifiant et un intitulé court reformulé,
 * jamais le texte d'une norme sous copyright.
 */
export function ReferentielsPanel({ frameworks, onCharger, onEnregistrer }: Props) {
  const [id, setId] = useState("");
  const [nom, setNom] = useState("");
  const [description, setDescription] = useState("");
  const [exigences, setExigences] = useState<Exigence[]>([]);
  const [personnel, setPersonnel] = useState(true);
  const [nouvelle, setNouvelle] = useState<Exigence>({ id: "", title: "", description: "" });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "erreur"; texte: string } | null>(null);

  const charger = async (fwId: string) => {
    setMessage(null);
    if (!fwId) {
      setId(""); setNom(""); setDescription(""); setExigences([]); setPersonnel(true);
      return;
    }
    try {
      const detail = await onCharger(fwId);
      setId(detail.id ?? fwId);
      setNom(detail.name ?? "");
      setDescription(detail.description ?? "");
      setExigences(detail.requirements ?? []);
      setPersonnel(detail.personnel);
    } catch (e) {
      setMessage({ type: "erreur", texte: e instanceof Error ? e.message : "Chargement impossible." });
    }
  };

  const ajouterExigence = () => {
    if (!nouvelle.id.trim() || !nouvelle.title.trim()) {
      setMessage({ type: "erreur", texte: "Une exigence a besoin d'un identifiant et d'un intitulé." });
      return;
    }
    if (exigences.some((e) => e.id === nouvelle.id.trim())) {
      setMessage({ type: "erreur", texte: `L'exigence « ${nouvelle.id} » existe déjà dans ce référentiel.` });
      return;
    }
    setMessage(null);
    setExigences([...exigences, { ...nouvelle, id: nouvelle.id.trim(), title: nouvelle.title.trim() }]);
    setNouvelle({ id: "", title: "", description: "" });
  };

  const enregistrer = async () => {
    if (!id.trim() || !nom.trim()) {
      setMessage({ type: "erreur", texte: "Un identifiant et un nom sont obligatoires." });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await onEnregistrer({ id: id.trim(), name: nom.trim(), description, requirements: exigences });
      setMessage({ type: "ok", texte: `Référentiel « ${nom} » enregistré (${exigences.length} exigence(s)).` });
    } catch (e) {
      setMessage({ type: "erreur", texte: e instanceof Error ? e.message : "Échec de l'enregistrement." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="glass p-5 flex flex-col gap-3">
      <div className="text-xs font-bold text-[var(--g1)] uppercase tracking-wide flex items-center gap-1.5">
        <BookOpen size={14} /> Référentiels d'audit
      </div>

      <p className="text-[11px] text-[var(--soft)] leading-normal">
        Les référentiels livrés ne couvrent qu'une fraction des exigences réelles. Enrichissez-les
        <strong className="text-[var(--ink)]"> au fil de vos missions</strong> plutôt qu'en amont, en
        créant vos propres référentiels ici.
      </p>

      <div className="flex items-start gap-2 text-[11px] text-[var(--soft)] bg-[rgba(255,207,107,0.06)] border border-[rgba(255,207,107,0.2)] rounded-xl p-2.5">
        <AlertTriangle size={13} className="text-[var(--amber)] shrink-0 mt-0.5" />
        <span>
          Saisissez un identifiant et un <strong className="text-[var(--ink)]">intitulé court reformulé</strong>.
          Le texte des normes ISO est sous copyright ISO/AFNOR : ne le recopiez pas dans l'outil.
        </span>
      </div>

      {/* Inventaire visible : c'est lui qui rend l'incomplétude tangible */}
      <div className="flex flex-wrap gap-1.5">
        {frameworks.map((f) => (
          <span key={f.id} className="text-[10px] bg-white/5 text-[var(--soft)] rounded-full px-2 py-0.5">
            {f.name} · <strong className="text-[var(--ink)]">{f.requirements_count} exigence(s)</strong>
          </span>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-[10px] text-[var(--faint)]">Ouvrir un référentiel existant</span>
          <select
            onChange={(e) => charger(e.target.value)}
            aria-label="Référentiel à ouvrir"
            className="bg-[var(--bg2)] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          >
            <option value="">— Nouveau référentiel personnel —</option>
            {frameworks.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] text-[var(--faint)]">Identifiant (lettres, chiffres, tirets)</span>
          <input
            type="text"
            value={id}
            onChange={(e) => setId(e.target.value)}
            placeholder="ex : secteur_sante"
            aria-label="Identifiant du référentiel"
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] font-mono focus:outline-none focus:border-[var(--g1)]"
          />
        </label>
      </div>

      <input
        type="text"
        value={nom}
        onChange={(e) => setNom(e.target.value)}
        placeholder="Nom du référentiel"
        aria-label="Nom du référentiel"
        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
      />
      <input
        type="text"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Description (optionnel)"
        aria-label="Description du référentiel"
        className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
      />

      {!personnel && (
        <div className="flex items-center gap-2 text-[11px] text-[var(--amber)]">
          <Lock size={12} /> Référentiel livré avec l'application : enregistrer sous cet identifiant sera refusé.
          Changez l'identifiant pour en faire votre version personnelle.
        </div>
      )}

      {/* Exigences */}
      <div className="border-t border-white/[0.04] pt-2.5 flex flex-col gap-2">
        <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">
          Exigences ({exigences.length})
        </span>

        {exigences.length === 0 ? (
          <p className="text-[11px] text-[var(--soft)] italic">Aucune exigence pour l'instant.</p>
        ) : (
          <div className="flex flex-col gap-1 max-h-52 overflow-y-auto pr-1">
            {exigences.map((ex) => (
              <div key={ex.id} className="flex items-start justify-between gap-2 bg-white/[0.02] border border-white/[0.04] rounded-lg px-2.5 py-1.5 text-[11px]">
                <div className="min-w-0">
                  <span className="font-mono text-[var(--sky)] mr-2">{ex.id}</span>
                  <span className="text-[var(--ink)]">{ex.title}</span>
                  {ex.description && <p className="text-[10px] text-[var(--soft)] mt-0.5">{ex.description}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => setExigences(exigences.filter((e) => e.id !== ex.id))}
                  aria-label={`Retirer l'exigence ${ex.id}`}
                  className="text-[var(--rose)] hover:bg-white/5 p-1 rounded shrink-0"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-[auto_1fr_1fr_auto] gap-2">
          <input
            type="text"
            value={nouvelle.id}
            onChange={(e) => setNouvelle({ ...nouvelle, id: e.target.value })}
            placeholder="ID"
            aria-label="Identifiant de l'exigence"
            className="w-28 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] font-mono focus:outline-none focus:border-[var(--g1)]"
          />
          <input
            type="text"
            value={nouvelle.title}
            onChange={(e) => setNouvelle({ ...nouvelle, title: e.target.value })}
            placeholder="Intitulé court (reformulé)"
            aria-label="Intitulé de l'exigence"
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <input
            type="text"
            value={nouvelle.description ?? ""}
            onChange={(e) => setNouvelle({ ...nouvelle, description: e.target.value })}
            placeholder="Précision (optionnel)"
            aria-label="Précision de l'exigence"
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]"
          />
          <button
            type="button"
            onClick={ajouterExigence}
            className="bg-white/[0.06] border border-[var(--stroke)] text-[var(--ink)] font-bold rounded-xl px-3 py-1.5 text-xs hover:bg-white/[0.1] flex items-center gap-1"
          >
            <Plus size={13} /> Ajouter
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={enregistrer}
          disabled={busy}
          className="self-start bg-[var(--g1)] text-[#04150e] font-bold rounded-xl px-3.5 py-1.5 text-xs hover:opacity-90 disabled:opacity-40 flex items-center gap-1.5"
        >
          {busy ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />} Enregistrer le référentiel
        </button>
        {message && (
          <span className={`text-[11px] ${message.type === "ok" ? "text-[var(--g1)]" : "text-[var(--rose)]"}`}>
            {message.texte}
          </span>
        )}
      </div>
    </div>
  );
}
