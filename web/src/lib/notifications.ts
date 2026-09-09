/**
 * File de notifications non bloquantes — remplaçant de `window.alert()`.
 *
 * Pourquoi un magasin externe (module + `useSyncExternalStore`) plutôt qu'un
 * contexte React monté dans `App.tsx` (09/09/2026) :
 *
 * 1. Un contexte doit envelopper la frontière `<Suspense>` d'`App.tsx`, donc
 *    tout l'arbre applicatif. Chaque notification (y compris celle de la
 *    sauvegarde automatique, toutes les 60 s) ferait alors re-rendre la vue
 *    mission entière et ses six phases. Ici seul l'afficheur s'abonne : le
 *    reste de l'application ne bouge pas.
 * 2. Notifier ne demande plus d'être dans un composant. Les 25 appels
 *    remplacés vivent dans des `.catch()` de gestionnaires d'événements, mais
 *    la même API restera utilisable depuis `lib/api.ts` (ex. expiration de
 *    session) sans hook ni prop.
 * 3. L'afficheur est une feuille, pas un enveloppeur : il est monté à côté
 *    d'`<App/>` dans `main.tsx`, donc jamais imbriqué dans un ancêtre animé
 *    par framer-motion — un `transform` sur un ancêtre redéfinit le bloc
 *    conteneur d'un élément `position: fixed` et casserait le placement.
 *
 * Règle de disparition (exigence métier) : succès et informations s'effacent
 * seuls, une erreur reste jusqu'à fermeture explicite — on ne fait pas
 * disparaître un échec avant que le consultant l'ait lu.
 */

export type NiveauNotification = "succes" | "info" | "erreur";

export interface Notification {
  id: string;
  niveau: NiveauNotification;
  message: string;
  /** Clé de dédoublonnage : une nouvelle notification de même clé remplace la précédente. */
  cle?: string;
}

export interface OptionsNotification {
  cle?: string;
  /** Durée d'affichage en ms. `0` = persistant (défaut des erreurs). */
  dureeMs?: number;
}

/** 2500 ms pour le succès : même durée que la pastille « ✓ Enregistré » de Projects.tsx. */
const DUREES_PAR_DEFAUT: Record<NiveauNotification, number> = {
  succes: 2500,
  info: 5000,
  erreur: 0,
};

/**
 * Au-delà de 4 notifications simultanées la pile masque l'interface. On
 * sacrifie en priorité un succès ou une information (éphémères par nature)
 * plutôt qu'une erreur, qui porte la seule information non reproductible.
 */
const MAX_EMPILEES = 4;

let notifications: Notification[] = [];
let compteur = 0;
const abonnes = new Set<() => void>();
const minuteurs = new Map<string, ReturnType<typeof setTimeout>>();

function publier(suivantes: Notification[]): void {
  notifications = suivantes;
  abonnes.forEach((prevenir) => prevenir());
}

function annulerMinuteur(id: string): void {
  const minuteur = minuteurs.get(id);
  if (minuteur !== undefined) {
    clearTimeout(minuteur);
    minuteurs.delete(id);
  }
}

/** Abonnement pour `useSyncExternalStore`. */
export function sabonnerAuxNotifications(ecouteur: () => void): () => void {
  abonnes.add(ecouteur);
  return () => {
    abonnes.delete(ecouteur);
  };
}

/**
 * Instantané pour `useSyncExternalStore` : la même référence tant que rien ne
 * change, sans quoi React boucherait en re-rendu infini.
 */
export function lireNotifications(): Notification[] {
  return notifications;
}

function fermer(id: string): void {
  annulerMinuteur(id);
  if (!notifications.some((n) => n.id === id)) return;
  publier(notifications.filter((n) => n.id !== id));
}

function fermerParCle(cle: string): void {
  if (!notifications.some((n) => n.cle === cle)) return;
  notifications.filter((n) => n.cle === cle).forEach((n) => annulerMinuteur(n.id));
  publier(notifications.filter((n) => n.cle !== cle));
}

function empiler(niveau: NiveauNotification, message: string, options: OptionsNotification = {}): string {
  compteur += 1;
  const id = `notif-${compteur}`;
  const nouvelle: Notification = { id, niveau, message, cle: options.cle };

  let suivantes = notifications;
  // Dédoublonnage : une panne répétée (sauvegarde automatique toutes les 60 s)
  // rafraîchit sa notification au lieu d'en empiler une nouvelle à chaque tour.
  if (options.cle !== undefined) {
    suivantes.filter((n) => n.cle === options.cle).forEach((n) => annulerMinuteur(n.id));
    suivantes = suivantes.filter((n) => n.cle !== options.cle);
  }
  suivantes = [...suivantes, nouvelle];

  while (suivantes.length > MAX_EMPILEES) {
    const sacrifiee = suivantes.find((n) => n.niveau !== "erreur") ?? suivantes[0];
    annulerMinuteur(sacrifiee.id);
    suivantes = suivantes.filter((n) => n.id !== sacrifiee.id);
  }

  publier(suivantes);

  const dureeMs = options.dureeMs ?? DUREES_PAR_DEFAUT[niveau];
  if (dureeMs > 0) minuteurs.set(id, setTimeout(() => fermer(id), dureeMs));
  return id;
}

export const notifier = {
  succes: (message: string, options?: OptionsNotification) => empiler("succes", message, options),
  info: (message: string, options?: OptionsNotification) => empiler("info", message, options),
  erreur: (message: string, options?: OptionsNotification) => empiler("erreur", message, options),
  fermer,
  fermerParCle,
  /** Remise à zéro entre deux tests — le magasin est un singleton de module. */
  reinitialiser: () => {
    minuteurs.forEach((minuteur) => clearTimeout(minuteur));
    minuteurs.clear();
    compteur = 0;
    publier([]);
  },
};

/**
 * `.catch((err) => ...)` reçoit un `unknown` : un rejet peut ne pas être une
 * `Error` (chaîne, réponse API). Lire `err.message` à l'aveugle affichait
 * alors « undefined » à la place du motif réel.
 */
export function messageErreur(err: unknown, repli: string): string {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === "string" && err) return err;
  return repli;
}
