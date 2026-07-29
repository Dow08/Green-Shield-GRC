import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TempsPanel } from "./TempsPanel";
import type { TempsEntree } from "../types";

function entrees(): TempsEntree[] {
  return [
    { id: "T-001", phase: "cadrage", minutes: 90, date: "2026-07-20", note: "Réunion de lancement" },
    { id: "T-002", phase: "ebios", minutes: 150, date: "2026-07-21", note: "" },
  ];
}

function renderPanel(overrides: Partial<Parameters<typeof TempsPanel>[0]> = {}) {
  const props = {
    entrees: entrees(),
    onAdd: vi.fn(),
    onDelete: vi.fn(),
    ...overrides,
  };
  render(<TempsPanel {...props} />);
  return props;
}

describe("TempsPanel", () => {
  it("affiche le total cumulé des entrées", () => {
    renderPanel(); // 90 + 150 = 240 min = 4 h
    expect(screen.getByText("4 h")).toBeInTheDocument();
  });

  it("affiche le budget vendu quand il est renseigné", () => {
    renderPanel({ budget: "10 jours" });
    expect(screen.getByText("10 jours")).toBeInTheDocument();
  });

  it("n'affiche pas de budget quand il est absent", () => {
    renderPanel();
    expect(screen.queryByText(/Budget vendu/)).not.toBeInTheDocument();
  });

  it("ventile le total par phase, sans inventer de phase vide", () => {
    renderPanel();
    // Les pastilles de ventilation portent "Label · durée" — à distinguer des
    // <option> du sélecteur, qui portent le même label seul.
    const pastille = (regex: RegExp) =>
      screen.queryAllByText(regex).find((n) => n.tagName !== "OPTION");

    expect(pastille(/1\. Cadrage ·/)).toBeDefined();
    expect(pastille(/4\. EBIOS RM ·/)).toBeDefined();
    // Aucune entrée sur TPRM : la pastille ne doit pas exister.
    expect(pastille(/3\. Risques Tiers ·/)).toBeUndefined();
  });

  it("affiche un état vide explicite quand aucun temps n'est saisi", () => {
    renderPanel({ entrees: [] });
    expect(screen.getByText(/Aucun temps saisi/i)).toBeInTheDocument();
  });

  it("liste les entrées, la plus récente en premier", () => {
    renderPanel();
    const dates = screen.getAllByText(/2026-07-2\d/).map((n) => n.textContent);
    expect(dates[0]).toBe("2026-07-21");
  });

  it("transmet la saisie via onAdd", async () => {
    const user = userEvent.setup();
    const { onAdd } = renderPanel();

    await user.selectOptions(screen.getByLabelText("Phase concernée"), "tprm");
    await user.type(screen.getByLabelText("Durée en minutes"), "45");
    await user.type(screen.getByLabelText("Note"), "Analyse fournisseur");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(onAdd).toHaveBeenCalledWith({ phase: "tprm", minutes: 45, note: "Analyse fournisseur" });
  });

  it("refuse une durée vide sans appeler onAdd", async () => {
    const user = userEvent.setup();
    const { onAdd } = renderPanel();

    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(onAdd).not.toHaveBeenCalled();
    expect(screen.getByText(/saisissez une durée/i)).toBeInTheDocument();
  });

  it("refuse une durée nulle ou négative", async () => {
    const user = userEvent.setup();
    const { onAdd } = renderPanel();

    await user.type(screen.getByLabelText("Durée en minutes"), "-10");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(onAdd).not.toHaveBeenCalled();
  });

  it("vide les champs après un ajout réussi", async () => {
    const user = userEvent.setup();
    renderPanel({ onAdd: vi.fn().mockResolvedValue(undefined) });

    const duree = screen.getByLabelText("Durée en minutes");
    await user.type(duree, "30");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(duree).toHaveValue(null);
  });

  it("affiche l'erreur remontée par onAdd sans perdre la saisie", async () => {
    const user = userEvent.setup();
    renderPanel({ onAdd: vi.fn().mockRejectedValue(new Error("HTTP 400")) });

    await user.type(screen.getByLabelText("Durée en minutes"), "30");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(await screen.findByText("HTTP 400")).toBeInTheDocument();
    expect(screen.getByLabelText("Durée en minutes")).toHaveValue(30);
  });

  it("supprime une entrée via onDelete", async () => {
    const user = userEvent.setup();
    const { onDelete } = renderPanel();

    await user.click(screen.getByRole("button", { name: /supprimer l'entrée de temps du 2026-07-21/i }));

    expect(onDelete).toHaveBeenCalledWith("T-002");
  });

  it("supporte une phase inconnue sans planter (mission d'une version antérieure)", () => {
    renderPanel({
      entrees: [{ id: "T-009", phase: "phase_disparue" as never, minutes: 60, date: "2026-01-01", note: "" }],
    });
    expect(screen.getByText("phase_disparue")).toBeInTheDocument();
  });

  it("tronque visuellement une note très longue sans casser la mise en page", () => {
    const longue = "MotTresLongSansEspace".repeat(20);
    renderPanel({
      entrees: [{ id: "T-010", phase: "autre", minutes: 30, date: "2026-01-01", note: longue }],
    });
    const noteNode = screen.getByText(new RegExp(longue.slice(0, 30)));
    expect(noteNode.className).toContain("truncate");
  });
});
