import { Mic, MicOff } from "lucide-react";
import { useDictee } from "../lib/useDictee";
import { dicteeAutorisee, raisonExclusion } from "../lib/dictee";
import type { NatureChamp } from "../lib/dictee";

interface Props {
  /** Reçoit chaque segment transcrit. À l'appelant de concaténer ou remplacer. */
  onTexte: (texte: string) => void;
  /** Nature du champ — sert à refuser la dictée sur les données client. */
  nature?: NatureChamp | string;
  /** Libellé du champ, pour l'intitulé accessible du bouton. */
  libelle?: string;
}

/**
 * Micro de dictée à poser à côté d'un champ texte.
 *
 * N'affiche rien du tout quand la dictée est désactivée dans les Réglages, ou
 * quand la nature du champ l'interdit (cf. `dictee.ts`) : un bouton grisé
 * inviterait à chercher comment le débloquer, alors que l'exclusion est
 * délibérée.
 */
export function BoutonDictee({ onTexte, nature, libelle }: Props) {
  const autorisee = dicteeAutorisee(nature);
  const { disponible, ecoute, erreur, basculer } = useDictee(onTexte, autorisee);

  if (!autorisee) {
    const raison = raisonExclusion(nature);
    // L'exclusion est expliquée au survol plutôt que masquée : c'est une
    // décision de confidentialité que le consultant doit pouvoir constater.
    return raison ? (
      <span
        title={`Dictée désactivée sur ce champ. ${raison}`}
        aria-hidden="true"
        className="cursor-help select-none text-[10px] text-[var(--faint)]"
      >
        <MicOff size={13} />
      </span>
    ) : null;
  }

  if (!disponible) return null;

  const intitule = libelle ? `Dicter : ${libelle}` : "Dicter ce champ";

  return (
    <span className="inline-flex items-center gap-1">
      <button
        type="button"
        onClick={basculer}
        aria-label={ecoute ? `Arrêter la dictée (${libelle ?? "champ"})` : intitule}
        aria-pressed={ecoute}
        title={
          ecoute
            ? "Arrêter la dictée"
            : "Dicter. L'audio est transmis au service de reconnaissance du navigateur."
        }
        className={`rounded-lg p-1.5 transition ${
          ecoute
            ? "animate-pulse bg-[var(--rose)]/20 text-[var(--rose)]"
            : "text-[var(--faint)] hover:bg-white/10 hover:text-[var(--ink)]"
        }`}
      >
        {ecoute ? <MicOff size={13} /> : <Mic size={13} />}
      </button>
      {erreur && (
        <span role="alert" className="text-[10px] font-bold text-[var(--rose)]">
          {erreur}
        </span>
      )}
    </span>
  );
}
