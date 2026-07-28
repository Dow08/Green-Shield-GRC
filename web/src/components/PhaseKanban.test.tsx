import { useState } from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PhaseKanban } from "./PhaseKanban";
import type { Workflow, AvancementWorkflow, ValeurChamp } from "../types/workflow";

// Workflow minimal mais structurellement fidèle à iso27001/workflow.yaml :
// pas de contenu inventé dans le composant, tout vient de cette donnée.
function workflowMinimal(): Workflow {
  return {
    metadata: { id: "test", name: "Test", version: "1.0.0" },
    macro_phases: [
      {
        id: "preparation",
        titre: "1. Préparation",
        duree: "Semaine 1",
        etapes: [
          {
            id: "cadrage_mission",
            titre: "Cadrer la mission",
            jour_relatif: 1,
            role_a_rencontrer: ["Sponsor exécutif", "RSSI"],
            questions: ["Quel est le périmètre exact ?"],
            champs: [
              { key: "perimetre", label: "Périmètre exact", type: "text" },
              { key: "nda_signe", label: "NDA signé", type: "boolean" },
              { key: "documents_recus", label: "Documents reçus", type: "list" },
              {
                key: "controles_annexe_a", label: "Contrôles Annexe A", type: "preuve_technique",
                source_automatique: "auditcraft_grc", note: "Alimenté par le scan technique.",
              },
            ],
            livrables: ["Lettre de mission signée"],
            sources: [{ label: "ISO 27001 clause 4", url: "" }],
          },
          {
            id: "collecte_documentation",
            titre: "Collecter la documentation",
            duree: "J-15",
            questions: [],
            champs: [],
            livrables: [],
            sources: [],
          },
        ],
      },
      {
        id: "execution",
        titre: "2. Exécution",
        etapes: [{ id: "reunion_ouverture", titre: "Réunion d'ouverture" }],
      },
    ],
  };
}

function renderKanban(overrides: Partial<Parameters<typeof PhaseKanban>[0]> = {}) {
  return render(
    <PhaseKanban
      workflow={workflowMinimal()}
      avancement={{}}
      onStatusChange={vi.fn()}
      onValueChange={vi.fn()}
      {...overrides}
    />
  );
}

async function ouvrirCadrageMission() {
  const user = userEvent.setup();
  await user.click(screen.getByText("Cadrer la mission"));
  return user;
}

/** Harnais contrôlé : reflète comment IsoPivotView tient réellement l'état,
 * pour que la saisie s'accumule au lieu d'être réinitialisée à chaque frappe
 * par un composant purement contrôlé sans retour d'état. */
function KanbanControle({ onValueChange }: { onValueChange: (e: string, k: string, v: ValeurChamp) => void }) {
  const [avancement, setAvancement] = useState<AvancementWorkflow>({});
  return (
    <PhaseKanban
      workflow={workflowMinimal()}
      avancement={avancement}
      onStatusChange={() => {}}
      onValueChange={(etapeId, champKey, valeur) => {
        onValueChange(etapeId, champKey, valeur);
        setAvancement((prev) => ({
          ...prev,
          [etapeId]: { statut: prev[etapeId]?.statut ?? "a_faire", valeurs: { ...prev[etapeId]?.valeurs, [champKey]: valeur } },
        }));
      }}
    />
  );
}

