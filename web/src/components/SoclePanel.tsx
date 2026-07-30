import { useState } from "react";
import { Briefcase, ChevronDown, Plus, Trash2 } from "lucide-react";
import { nextId } from "../lib/ids";
import type { Entretien, Socle } from "../types";

interface Props {
  socle: Socle;
  onChange: (socle: Socle) => void;
}

type Bloc = "qualification" | "contractualisation" | "kickoff" | "entretiens";

const BLOCS: { cle: Bloc; titre: string; aide: string }[] = [
  { cle: "qualification", titre: "Qualification de l'opportunité",
    aide: "Pourquoi cette mission existe, qui la porte, et à quelle échéance." },
  { cle: "contractualisation", titre: "Cadrage contractuel",
    aide: "Ce qui est dans le périmètre, ce qui en est exclu, et à quelles conditions." },
  { cle: "kickoff", titre: "Réunion de lancement",
    aide: "Qui était présent et comment la mission est gouvernée." },
  { cle: "entretiens", titre: "Entretiens menés",
    aide: "Les 8 à 10 interlocuteurs à rencontrer, et ce qu'ils ont déclaré." },
];

const CHAMPS_QUALIF = [
  { cle: "declencheur", libelle: "Déclencheur de la mission", lignes: 2,
    exemple: "Exigence d'un donneur d'ordre, incident évité, échéance réglementaire…" },
  { cle: "sponsor_executif", libelle: "Sponsor exécutif", lignes: 1,
    exemple: "Fonction et niveau de rattachement" },
  { cle: "budget", libelle: "Budget vendu", lignes: 1, exemple: "ex : 18 jours" },
  { cle: "maturite_actuelle", libelle: "Maturité constatée à l'entrée", lignes: 2,
    exemple: "Ce qui existe déjà, ce qui manque manifestement" },
  { cle: "equipe_interne", libelle: "Équipe interne mobilisable", lignes: 2,
    exemple: "Rôles et disponibilité réelle en ETP" },
  { cle: "echeance_cible", libelle: "Échéance cible", lignes: 1, exemple: "AAAA-MM-JJ" },
] as const;

const CHAMPS_CONTRAT = [
  { cle: "perimetre_inclus", libelle: "Périmètre inclus", lignes: 2,
    exemple: "Sites, systèmes et fonctions couverts" },
  { cle: "perimetre_exclu", libelle: "Périmètre explicitement exclu", lignes: 2,
    exemple: "Ce qui borne votre responsabilité — repris tel quel dans le rapport" },
  { cle: "modalites", libelle: "Modalités d'intervention", lignes: 2,
    exemple: "Durée, jours sur site, rythme des points d'avancement" },
  { cle: "acces_si", libelle: "Accès au SI consentis", lignes: 2,
    exemple: "Comptes, niveaux de droit, ce qui reste fourni par le client" },
] as const;

const CHAMPS_KICKOFF = [
  { cle: "date", libelle: "Date de la réunion de lancement", lignes: 1, exemple: "AAAA-MM-JJ" },
  { cle: "gouvernance", libelle: "Gouvernance de la mission", lignes: 2,
    exemple: "Instance, fréquence, règle d'escalade en cas de découverte critique" },
] as const;

const CLASSE_CHAMP =
  "w-full bg-white/[0.02] border border-[var(--stroke)] rounded-xl px-2.5 py-1.5 text-xs text-[var(--ink)] focus:outline-none focus:border-[var(--g1)]";

/** Socle commun de la mission — le cadrage qui rend le périmètre opposable.
 *
 *  Ces champs existaient dans le modèle de données depuis le jalon 1 sans aucun
 *  écran : la recette du 29/07/2026 a montré qu'ils n'étaient remplissables que
 *  par l'API, et que le chapitre « Cadrage » du rapport sortait donc toujours vide.
 */
