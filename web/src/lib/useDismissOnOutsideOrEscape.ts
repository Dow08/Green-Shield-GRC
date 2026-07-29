import { useEffect, useRef } from "react";

/**
 * Ferme un menu/dropdown au clic extérieur ou à la touche Échap — comportement
 * attendu de tout overlay (cf. CLAUDE.md, section Conventions frontend).
 * Retourne un ref à poser sur le conteneur du menu (bouton déclencheur inclus).
 */
export function useDismissOnOutsideOrEscape<T extends HTMLElement>(
  isOpen: boolean,
  onDismiss: () => void
) {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (!isOpen) return;

    function handlePointerDown(event: PointerEvent) {
      if (ref.current && event.target instanceof Node && !ref.current.contains(event.target)) {
        onDismiss();
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onDismiss();
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onDismiss]);

  return ref;
}
