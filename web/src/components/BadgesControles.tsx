import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { PratiqueControle } from "../types";

interface Props {
  /** Identifiant de pratique côté serveur (`vulnerabilites`, `journalisation`…). */
  pratique: string;
}

/** Contrôles CIS v8 / NIST CSF auxquels répond une case cochée (§14.2.4).
 *
 *  Un booléen coché ne vaut rien devant un client s'il ne se rattache à rien.
 *  Le rattachement décrit les référentiels, pas la mission : il est lu depuis
 *  l'API et jamais recopié ici.
 */
export function BadgesControles({ pratique }: Props) {
  const [referentiel, setReferentiel] = useState<PratiqueControle[]>([]);

  useEffect(() => {
    // Un échec reste silencieux : c'est un enrichissement, pas une donnée de
    // mission — mieux vaut une case sans étiquette qu'un écran en erreur.
    api.controles.referentiel().then(setReferentiel).catch(() => undefined);
  }, []);

  const mappings = referentiel.find((p) => p.id === pratique)?.mappings ?? [];
  if (mappings.length === 0) return null;

  return (
    <span className="flex flex-wrap gap-1 mt-0.5">
      {mappings.map((m) => (
        <span
          key={`${m.referentiel}-${m.ref}`}
          title={`${m.referentiel} — ${m.intitule}`}
          className="text-[9px] font-bold rounded-full px-1.5 py-0.5 bg-white/[0.06] text-[var(--g3)]"
        >
          {m.ref}
        </span>
      ))}
    </span>
  );
}
