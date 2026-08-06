import { safeGetItem } from "./storage";

/**
 * Politique de dictée vocale — quels champs peuvent l'utiliser, et pourquoi pas
 * les autres.
 *
 * La dictée transmet l'audio à l'éditeur du navigateur (Google sur Chrome).
 * Un consultant qui dicte « le serveur de paie de la clinique Saint-Roch
 * expose un compte admin sans mot de passe » vient d'envoyer à un tiers le nom
 * du client et une vulnérabilité exploitable.
 *
 * Deux garde-fous, cumulatifs :
 *
 *   1. Interrupteur général, désactivé par défaut, dans les Réglages.
 *   2. Cette liste : même interrupteur activé, ces natures de champ n'affichent
 *      jamais de micro.
 *
 * La liste est nominative et commentée plutôt que dispersée en `showMic={false}`
 * dans les composants : un consultant doit pouvoir vérifier en un coup d'œil ce
 * que l'outil s'interdit d'envoyer.
 */

/** Natures de champ interdites à la dictée, avec la raison de l'exclusion. */
export const CHAMPS_SANS_DICTEE: Record<string, string> = {
  client: "Nom du client — identifie directement la mission et l'organisation auditée.",
  entretien:
    "Comptes rendus d'entretien — contiennent des noms de personnes et leurs propos (données personnelles, RGPD).",
  constat:
    "Constats d'audit et notes de contrôle — décrivent des vulnérabilités exploitables chez le client.",
  preuve: "Références de preuve — pointent vers des documents internes du client.",
  violation:
    "Registre des violations — incidents de sécurité réels et données personnelles concernées.",
  scope: "Périmètre de mission — décrit l'infrastructure du client.",
};

export type NatureChamp = keyof typeof CHAMPS_SANS_DICTEE;

const CLE_REGLAGE = "dictee_activee";

/** La dictée est-elle autorisée globalement ? Désactivée tant que le consultant
 *  ne l'a pas activée en connaissance de cause. */
export function dicteeActivee(): boolean {
  return safeGetItem(CLE_REGLAGE) === "1";
}

/**
 * Un champ de cette nature peut-il afficher un micro ?
 *
 * Sans nature déclarée, le champ est considéré comme neutre (une note libre,
 * une recommandation) et la dictée est permise — c'est l'arbitrage retenu :
 * micro partout, sauf sur les natures listées ci-dessus.
 */
export function dicteeAutorisee(nature?: NatureChamp | string): boolean {
  if (!dicteeActivee()) return false;
  if (!nature) return true;
  return !(nature in CHAMPS_SANS_DICTEE);
}

/** Raison de l'exclusion, à afficher à la place du micro. */
export function raisonExclusion(nature?: NatureChamp | string): string | null {
  if (!nature) return null;
  return CHAMPS_SANS_DICTEE[nature] ?? null;
}
