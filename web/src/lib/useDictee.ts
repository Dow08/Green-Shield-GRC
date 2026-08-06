import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Dictée vocale réutilisable, adossée à l'API de reconnaissance du navigateur.
 *
 * ⚠️ CETTE FONCTION N'EST PAS HORS-LIGNE. L'API `SpeechRecognition` des
 * navigateurs Chromium transmet l'audio aux serveurs de l'éditeur pour
 * transcription. C'est la seule fonctionnalité de GREEN SHIELD qui sorte des
 * données sans clé d'API saisie par le consultant, d'où :
 *
 *   * l'activation explicite dans les Réglages, désactivée par défaut ;
 *   * l'absence de micro sur les champs porteurs de données client
 *     (cf. `champsSansDictee` dans `dictee.ts`).
 *
 * Extrait de `AICopilotCreator` le 05/08/2026 pour être posé sur les champs
 * texte des six phases. Testé avant branchement (règle n°2 du projet).
 */

export interface EtatDictee {
  /** Le navigateur expose-t-il la reconnaissance vocale ? */
  disponible: boolean;
  /** Une dictée est-elle en cours ? */
  ecoute: boolean;
  /** Message destiné à l'utilisateur, vide si tout va bien. */
  erreur: string;
  /** Démarre ou arrête la dictée. */
  basculer: () => void;
}

const MESSAGES_ERREUR: Record<string, string> = {
  "not-allowed": "Accès au micro refusé. Autorisez-le dans les réglages du navigateur pour dicter.",
  "service-not-allowed": "Le service de dictée du navigateur est indisponible.",
  "no-speech": "Aucune parole détectée — réessayez en parlant plus près du micro.",
  "audio-capture": "Aucun micro détecté sur ce poste.",
  network: "La dictée nécessite une connexion : le navigateur transcrit l'audio en ligne.",
};

/**
 * @param onTexte Appelé à chaque segment transcrit définitif. Reçoit le texte
 *   seul : c'est à l'appelant de décider s'il l'ajoute ou remplace le champ.
 * @param actif Permet de neutraliser la dictée sans démonter le composant
 *   (réglage désactivé, champ sensible).
 */
export function useDictee(onTexte: (texte: string) => void, actif = true): EtatDictee {
  const [disponible, setDisponible] = useState(false);
  const [ecoute, setEcoute] = useState(false);
  const [erreur, setErreur] = useState("");
  const reconnaissanceRef = useRef<any>(null);

  // Le callback change à chaque rendu du parent ; le garder dans une ref évite
  // de reconstruire l'objet de reconnaissance (ce qui couperait une dictée en
  // cours à chaque frappe au clavier).
  const onTexteRef = useRef(onTexte);
  useEffect(() => {
    onTexteRef.current = onTexte;
  }, [onTexte]);

  useEffect(() => {
    if (!actif) return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const reconnaissance = new SpeechRecognition();
    reconnaissance.continuous = true;
    reconnaissance.interimResults = true;
    reconnaissance.lang = "fr-FR";

    reconnaissance.onresult = (evenement: any) => {
      let definitif = "";
      for (let i = evenement.resultIndex; i < evenement.results.length; ++i) {
        if (evenement.results[i].isFinal) definitif += evenement.results[i][0].transcript;
      }
      if (definitif.trim()) onTexteRef.current(definitif.trim());
    };

    reconnaissance.onerror = (evenement: any) => {
      setErreur(MESSAGES_ERREUR[evenement.error] || `Dictée interrompue (${evenement.error}).`);
      setEcoute(false);
    };

    reconnaissance.onend = () => setEcoute(false);

    reconnaissanceRef.current = reconnaissance;
    setDisponible(true);

    return () => {
      try {
        reconnaissance.stop();
      } catch {
        /* déjà arrêtée */
      }
      reconnaissanceRef.current = null;
      setDisponible(false);
    };
  }, [actif]);

  const basculer = useCallback(async () => {
    setErreur("");
    if (ecoute) {
      reconnaissanceRef.current?.stop();
      setEcoute(false);
      return;
    }
    // Demande explicite du micro : sans elle, le navigateur peut échouer en
    // silence et l'utilisateur ne comprend pas pourquoi rien ne se passe. Le
    // flux est relâché aussitôt, la reconnaissance ouvre le sien.
    try {
      const flux = await navigator.mediaDevices.getUserMedia({ audio: true });
      flux.getTracks().forEach((piste) => piste.stop());
    } catch {
      setErreur("Accès au micro refusé. Autorisez-le dans les réglages du navigateur pour dicter.");
      return;
    }
    try {
      reconnaissanceRef.current?.start();
      setEcoute(true);
    } catch {
      setErreur("La dictée n'a pas pu démarrer. Réessayez.");
    }
  }, [ecoute]);

  return { disponible, ecoute, erreur, basculer };
}
