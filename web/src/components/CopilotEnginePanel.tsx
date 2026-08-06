import { useState } from "react";
import { Cpu, Key, Loader2, Gauge, CheckCircle2, AlertTriangle, Wifi, WifiOff } from "lucide-react";
import { api } from "../lib/api";
import type { FournisseurLLM, MaterielInfo, MesureModele } from "../types";

interface Props {
  fournisseur: FournisseurLLM | "";
  onFournisseurChange: (f: FournisseurLLM | "") => void;
  modele: string;
  onModeleChange: (m: string) => void;
  apiKey: string;
  onApiKeyChange: (k: string) => void;
}

/**
 * Choix du moteur du Copilote : modèle local ou fournisseur en ligne.
 *
 * Le panneau assume une contrainte du produit : l'utilisateur est consultant
 * GRC, pas administrateur système. Il ne doit pas avoir à deviner quel modèle
 * son ordinateur supporte — d'où la détection matérielle et le chronométrage
 * réel, qui remplacent une recommandation théorique invérifiable.
 */

// Chaque fournisseur annonce sa propre réalité réseau. La mention est
// délibérément explicite : c'est la question que se pose un consultant avant
// de faire passer un constat d'audit dans un modèle.
const FOURNISSEURS: {
  id: FournisseurLLM;
  nom: string;
  local: boolean;
  reseau: string;
  aide: string;
  exempleModele: string;
}[] = [
  {
    id: "ollama",
    nom: "Modèle local (Ollama)",
    local: true,
    reseau: "Aucune sortie réseau. Tout reste sur ce poste.",
    aide: "Nécessite Ollama installé et lancé sur cette machine.",
    exempleModele: "mistral",
  },
  {
    id: "gemini",
    nom: "Google Gemini",
    local: false,
    reseau: "Votre question et le contexte de mission sont envoyés à Google.",
    aide: "Clé disponible sur aistudio.google.com",
    exempleModele: "gemini-2.0-flash",
  },
  {
    id: "anthropic",
    nom: "Anthropic Claude",
    local: false,
    reseau: "Votre question et le contexte de mission sont envoyés à Anthropic.",
    aide: "Clé disponible sur console.anthropic.com",
    exempleModele: "claude-opus-5",
  },
  {
    id: "openai",
    nom: "OpenAI ChatGPT",
    local: false,
    reseau: "Votre question et le contexte de mission sont envoyés à OpenAI.",
    aide: "Clé disponible sur platform.openai.com",
    exempleModele: "gpt-4o",
  },
  {
    id: "kimi",
    nom: "Moonshot Kimi",
    local: false,
    reseau: "Votre question et le contexte de mission sont envoyés à Moonshot (Chine).",
    aide: "Clé disponible sur platform.moonshot.cn",
    exempleModele: "moonshot-v1-8k",
  },
];

