import { useState } from "react";
import { FileText, Plus, Trash2, Search, Link as LinkIcon } from "lucide-react";
import { nextId } from "../lib/ids";
import type { LienControle, ManualControl, Preuve } from "../types";
import { api } from "../lib/api";

interface Props {
  projectId?: string;
  preuves: Preuve[];
  manualControls: ManualControl[];
  onChange: (preuves: Preuve[]) => void;
}

const NOUVELLE: Omit<Preuve, "id"> = {
  libelle: "", description: "", document_reference: "", date: "", controles_lies: [],
};

function lienEgal(a: LienControle, b: LienControle): boolean {
  return a.referentiel_id === b.referentiel_id && a.control_id === b.control_id;
}

/**
 * Bibliothèque de preuves multi-référentiels (G3bis, 31/07/2026).
 *
 * Une preuve écrite une fois (ex. une politique de sécurité) sert souvent
 * plusieurs référentiels actifs d'une même mission — jusqu'ici chaque
 * contrôle ne portait qu'un champ `notes` libre, sans lien vers les autres.
 * Aucun catalogue figé ici (contrairement à la SoA) : les preuves sont
 * saisies par le consultant au fil de la mission, jamais préchargées.
 */
export function PreuveLibraryPanel({ projectId, preuves, manualControls, onChange }: Props) {
  const [nouvelle, setNouvelle] = useState<Omit<Preuve, "id">>(NOUVELLE);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const fetchSuggestions = async () => {
    if (!projectId) return;
    setLoadingSuggestions(true);
    try {
      const res = await api.projects.getSuggestions(projectId);
      setSuggestions(res || []);
    } catch (err) {
      console.error("Erreur suggestions", err);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const applySuggestion = (sug: any) => {
    const list = [...preuves];
    const preuveIdx = list.findIndex(p => p.id === sug.preuve_id);
    if (preuveIdx !== -1) {
       const lien: LienControle = { referentiel_id: sug.controle_suggere.referentiel_id, control_id: sug.controle_suggere.control_id };
       if (!list[preuveIdx].controles_lies.some(l => lienEgal(l, lien))) {
           list[preuveIdx].controles_lies.push(lien);
           onChange(list);
       }
    }
    setSuggestions(suggestions.filter(s => s !== sug));
  };

  const controlesCouverts = new Set(
    preuves.flatMap((p) => p.controles_lies.map((l) => `${l.referentiel_id}::${l.control_id}`))
  );
  const total = manualControls.length;
  const couverts = manualControls.filter((c) =>
    controlesCouverts.has(`${c.referentiel_id ?? ""}::${c.id}`)
  ).length;
  const taux = total ? Math.round((couverts / total) * 100) : 0;

  // Groupé par référentiel, comme la check-list elle-même (Lot D) — le
  // consultant choisit les contrôles couverts dans le même repère visuel.
  const referentiels = Array.from(new Set(manualControls.map((c) => c.referentiel_id).filter(Boolean))) as string[];

  const toggleLien = (lien: LienControle) => {
    const deja = nouvelle.controles_lies.some((l) => lienEgal(l, lien));
    setNouvelle({
      ...nouvelle,
      controles_lies: deja
        ? nouvelle.controles_lies.filter((l) => !lienEgal(l, lien))
        : [...nouvelle.controles_lies, lien],
    });
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="text-xs font-bold text-[var(--sky)] flex items-center gap-1.5">
          <FileText size={14} /> Bibliothèque de preuves
        </div>
        <div className="flex items-center gap-3">
          {projectId && referentiels.length > 1 && preuves.length > 0 && (
            <button
              onClick={fetchSuggestions}
              disabled={loadingSuggestions}
              className="text-[10px] font-bold bg-[var(--accent)]/10 text-[var(--accent)] px-2 py-1 rounded hover:bg-[var(--accent)]/20 transition-colors flex items-center gap-1"
            >
              <Search size={12} /> {loadingSuggestions ? "Recherche..." : "Vérifier les référentiels"}
            </button>
          )}
          {total > 0 && (
            <div className="text-[10px] text-[var(--soft)]">
              <strong className="text-[var(--ink)]">{couverts}/{total}</strong> contrôle(s) couvert(s) par au moins une preuve ({taux} %)
            </div>
          )}
        </div>
      </div>
      
      {suggestions.length > 0 && (
        <div className="bg-[var(--sky)]/10 border border-[var(--sky)]/20 rounded-xl p-3 flex flex-col gap-2 mb-2 animate-fade-in">
          <div className="text-[10px] font-bold text-[var(--sky)] uppercase tracking-wide">Suggestions de réutilisation</div>
          <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto pr-1">
            {suggestions.map((sug, idx) => (
              <div key={idx} className="bg-white/5 p-2 rounded-lg text-[10px] flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-[var(--soft)] truncate">Lier la preuve <strong className="text-[var(--ink)]">{sug.preuve_libelle}</strong> au contrôle :</div>
                  <div className="text-[var(--ink)] font-bold truncate mt-0.5">{sug.controle_suggere.referentiel_name} · {sug.controle_suggere.control_id} : {sug.controle_suggere.title}</div>
                  <div className="text-[8px] text-[var(--sky)] font-mono mt-0.5">Confiance : {sug.confiance}%</div>
                </div>
                <button
                  onClick={() => applySuggestion(sug)}
                  className="shrink-0 bg-[var(--sky)] text-white px-2 py-1 rounded flex items-center gap-1 hover:opacity-90 font-bold"
                >
                  <LinkIcon size={12} /> Lier
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-[10px] text-[var(--faint)] -mt-1.5 leading-normal">
        Une même preuve (politique, contrat, capture d'écran référencée) peut couvrir plusieurs contrôles,
        y compris de référentiels différents — inutile de la ressaisir pour chacun.
      </p>

      <div className="flex flex-col gap-2">
        {preuves.map((p, idx) => (
          <div key={p.id} className="bg-white/[0.02] p-2.5 rounded-xl border border-white/[0.05] text-xs flex flex-col gap-1.5">
            <div className="flex justify-between items-start gap-2">
              <div>
                <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--sky)] mr-2">{p.id}</span>
                <span className="font-bold text-[var(--ink)]">{p.libelle || "Preuve sans intitulé"}</span>
                {p.document_reference && (
                  <p className="text-[10px] text-[var(--soft)] mt-0.5">Réf. document : {p.document_reference}</p>
                )}
                {p.description && <p className="text-[10px] text-[var(--faint)] mt-0.5">{p.description}</p>}
              </div>
              <button
                type="button"
                onClick={() => { const list = [...preuves]; list.splice(idx, 1); onChange(list); }}
                className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg flex-shrink-0"
                aria-label={`Supprimer la preuve ${p.id}`}
              >
                <Trash2 size={13} />
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {p.controles_lies.length === 0 && (
                <span className="text-[9px] text-[var(--amber)] font-bold">Aucun contrôle lié</span>
              )}
              {p.controles_lies.map((l) => (
                <span key={`${l.referentiel_id}-${l.control_id}`} className="text-[9px] font-mono bg-white/5 px-1.5 py-0.5 rounded text-[var(--soft)]">
                  {l.referentiel_id} · {l.control_id}
                </span>
              ))}
            </div>
          </div>
        ))}
        {preuves.length === 0 && (
          <p className="text-[10px] text-[var(--soft)] italic">Aucune preuve saisie sur cette mission.</p>
        )}
      </div>

      <div className="flex flex-col gap-2 bg-white/[0.01] border border-dashed border-[var(--stroke)] p-3 rounded-xl text-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <input
            type="text" placeholder="Intitulé de la preuve (ex : PSSI signée)" value={nouvelle.libelle}
            onChange={(e) => setNouvelle({ ...nouvelle, libelle: e.target.value })}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
          <input
            type="text" placeholder="Référence du document" value={nouvelle.document_reference}
            onChange={(e) => setNouvelle({ ...nouvelle, document_reference: e.target.value })}
            className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
          />
        </div>
        <input
          type="text" placeholder="Description (optionnel)" value={nouvelle.description}
          onChange={(e) => setNouvelle({ ...nouvelle, description: e.target.value })}
          className="bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none"
        />
        <div>
          <label className="block text-[9px] font-bold text-[var(--faint)] mb-0.5">Date</label>
          <input
            type="date" value={nouvelle.date}
            onChange={(e) => setNouvelle({ ...nouvelle, date: e.target.value })}
            className="w-40 bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 focus:outline-none text-[var(--ink)]"
          />
        </div>

        {referentiels.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <span className="text-[9px] font-bold text-[var(--faint)]">Contrôles couverts par cette preuve</span>
            {referentiels.map((refId) => {
              const controles = manualControls.filter((c) => c.referentiel_id === refId);
              const nom = controles[0]?.referentiel_name || refId;
              return (
                <div key={refId} className="flex flex-col gap-1">
                  <span className="text-[9px] text-[var(--sky)] font-bold">{nom}</span>
                  <div className="flex flex-wrap gap-1.5">
                    {controles.map((c) => {
                      const lien: LienControle = { referentiel_id: refId, control_id: c.id };
                      const coche = nouvelle.controles_lies.some((l) => lienEgal(l, lien));
                      return (
                        <label key={c.id} className={`flex items-center gap-1 px-1.5 py-0.5 rounded-lg border cursor-pointer text-[9px] ${coche ? "bg-[rgba(46,230,160,0.12)] border-[var(--g1)]/40 text-[var(--g1)]" : "bg-white/[0.02] border-white/5 text-[var(--soft)]"}`}>
                          <input
                            type="checkbox" checked={coche} onChange={() => toggleLien(lien)}
                            className="rounded border-[var(--stroke)] bg-transparent text-[var(--g1)] focus:ring-0"
                          />
                          {c.id}
                        </label>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <button
          type="button"
          onClick={() => {
            if (!nouvelle.libelle.trim()) return;
            const id = nextId("PRV", preuves.map((p) => p.id));
            onChange([...preuves, { ...nouvelle, id }]);
            setNouvelle(NOUVELLE);
          }}
          className="self-end flex items-center gap-1.5 bg-[var(--g1)] text-[#04150e] px-3 py-1.5 rounded-xl hover:opacity-90 font-bold"
        >
          <Plus size={14} /> Ajouter la preuve
        </button>
      </div>
    </div>
  );
}