describe("PhaseKanban", () => {
  it("rend une colonne par macro-phase et une carte par étape", () => {
    renderKanban();
    expect(screen.getByLabelText("1. Préparation")).toBeInTheDocument();
    expect(screen.getByLabelText("2. Exécution")).toBeInTheDocument();
    expect(screen.getByText("Cadrer la mission")).toBeInTheDocument();
    expect(screen.getByText("Réunion d'ouverture")).toBeInTheDocument();
  });

  it("n'invente aucune étape ni aucune macro-phase absente du workflow fourni", () => {
    renderKanban();
    // 3 étapes au total dans la donnée -> exactement 3 cartes, pas de contenu fantôme.
    const cartes = screen.getAllByRole("button", { name: /statut de/i });
    expect(cartes).toHaveLength(3);
  });

  it("affiche À faire par défaut quand l'étape est absente de l'avancement", () => {
    renderKanban();
    const boutonStatut = screen.getByRole("button", {
      name: /statut de « cadrer la mission ».*à faire/i,
    });
    expect(boutonStatut).toHaveTextContent("À faire");
  });

  it("reflète le statut fourni dans l'avancement, sans le modifier de son propre chef", () => {
    const avancement: AvancementWorkflow = { cadrage_mission: { statut: "fait" } };
    renderKanban({ avancement });
    expect(
      screen.getByRole("button", { name: /statut de « cadrer la mission ».*fait/i })
    ).toHaveTextContent("Fait");
  });

  it("fait cycler le statut à_faire -> en_cours -> fait -> à_faire au tap", async () => {
    const user = userEvent.setup();
    const onStatusChange = vi.fn();
    renderKanban({ onStatusChange });

    const bouton = screen.getByRole("button", { name: /statut de « cadrer la mission »/i });
    await user.click(bouton);
    expect(onStatusChange).toHaveBeenCalledWith("cadrage_mission", "en_cours");
  });

  it("cycle correctement depuis en_cours vers fait, puis de fait vers à_faire", async () => {
    const user = userEvent.setup();
    const onStatusChange = vi.fn();
    const { rerender } = renderKanban({
      avancement: { cadrage_mission: { statut: "en_cours" } },
      onStatusChange,
    });
    await user.click(screen.getByRole("button", { name: /statut de « cadrer la mission »/i }));
    expect(onStatusChange).toHaveBeenCalledWith("cadrage_mission", "fait");

    rerender(
      <PhaseKanban
        workflow={workflowMinimal()}
        avancement={{ cadrage_mission: { statut: "fait" } }}
        onStatusChange={onStatusChange}
        onValueChange={vi.fn()}
      />
    );
    await user.click(screen.getByRole("button", { name: /statut de « cadrer la mission »/i }));
    expect(onStatusChange).toHaveBeenLastCalledWith("cadrage_mission", "a_faire");
  });

  it("le compteur de colonne compte les étapes réellement faites, pas devinées", () => {
    const avancement: AvancementWorkflow = {
      cadrage_mission: { statut: "fait" },
      collecte_documentation: { statut: "en_cours" },
    };
    renderKanban({ avancement });
    const colonnePreparation = screen.getByLabelText("1. Préparation");
    expect(colonnePreparation).toHaveTextContent("1/2");
  });

  it("n'affiche pas de bascule de détail pour une étape sans questions/champs/livrables/sources", () => {
    renderKanban();
    // "Réunion d'ouverture" n'a aucun contenu détaillé : pas de chevron cliquable inutile.
    const carteVide = screen.getByText("Réunion d'ouverture").closest("button");
    expect(carteVide).toHaveAttribute("aria-expanded", "false");
    expect(carteVide?.querySelector("svg")).toBeNull();
  });

  it("déplie les questions au clic, sans les inventer ni en perdre", async () => {
    renderKanban();
    expect(screen.queryByText("Quel est le périmètre exact ?")).not.toBeInTheDocument();
    await ouvrirCadrageMission();
    expect(screen.getByText("Quel est le périmètre exact ?")).toBeInTheDocument();
    expect(screen.getByText("Lettre de mission signée")).toBeInTheDocument();
  });

  it("affiche une source sans URL comme « hors couverture », sans deviner de lien", async () => {
    renderKanban();
    await ouvrirCadrageMission();
    expect(screen.getByText(/hors couverture/i)).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  // --- Saisie des champs (§13, "remplissable" — pas seulement un statut) ---

  it("affiche un champ texte vide quand aucune valeur n'a encore été saisie", async () => {
    renderKanban();
    await ouvrirCadrageMission();
    const champ = screen.getByLabelText("Périmètre exact") as HTMLInputElement;
    expect(champ.value).toBe("");
  });

  it("répercute la saisie d'un champ texte via onValueChange, et l'accumule à mesure de la frappe", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    render(<KanbanControle onValueChange={onValueChange} />);
    await ouvrirCadrageMission();

    const champ = screen.getByLabelText("Périmètre exact");
    await user.type(champ, "SI");
    expect(onValueChange).toHaveBeenCalledWith("cadrage_mission", "perimetre", "S");
    expect(onValueChange).toHaveBeenLastCalledWith("cadrage_mission", "perimetre", "SI");
  });

  it("réaffiche une valeur texte déjà saisie (relecture après sauvegarde)", async () => {
    renderKanban({
      avancement: { cadrage_mission: { statut: "a_faire", valeurs: { perimetre: "SI de production" } } },
    });
    await ouvrirCadrageMission();
    expect(screen.getByLabelText("Périmètre exact")).toHaveValue("SI de production");
  });

  it("le champ booléen respecte la valeur fournie sans la réinventer", () => {
    renderKanban({
      avancement: { cadrage_mission: { statut: "a_faire", valeurs: { nda_signe: true } } },
    });
    // La carte est fermée par défaut : on doit d'abord l'ouvrir pour trouver la case.
    return ouvrirCadrageMission().then(() => {
      expect(screen.getByLabelText("NDA signé")).toBeChecked();
    });
  });

  it("un champ liste convertit le texte en lignes, une entrée par ligne", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    render(<KanbanControle onValueChange={onValueChange} />);
    await ouvrirCadrageMission();
    const zone = screen.getByPlaceholderText("une entrée par ligne");
    await user.type(zone, "A{Enter}B");
    expect(onValueChange).toHaveBeenLastCalledWith("cadrage_mission", "documents_recus", ["A", "B"]);
  });

  it("un champ preuve_technique n'a aucune saisie manuelle : lecture seule", async () => {
    renderKanban();
    await ouvrirCadrageMission();
    expect(screen.getByText("Alimenté par le scan technique.")).toBeInTheDocument();
    // Ni input ni textarea pour ce champ précis — seule une preuve réelle l'alimente.
    expect(screen.queryByLabelText("Contrôles Annexe A")).not.toBeInTheDocument();
  });
});