export function CopilotEnginePanel({
  fournisseur,
  onFournisseurChange,
  modele,
  onModeleChange,
  apiKey,
  onApiKeyChange,
}: Props) {
  const [materiel, setMateriel] = useState<MaterielInfo | null>(null);
  const [detection, setDetection] = useState(false);
  const [mesure, setMesure] = useState<MesureModele | null>(null);
  const [test, setTest] = useState(false);
  const [erreur, setErreur] = useState("");

  const choisi = FOURNISSEURS.find((f) => f.id === fournisseur);
  const estLocal = choisi?.local ?? false;

  const detecter = async () => {
    setDetection(true);
    setErreur("");
    setMesure(null);
    try {
      const info = await api.copilot.materiel();
      setMateriel(info);
      // On pré-remplit le modèle recommandé plutôt que de le laisser deviner,
      // mais sans écraser un choix déjà fait par le consultant.
      if (info.modele_recommande && !modele) onModeleChange(info.modele_recommande);
    } catch {
      setErreur("Détection impossible. L'application est-elle bien démarrée ?");
    } finally {
      setDetection(false);
    }
  };

  const tester = async () => {
    if (!modele) return;
    setTest(true);
    setErreur("");
    setMesure(null);
    try {
      setMesure(await api.copilot.testerModele(modele));
    } catch {
      setErreur("Le test a échoué. Vérifiez qu'Ollama est lancé.");
    } finally {
      setTest(false);
    }
  };

  return (
    <div className="glass p-5 flex flex-col gap-4">
      <div className="text-xs font-bold text-[var(--g3)] uppercase tracking-wide flex items-center gap-1.5">
        <Cpu size={14} /> Moteur du Copilote
      </div>

      <p className="text-[11px] text-[var(--soft)] leading-normal">
        Sans moteur configuré, le Copilote répond hors-ligne à partir des données réelles de vos
        missions. Un moteur ajoute la reformulation en langage naturel.
      </p>

      <div>
        <label
          htmlFor="moteur-fournisseur"
          className="block text-[11px] font-bold text-[var(--soft)] mb-1"
        >
          Fournisseur
        </label>
        <select
          id="moteur-fournisseur"
          value={fournisseur}
          onChange={(e) => {
            const suivant = e.target.value as FournisseurLLM | "";
            onFournisseurChange(suivant);
            onModeleChange("");
            setMesure(null);
          }}
          className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g3)]"
        >
          <option value="">Aucun — hors-ligne uniquement</option>
          {FOURNISSEURS.map((f) => (
            <option key={f.id} value={f.id}>
              {f.nom}
            </option>
          ))}
        </select>
      </div>

      {choisi && (
        <div
          className={`flex items-start gap-2 rounded-xl p-3 text-[11px] leading-relaxed border ${
            choisi.local
              ? "border-[rgba(46,230,160,0.25)] bg-[rgba(46,230,160,0.06)] text-[var(--g1)]"
              : "border-amber-500/25 bg-amber-500/[0.06] text-amber-500"
          }`}
        >
          {choisi.local ? (
            <WifiOff size={14} className="flex-shrink-0 mt-0.5" />
          ) : (
            <Wifi size={14} className="flex-shrink-0 mt-0.5" />
          )}
          <span>{choisi.reseau}</span>
        </div>
      )}

      {estLocal && (
        <div className="flex flex-col gap-3 border-t border-[var(--stroke)] pt-4">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={detecter}
              disabled={detection}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--stroke)] bg-white/[0.04] px-3 py-2 text-[11px] font-bold text-[var(--ink)] transition hover:bg-white/10 disabled:opacity-50"
            >
              {detection ? <Loader2 size={13} className="animate-spin" /> : <Cpu size={13} />}
              {detection ? "Analyse…" : "Analyser mon ordinateur"}
            </button>
            {modele && (
              <button
                type="button"
                onClick={tester}
                disabled={test}
                className="flex items-center gap-1.5 rounded-xl border border-[var(--stroke)] bg-white/[0.04] px-3 py-2 text-[11px] font-bold text-[var(--ink)] transition hover:bg-white/10 disabled:opacity-50"
              >
                {test ? <Loader2 size={13} className="animate-spin" /> : <Gauge size={13} />}
                {test ? "Test en cours…" : "Tester la vitesse"}
              </button>
            )}
          </div>

          {test && (
            // Le premier appel charge le modèle en mémoire : mesuré à 113 s
            // sur un poste équipé d'une RTX 4080, contre 8 s ensuite. Sans cet
            // avertissement, l'utilisateur croit l'application figée.
            <p className="text-[10.5px] text-[var(--faint)] leading-relaxed">
              Le premier test peut prendre plusieurs minutes : le modèle doit être chargé en
              mémoire. Les réponses suivantes sont bien plus rapides.
            </p>
          )}

          {materiel && (
            <div className="rounded-xl border border-[var(--stroke)] bg-white/[0.02] p-3 text-[11px] leading-relaxed">
              <div className="text-[var(--soft)]">
                {materiel.systeme}
                {materiel.ram_go !== null && ` · ${materiel.ram_go} Go de mémoire`}
                {materiel.coeurs !== null && ` · ${materiel.coeurs} cœurs`}
                {materiel.gpu && ` · ${materiel.gpu.nom} (${materiel.gpu.vram_go} Go)`}
              </div>
              <div className="mt-2 text-[var(--ink)]">{materiel.conseil}</div>
              {materiel.estimation && materiel.modele_recommande && (
                <div className="mt-1.5 text-[10.5px] text-[var(--faint)]">
                  Estimation d'après la mémoire disponible. Lancez « Tester la vitesse » pour la
                  mesure réelle.
                </div>
              )}
            </div>
          )}

          <div>
            <label
              htmlFor="moteur-modele-local"
              className="block text-[11px] font-bold text-[var(--soft)] mb-1"
            >
              Modèle
            </label>
            {materiel && materiel.modeles_installes.length > 0 ? (
              <select
                id="moteur-modele-local"
                value={modele}
                onChange={(e) => {
                  onModeleChange(e.target.value);
                  setMesure(null);
                }}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g3)]"
              >
                <option value="">Choisir un modèle installé…</option>
                {materiel.modeles_installes.map((m) => (
                  <option key={m.nom} value={m.nom}>
                    {m.nom} ({m.taille_go} Go)
                    {m.nom === materiel.modele_recommande ? " — recommandé" : ""}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id="moteur-modele-local"
                type="text"
                placeholder={choisi?.exempleModele}
                value={modele}
                onChange={(e) => onModeleChange(e.target.value)}
                className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--g3)]"
              />
            )}
          </div>

          {mesure && (
            <div
              className={`flex items-start gap-2 rounded-xl border p-3 text-[11px] leading-relaxed ${
                mesure.ok
                  ? "border-[rgba(46,230,160,0.25)] bg-[rgba(46,230,160,0.06)]"
                  : "border-[var(--rose)]/30 bg-[var(--rose)]/[0.06]"
              }`}
            >
              {mesure.ok ? (
                <CheckCircle2 size={14} className="mt-0.5 flex-shrink-0 text-[var(--g1)]" />
              ) : (
                <AlertTriangle size={14} className="mt-0.5 flex-shrink-0 text-[var(--rose)]" />
              )}
              <div>
                <div className="font-bold text-[var(--ink)]">{mesure.verdict}</div>
                {mesure.extrait && (
                  <div className="mt-1.5 italic text-[var(--soft)]">« {mesure.extrait} »</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {choisi && !estLocal && (
        <div className="flex flex-col gap-3 border-t border-[var(--stroke)] pt-4">
          <div>
            <label
              htmlFor="moteur-cle"
              className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--soft)] mb-1"
            >
              <Key size={12} /> Clé d'API
            </label>
            <input
              id="moteur-cle"
              type="password"
              placeholder="Votre clé"
              value={apiKey}
              onChange={(e) => onApiKeyChange(e.target.value)}
              className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--g3)]"
            />
            <p className="mt-1 text-[10.5px] text-[var(--faint)]">{choisi.aide}</p>
          </div>
          <div>
            <label
              htmlFor="moteur-modele"
              className="block text-[11px] font-bold text-[var(--soft)] mb-1"
            >
              Modèle
            </label>
            <input
              id="moteur-modele"
              type="text"
              placeholder={choisi.exempleModele}
              value={modele}
              onChange={(e) => onModeleChange(e.target.value)}
              className="w-full bg-white/[0.04] border border-[var(--stroke)] rounded-xl px-3 py-2 text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--g3)]"
            />
            <p className="mt-1 text-[10.5px] text-[var(--faint)]">
              Laisser vide pour utiliser {choisi.exempleModele}.
            </p>
          </div>
        </div>
      )}

      {erreur && <p className="text-[11px] font-bold text-[var(--rose)]">{erreur}</p>}
    </div>
  );
}
