// Web Speech API — non standardisée (absente de lib.dom.d.ts), préfixée
// `webkit` sur Chromium. Typage minimal pour ce que useDictee/AICopilotCreator
// consomment réellement, plutôt que `any`.

export interface SpeechRecognitionResultLike {
  isFinal: boolean;
  [index: number]: { transcript: string };
}

export interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: { length: number; [index: number]: SpeechRecognitionResultLike };
}

export interface SpeechRecognitionErrorEventLike {
  error: string;
}

export interface SpeechRecognitionLike {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

/** Le constructeur, sous son nom standard ou préfixé webkit — absent si le
 *  navigateur ne supporte pas la reconnaissance vocale. */
export function obtenirConstructeurReconnaissance(): SpeechRecognitionConstructor | undefined {
  const global = window as unknown as {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };
  return global.SpeechRecognition || global.webkitSpeechRecognition;
}
