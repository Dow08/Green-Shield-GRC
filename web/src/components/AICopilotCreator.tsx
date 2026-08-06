import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Send, Bot, Sparkles, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import { obtenirConstructeurReconnaissance, type SpeechRecognitionLike } from "../types/speech";

interface AICopilotCreatorProps {
  onProjectGenerated: (data: { name: string; client: string; type: "grc" | "consulting"; framework_ids?: string[] }) => void;
  onCancel: () => void;
}

export function AICopilotCreator({ onProjectGenerated, onCancel }: AICopilotCreatorProps) {
  const [prompt, setPrompt] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  // La prise en charge de la dictée doit vivre dans un *state* : elle était
  // auparavant lue depuis la ref ci-dessous, assignée dans `useEffect`, ce qui
  // ne provoque aucun rendu — le bouton micro n'apparaissait donc jamais
  // (constaté en recette le 31/07/2026).
  const [dicteeDisponible, setDicteeDisponible] = useState(false);
  const [erreurDictee, setErreurDictee] = useState("");

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    const SpeechRecognitionCtor = obtenirConstructeurReconnaissance();
    if (!SpeechRecognitionCtor) return;

    const reconnaissance = new SpeechRecognitionCtor();
    reconnaissance.continuous = true;
    reconnaissance.interimResults = true;
    reconnaissance.lang = "fr-FR";

    reconnaissance.onresult = (event) => {
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setPrompt((prev) => (prev ? prev + " " : "") + finalTranscript.trim());
      }
    };

    reconnaissance.onerror = (event) => {
      const messages: Record<string, string> = {
        "not-allowed": "Accès au micro refusé. Autorisez-le dans les réglages du navigateur pour dicter.",
        "service-not-allowed": "Le service de dictée du navigateur est indisponible.",
        "no-speech": "Aucune parole détectée — réessayez en parlant plus près du micro.",
        "audio-capture": "Aucun micro détecté sur ce poste.",
      };
      setErreurDictee(messages[event.error] || `Dictée interrompue (${event.error}).`);
      setIsListening(false);
    };

    reconnaissance.onend = () => setIsListening(false);

    recognitionRef.current = reconnaissance;
    setDicteeDisponible(true);

    return () => {
      try { reconnaissance.stop(); } catch { /* déjà arrêtée */ }
    };
  }, []);

  const toggleListening = async () => {
    setErreurDictee("");
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    // Demande explicite du micro : sans elle, le navigateur peut échouer
    // silencieusement et l'utilisateur ne comprend pas pourquoi rien ne se
    // passe. Le flux est relâché aussitôt, la dictée ouvre le sien.
    try {
      const flux = await navigator.mediaDevices.getUserMedia({ audio: true });
      flux.getTracks().forEach((piste) => piste.stop());
    } catch {
      setErreurDictee("Accès au micro refusé. Autorisez-le dans les réglages du navigateur pour dicter.");
      return;
    }
    try {
      recognitionRef.current?.start();
      setIsListening(true);
    } catch {
      setErreurDictee("La dictée n'a pas pu démarrer. Réessayez.");
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    try {
      // 1. Envoyer le prompt au backend (qui va le masquer, l'envoyer à l'IA, le démasquer)
      const aiResponse = await api.projects.copilotGenerate(prompt);
      
      // 2. Transmettre les données générées au parent (Projects.tsx)
      onProjectGenerated({
        name: aiResponse.name,
        client: aiResponse.client,
        type: aiResponse.type as "grc" | "consulting",
        framework_ids: aiResponse.framework_ids || undefined
      });
      
    } catch (error) {
      console.error(error);
      alert("Le pré-remplissage du formulaire a échoué.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full min-h-[400px]">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-[var(--accent)]/10 text-[var(--accent)] rounded-xl">
          <Bot size={24} />
        </div>
        <div>
          <h2 className="text-xl font-bold">Création assistée</h2>
          <p className="text-sm text-[var(--soft)]">
            Décrivez la mission à voix haute ou à l'écrit : le formulaire de création est
            pré-rempli, à vous de le relire et de le compléter.
          </p>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-4 relative">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ex: Je dois faire un audit de conformité ISO 27001 pour la Banque Populaire la semaine prochaine..."
          className="flex-1 w-full p-4 bg-[var(--bg2)] border-2 border-[var(--stroke)] rounded-xl text-[var(--fg)] focus:outline-none focus:border-[var(--accent)] resize-none"
        />
        
        <div className="absolute bottom-4 right-4 flex gap-2">
          {dicteeDisponible && (
            <button
              type="button"
              onClick={toggleListening}
              aria-label={isListening ? "Arrêter la dictée" : "Dicter à voix haute"}
              className={`p-3 rounded-full flex items-center justify-center transition-all shadow-lg ${
                isListening
                  ? "bg-red-500 text-white animate-pulse"
                  : "bg-[var(--bg3)] text-[var(--fg)] hover:bg-[var(--stroke)]"
              }`}
              title={isListening ? "Arrêter la dictée" : "Dicter à voix haute"}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
          )}
        </div>
      </div>

      {erreurDictee && (
        <p className="mt-2 text-xs text-[var(--rose)]">{erreurDictee}</p>
      )}
      {!dicteeDisponible && (
        <p className="mt-2 text-xs text-[var(--faint)]">
          La dictée vocale n'est pas prise en charge par ce navigateur — la saisie au clavier
          reste disponible. (Chrome et Edge la proposent.)
        </p>
      )}

      {/* Ce panneau annonçait « vos données confidentielles sont masquées avant
          envoi » : rien n'est envoyé, et le masquage ne couvre pas les noms de
          clients. Le texte décrit désormais le comportement réel. */}
      <div className="mt-4 flex flex-col gap-2 p-4 bg-[var(--accent)]/5 border border-[var(--accent)]/20 rounded-lg text-sm text-[var(--soft)]">
        <div className="flex items-start gap-2">
          <Sparkles size={16} className="text-[var(--accent)] flex-shrink-0 mt-0.5" />
          <span>
            Le formulaire est pré-rempli <strong>localement</strong>, sans appel à un service
            d'IA : votre description ne quitte pas ce poste.
          </span>
        </div>
        {dicteeDisponible && (
          <div className="flex items-start gap-2">
            <Mic size={16} className="text-[var(--accent)] flex-shrink-0 mt-0.5" />
            <span>
              <strong>Exception :</strong> la dictée s'appuie sur le service de reconnaissance
              vocale du navigateur, qui transmet l'audio à son éditeur. Préférez le clavier pour
              tout élément confidentiel.
            </span>
          </div>
        )}
      </div>

      {/* Footer / Controls */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-[var(--stroke)]">
        <button
          onClick={onCancel}
          className="px-4 py-2 rounded text-sm font-medium text-[var(--soft)] hover:text-[var(--fg)] hover:bg-[var(--bg2)] transition-colors"
        >
          Annuler
        </button>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={!prompt.trim() || isLoading}
          className="flex items-center gap-2 px-6 py-2 rounded bg-[var(--accent)] text-white text-sm font-bold hover:bg-opacity-90 disabled:opacity-50 transition-all"
        >
          {isLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Préparation...
            </>
          ) : (
            <>
              Pré-remplir le formulaire <Send size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
