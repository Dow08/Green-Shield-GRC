import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Mic, MicOff, Send, Bot, Sparkles, Loader2 } from "lucide-react";
import { api } from "../lib/api";

interface AICopilotCreatorProps {
  onProjectGenerated: (data: { name: string; client: string; type: "grc" | "consulting"; framework_ids?: string[] }) => void;
  onCancel: () => void;
}

export function AICopilotCreator({ onProjectGenerated, onCancel }: AICopilotCreatorProps) {
  const [prompt, setPrompt] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // @ts-ignore - webkitSpeechRecognition is not in standard TS DOM lib
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Initialisation de la reconnaissance vocale
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'fr-FR';

      recognitionRef.current.onresult = (event: any) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setPrompt(prev => prev + " " + finalTranscript.trim());
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      setPrompt("");
      recognitionRef.current?.start();
      setIsListening(true);
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
      alert("L'IA n'a pas pu générer le projet.");
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
          <h2 className="text-xl font-bold">Copilote IA GREEN SHIELD</h2>
          <p className="text-sm text-[var(--soft)]">
            Décrivez la mission à voix haute ou à l'écrit, l'IA s'occupe de tout configurer.
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
          {recognitionRef.current && (
            <button
              onClick={toggleListening}
              className={`p-3 rounded-full flex items-center justify-center transition-all shadow-lg ${
                isListening 
                  ? "bg-red-500 text-white animate-pulse" 
                  : "bg-[var(--bg3)] text-[var(--fg)] hover:bg-[var(--stroke)]"
              }`}
              title="Dicter à voix haute"
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between p-4 bg-[var(--accent)]/5 border border-[var(--accent)]/20 rounded-lg text-sm text-[var(--soft)]">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-[var(--accent)]" />
          <span>Vos données confidentielles sont masquées localement avant envoi.</span>
        </div>
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
          onClick={handleGenerate}
          disabled={!prompt.trim() || isLoading}
          className="flex items-center gap-2 px-6 py-2 rounded bg-[var(--accent)] text-white text-sm font-bold hover:bg-opacity-90 disabled:opacity-50 transition-all"
        >
          {isLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Génération...
            </>
          ) : (
            <>
              Générer <Send size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
