import { useEffect, useRef, useSyncExternalStore } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Info, AlertTriangle, X } from "lucide-react";
import {
  lireNotifications,
  notifier,
  sabonnerAuxNotifications,
  type NiveauNotification,
} from "../lib/notifications";

/**
 * Afficheur unique de la file de notifications (09/09/2026).
 *
 * Remplace `window.alert()`, qui gelait la page entière, sortait de la charte
 * (fenêtre système titrée `localhost:5175`) et ne laissait aucune trace après
 * le clic sur « OK ».
 *
 * Accessibilité : `alert()` était annoncé nativement, il ne faut pas régresser.
 * Chaque notification porte donc son propre rôle live — `alert` (assertif) pour
 * une erreur, `status` (poli) pour un succès ou une information — et son bouton
 * de fermeture porte un intitulé accessible reprenant le message, pour rester
 * distinguable quand plusieurs notifications sont empilées.
 *
 * Le style reprend la pastille « ✓ Enregistré » de Projects.tsx (bordure et
 * fond translucides teintés de la couleur du niveau) et les variables CSS du
 * projet, jamais une couleur en dur hors de ces variables.
 */

const STYLES: Record<NiveauNotification, { classe: string; libelle: string }> = {
  succes: {
    classe: "border-[rgba(46,230,160,0.35)] bg-[rgba(46,230,160,0.12)] text-[var(--g1)]",
    libelle: "Succès",
  },
  info: {
    classe: "border-[rgba(92,200,255,0.35)] bg-[rgba(92,200,255,0.12)] text-[var(--sky)]",
    libelle: "Information",
  },
  erreur: {
    classe: "border-[rgba(255,111,145,0.35)] bg-[rgba(255,111,145,0.12)] text-[var(--rose)]",
    libelle: "Erreur",
  },
};

function Icone({ niveau }: { niveau: NiveauNotification }) {
  if (niveau === "succes") return <Check size={14} aria-hidden="true" />;
  if (niveau === "info") return <Info size={14} aria-hidden="true" />;
  return <AlertTriangle size={14} aria-hidden="true" />;
}

export function Notifications() {
  const notifications = useSyncExternalStore(sabonnerAuxNotifications, lireNotifications);
  // Élément qui avait le focus avant la fermeture. Sans lui, `document.
  // activeElement` retombe sur `<body>` : au clavier, on repart du haut de la
  // page alors qu'on travaillait dans un formulaire de mission (constaté à
  // l'audit du 09/09/2026).
  const focusAvantFermeture = useRef<HTMLElement | null>(null);

  const fermer = (id: string) => {
    const precedent = focusAvantFermeture.current;
    notifier.fermer(id);
    // Le bouton fermé disparaît du DOM : on rend la main à l'élément d'où
    // l'utilisateur venait, s'il est toujours là.
    if (precedent?.isConnected) precedent.focus();
    focusAvantFermeture.current = null;
  };

  // Échap ferme la plus récente. L'afficheur étant monté après `<App/>`, son
  // bouton arrive en toute fin d'ordre de tabulation : sans ce raccourci, se
  // débarrasser d'une erreur persistante coûte de traverser tout l'arbre.
  useEffect(() => {
    if (notifications.length === 0) return;
    const surTouche = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      const derniere = notifications[notifications.length - 1];
      if (derniere) notifier.fermer(derniere.id);
    };
    window.addEventListener("keydown", surTouche);
    return () => window.removeEventListener("keydown", surTouche);
  }, [notifications]);

  return (
    // `pointer-events-none` sur la pile, réactivé sur chaque carte : hors des
    // cartes, la zone ne doit rien intercepter — l'inverse d'`alert()`, qui
    // condamnait toute l'interface tant qu'on n'avait pas cliqué « OK ».
    <div className="pointer-events-none fixed bottom-4 right-4 z-[200] flex w-[min(26rem,calc(100vw-2rem))] flex-col items-stretch gap-2">
      <AnimatePresence initial={false}>
        {notifications.map((n) => (
          <motion.div
            key={n.id}
            layout
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.18 }}
            role={n.niveau === "erreur" ? "alert" : "status"}
            className={`pointer-events-auto flex items-start gap-2 rounded-2xl border px-3 py-2.5 text-xs font-bold shadow-[0_12px_32px_rgba(0,0,0,0.45)] backdrop-blur-md ${STYLES[n.niveau].classe}`}
          >
            <span className="mt-0.5 shrink-0">
              <Icone niveau={n.niveau} />
            </span>
            <span id={`notif-${n.id}`} className="min-w-0 flex-1 break-words whitespace-pre-wrap">
              <span className="sr-only">{STYLES[n.niveau].libelle} : </span>
              {n.message}
            </span>
            <button
              type="button"
              onClick={() => fermer(n.id)}
              onFocus={(e) => { focusAvantFermeture.current = e.relatedTarget as HTMLElement | null; }}
              // Intitulé court + `aria-describedby` plutôt que le message
              // recopié dans l'`aria-label` : `role="alert"` étant `aria-atomic`
              // par défaut, le lecteur d'écran annonçait le message, puis le
              // relisait entièrement en atteignant le bouton (audit 09/09/2026).
              // Le lien conserve la distinction entre notifications empilées.
              aria-label="Fermer"
              aria-describedby={`notif-${n.id}`}
              className="shrink-0 rounded-full p-0.5 opacity-70 transition hover:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-current"
            >
              <X size={14} aria-hidden="true" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
