import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HistoriquePanel } from "./HistoriquePanel";
import type { SnapshotInfo } from "../types";

function instantanes(): SnapshotInfo[] {
  return [
    { nom: "20260729-140000_phase-cadrage-validee.json", date: "29/07/2026 14:00:00", motif: "phase cadrage validee", octets: 4096 },
    { nom: "20260728-090000_phase-ebios-validee.json", date: "28/07/2026 09:00:00", motif: "phase ebios validee", octets: 5120 },
  ];
}

function renderPanel(overrides: Partial<Parameters<typeof HistoriquePanel>[0]> = {}) {
  const props = { instantanes: instantanes(), onRestaurer: vi.fn().mockResolvedValue(undefined), ...overrides };
  render(<HistoriquePanel {...props} />);
  return props;
}

describe("HistoriquePanel", () => {
  it("explique quand aucun point de restauration n'existe", () => {
    renderPanel({ instantanes: [] });
    expect(screen.getByText(/Aucun point de restauration/i)).toBeInTheDocument();
    expect(screen.getByText(/à chaque validation de phase/i)).toBeInTheDocument();
  });

  it("liste les instantanés avec leur motif et leur date", () => {
    renderPanel();
    expect(screen.getByText("phase cadrage validee")).toBeInTheDocument();
    expect(screen.getByText("29/07/2026 14:00:00")).toBeInTheDocument();
  });

  it("demande confirmation avant de restaurer", async () => {
    const user = userEvent.setup();
    const { onRestaurer } = renderPanel();

    await user.click(screen.getByRole("button", { name: /Restaurer l'état du 29\/07\/2026/i }));

    expect(onRestaurer).not.toHaveBeenCalled();
    expect(screen.getByText(/Écraser l'état actuel/i)).toBeInTheDocument();
  });

  it("restaure après confirmation", async () => {
    const user = userEvent.setup();
    const { onRestaurer } = renderPanel();

    await user.click(screen.getByRole("button", { name: /Restaurer l'état du 29\/07\/2026/i }));
    await user.click(screen.getByRole("button", { name: /confirmer/i }));

    expect(onRestaurer).toHaveBeenCalledWith("20260729-140000_phase-cadrage-validee.json");
  });

  it("permet d'annuler la confirmation sans rien restaurer", async () => {
    const user = userEvent.setup();
    const { onRestaurer } = renderPanel();

    await user.click(screen.getByRole("button", { name: /Restaurer l'état du 29\/07\/2026/i }));
    await user.click(screen.getByRole("button", { name: /annuler/i }));

    expect(onRestaurer).not.toHaveBeenCalled();
    expect(screen.queryByText(/Écraser l'état actuel/i)).not.toBeInTheDocument();
  });

  it("affiche l'erreur remontée par l'API", async () => {
    const user = userEvent.setup();
    renderPanel({ onRestaurer: vi.fn().mockRejectedValue(new Error("Instantané illisible")) });

    await user.click(screen.getByRole("button", { name: /Restaurer l'état du 29\/07\/2026/i }));
    await user.click(screen.getByRole("button", { name: /confirmer/i }));

    expect(await screen.findByText("Instantané illisible")).toBeInTheDocument();
  });

  it("rassure sur la réversibilité de l'opération", () => {
    renderPanel();
    expect(screen.getByText(/sauvegardé avant toute restauration/i)).toBeInTheDocument();
  });
});