export function SoclePanel({ socle, onChange }: Props) {
  const [ouvert, setOuvert] = useState<Bloc | null>("qualification");
  const [nouvelEntretien, setNouvelEntretien] = useState({ role: "", personne: "", date: "", synthese: "" });
  const [nouveauLivrable, setNouveauLivrable] = useState("");
  const [nouveauParticipant, setNouveauParticipant] = useState("");

  const majBloc = <B extends "qualification" | "contractualisation" | "kickoff">(
    bloc: B, champ: string, valeur: unknown,
  ) => onChange({ ...socle, [bloc]: { ...(socle[bloc] ?? {}), [champ]: valeur } });

  const listeContrat = socle.contractualisation?.livrables ?? [];
  const listeParticipants = socle.kickoff?.participants ?? [];
  const entretiens = socle.entretiens ?? [];

  const ajouterEntretien = () => {
    if (!nouvelEntretien.role.trim() || !nouvelEntretien.synthese.trim()) return;
    onChange({
      ...socle,
      entretiens: [...entretiens, { id: nextId("ENT", entretiens.map((e) => e.id)), ...nouvelEntretien }],
    });
    setNouvelEntretien({ role: "", personne: "", date: "", synthese: "" });
  };

  const rempli = (bloc: Bloc): number => {
    if (bloc === "entretiens") return entretiens.length;
    const valeurs = Object.values((socle[bloc] ?? {}) as Record<string, unknown>);
    return valeurs.filter((v) => (Array.isArray(v) ? v.length > 0 : String(v ?? "").trim())).length;
  };

  return (
    <div className="glass-2 p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Briefcase size={14} className="text-[var(--g1)]" />
        <span className="text-[10px] font-bold text-[var(--faint)] uppercase tracking-wide">
          Socle de la mission
        </span>
      </div>
      <p className="text-[11px] text-[var(--soft)]">
        Le cadrage repris au chapitre « Cadrage de la mission » du rapport d'audit. Ce qui n'est pas
        saisi ici n'apparaît pas dans le livrable — aucune valeur n'est supposée à votre place.
      </p>

      {BLOCS.map(({ cle, titre, aide }) => {
        const estOuvert = ouvert === cle;
        return (
          <div key={cle} className="border border-white/[0.05] rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setOuvert(estOuvert ? null : cle)}
              aria-expanded={estOuvert}
              className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-white/[0.02] hover:bg-white/[0.04] text-left"
            >
              <span className="flex flex-col">
                <span className="text-xs font-bold text-[var(--ink)]">{titre}</span>
                <span className="text-[10px] text-[var(--faint)]">{aide}</span>
              </span>
              <span className="flex items-center gap-2 flex-shrink-0">
                <span className="text-[10px] font-mono text-[var(--soft)]">{rempli(cle)}</span>
                <ChevronDown
                  size={14}
                  className={`text-[var(--soft)] transition-transform ${estOuvert ? "rotate-180" : ""}`}
                />
              </span>
            </button>

            {estOuvert && (
              <div className="p-3 flex flex-col gap-2.5 bg-white/[0.01]">
                {cle === "qualification" && CHAMPS_QUALIF.map((c) => (
                  <div key={c.cle}>
                    <label htmlFor={`socle-${c.cle}`} className="block text-[10px] font-bold text-[var(--soft)] mb-1">
                      {c.libelle}
                    </label>
                    {c.lignes > 1 ? (
                      <textarea id={`socle-${c.cle}`} rows={c.lignes} placeholder={c.exemple}
                        value={socle.qualification?.[c.cle] ?? ""}
                        onChange={(e) => majBloc("qualification", c.cle, e.target.value)}
                        className={CLASSE_CHAMP} />
                    ) : (
                      <input id={`socle-${c.cle}`} type="text" placeholder={c.exemple}
                        value={socle.qualification?.[c.cle] ?? ""}
                        onChange={(e) => majBloc("qualification", c.cle, e.target.value)}
                        className={CLASSE_CHAMP} />
                    )}
                  </div>
                ))}

                {cle === "contractualisation" && (
                  <>
                    {CHAMPS_CONTRAT.map((c) => (
                      <div key={c.cle}>
                        <label htmlFor={`socle-${c.cle}`} className="block text-[10px] font-bold text-[var(--soft)] mb-1">
                          {c.libelle}
                        </label>
                        <textarea id={`socle-${c.cle}`} rows={c.lignes} placeholder={c.exemple}
                          value={socle.contractualisation?.[c.cle] ?? ""}
                          onChange={(e) => majBloc("contractualisation", c.cle, e.target.value)}
                          className={CLASSE_CHAMP} />
                      </div>
                    ))}
                    <ListeEditable
                      libelle="Livrables contractuels"
                      exemple="ex : Rapport d'audit avec constats sourcés"
                      items={listeContrat}
                      valeur={nouveauLivrable}
                      setValeur={setNouveauLivrable}
                      onAjout={(v) => majBloc("contractualisation", "livrables", [...listeContrat, v])}
                      onRetrait={(i) =>
                        majBloc("contractualisation", "livrables", listeContrat.filter((_, j) => j !== i))}
                    />
                  </>
                )}

                {cle === "kickoff" && (
                  <>
                    {CHAMPS_KICKOFF.map((c) => (
                      <div key={c.cle}>
                        <label htmlFor={`socle-${c.cle}`} className="block text-[10px] font-bold text-[var(--soft)] mb-1">
                          {c.libelle}
                        </label>
                        {c.lignes > 1 ? (
                          <textarea id={`socle-${c.cle}`} rows={c.lignes} placeholder={c.exemple}
                            value={socle.kickoff?.[c.cle] ?? ""}
                            onChange={(e) => majBloc("kickoff", c.cle, e.target.value)}
                            className={CLASSE_CHAMP} />
                        ) : (
                          <input id={`socle-${c.cle}`} type="text" placeholder={c.exemple}
                            value={socle.kickoff?.[c.cle] ?? ""}
                            onChange={(e) => majBloc("kickoff", c.cle, e.target.value)}
                            className={CLASSE_CHAMP} />
                        )}
                      </div>
                    ))}
                    <ListeEditable
                      libelle="Participants au lancement"
                      exemple="ex : RSSI"
                      items={listeParticipants}
                      valeur={nouveauParticipant}
                      setValeur={setNouveauParticipant}
                      onAjout={(v) => majBloc("kickoff", "participants", [...listeParticipants, v])}
                      onRetrait={(i) =>
                        majBloc("kickoff", "participants", listeParticipants.filter((_, j) => j !== i))}
                    />
                  </>
                )}

                {cle === "entretiens" && (
                  <div className="flex flex-col gap-2">
                    {entretiens.map((e: Entretien) => (
                      <div key={e.id} className="bg-white/[0.02] border border-white/[0.05] rounded-lg p-2.5 flex justify-between gap-2">
                        <div className="min-w-0">
                          <div className="text-[11px] font-bold text-[var(--ink)]">
                            {e.role}
                            {e.personne && <span className="text-[var(--soft)] font-normal"> · {e.personne}</span>}
                            {e.date && <span className="text-[var(--faint)] font-normal"> · {e.date}</span>}
                          </div>
                          <p className="text-[10px] text-[var(--soft)] mt-0.5">{e.synthese}</p>
                        </div>
                        <button
                          type="button"
                          aria-label={`Retirer l'entretien ${e.role}`}
                          onClick={() => onChange({ ...socle, entretiens: entretiens.filter((x) => x.id !== e.id) })}
                          className="text-[var(--rose)] hover:bg-white/5 p-1 rounded-lg self-start flex-shrink-0"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    ))}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2 border border-dashed border-[var(--stroke)] rounded-lg p-2.5">
                      <div>
                        <label htmlFor="ent-role" className="block text-[10px] font-bold text-[var(--soft)] mb-1">Rôle</label>
                        <input id="ent-role" type="text" placeholder="ex : RSSI"
                          value={nouvelEntretien.role}
                          onChange={(e) => setNouvelEntretien({ ...nouvelEntretien, role: e.target.value })}
                          className={CLASSE_CHAMP} />
                      </div>
                      <div>
                        <label htmlFor="ent-personne" className="block text-[10px] font-bold text-[var(--soft)] mb-1">Fonction précise</label>
                        <input id="ent-personne" type="text" placeholder="Sans nom : voir politique RGPD"
                          value={nouvelEntretien.personne}
                          onChange={(e) => setNouvelEntretien({ ...nouvelEntretien, personne: e.target.value })}
                          className={CLASSE_CHAMP} />
                      </div>
                      <div>
                        <label htmlFor="ent-date" className="block text-[10px] font-bold text-[var(--soft)] mb-1">Date</label>
                        <input id="ent-date" type="date"
                          value={nouvelEntretien.date}
                          onChange={(e) => setNouvelEntretien({ ...nouvelEntretien, date: e.target.value })}
                          className={CLASSE_CHAMP} />
                      </div>
                      <div className="md:col-span-3">
                        <label htmlFor="ent-synthese" className="block text-[10px] font-bold text-[var(--soft)] mb-1">
                          Ce qui a été déclaré
                        </label>
                        <textarea id="ent-synthese" rows={2}
                          placeholder="Constat attribuable, tel que déclaré — pas votre interprétation"
                          value={nouvelEntretien.synthese}
                          onChange={(e) => setNouvelEntretien({ ...nouvelEntretien, synthese: e.target.value })}
                          className={CLASSE_CHAMP} />
                      </div>
                      <div className="md:col-span-3 flex justify-end">
                        <button
                          type="button"
                          onClick={ajouterEntretien}
                          className="px-3 py-1.5 bg-[var(--g1)] text-[#04150e] font-bold rounded-xl text-[11px] hover:opacity-90 flex items-center gap-1"
                        >
                          <Plus size={12} /> Ajouter l'entretien
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface ListeProps {
  libelle: string;
  exemple: string;
  items: string[];
  valeur: string;
  setValeur: (v: string) => void;
  onAjout: (v: string) => void;
  onRetrait: (index: number) => void;
}

function ListeEditable({ libelle, exemple, items, valeur, setValeur, onAjout, onRetrait }: ListeProps) {
  const ajouter = () => {
    if (!valeur.trim()) return;
    onAjout(valeur.trim());
    setValeur("");
  };

  return (
    <div>
      <label htmlFor={`liste-${libelle}`} className="block text-[10px] font-bold text-[var(--soft)] mb-1">
        {libelle}
      </label>
      <div className="flex flex-col gap-1.5">
        {items.map((item, i) => (
          <div key={`${item}-${i}`} className="flex items-center justify-between gap-2 bg-white/[0.02] rounded-lg px-2.5 py-1">
            <span className="text-[11px] text-[var(--ink)]">{item}</span>
            <button
              type="button"
              aria-label={`Retirer ${item}`}
              onClick={() => onRetrait(i)}
              className="text-[var(--rose)] hover:bg-white/5 p-1 rounded flex-shrink-0"
            >
              <Trash2 size={11} />
            </button>
          </div>
        ))}
        <div className="flex gap-2">
          <input
            id={`liste-${libelle}`}
            type="text"
            placeholder={exemple}
            value={valeur}
            onChange={(e) => setValeur(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); ajouter(); } }}
            className={CLASSE_CHAMP}
          />
          <button
            type="button"
            onClick={ajouter}
            aria-label={`Ajouter à ${libelle}`}
            className="px-2.5 bg-white/[0.06] hover:bg-white/[0.1] rounded-xl text-[var(--g1)] flex-shrink-0"
          >
            <Plus size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
