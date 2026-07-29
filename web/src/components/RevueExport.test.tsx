import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RevueExport } from "./RevueExport";
import type { RevueExportResult } from "../types";

function revueFixture(overrides: Partial<RevueExportResult> = {}): RevueExportResult {
  return {
    complet: false,
    pret_pour_export: false,
    total: 2,
    bloquants: 1,
    manques: [
      { phase: 1, phase_libelle: "Cadrage & Patrimoine", champ: "Périmètre technique de l'audit", gravite: "bloquant" },
      { phase: 5, phase_libelle: "Résilience & E3R", champ: "Cible de reprise (RTO)", gravite: "recommande" },
    ],
    ...overrides,
  };
}

function renderRevue(props: Partial<Parameters<typeof RevueExport>[0]> = {}) {
  const complet = {
    revue: revueFixture(),
    chargement: false,
    onAllerALaPhase: vi.fn(),
    ...props,
  };
  render(<RevueExport {...complet} />);
  return complet;
}

describe("RevueExport", () => {
  it("n'affiche rien tant qu'aucune revue n'est disponible", () => {
    const { container } = render(
      <RevueExport revue={null} chargement={false} onAllerALaPhase={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("annonce l'analyse en cours", () => {
    renderRevue({ chargement: true });
    expect(screen.getByText(/Analyse de la complétude/i)).toBeInTheDocument();
  });

  it("confirme explicitement une mission complète", () => {
    renderRevue({ revue: revueFixture({ complet: true, total: 0, bloquants: 0, manques: [] }) });
    expect(screen.getByText(/Mission complète/i)).toBeInTheDocument();
  });

  it("liste chaque manque avec sa phase", () => {
    renderRevue();
    expect(screen.getByText("Périmètre technique de l'audit")).toBeInTheDocument();
    expect(screen.getByText(/Phase 1 — Cadrage & Patrimoine/)).toBeInTheDocument();
    expect(screen.getByText("Cible de reprise (RTO)")).toBeInTheDocument();
  });

  it("compte les manques bloquants", () => {
    renderRevue();
    expect(screen.getByText(/1 manque\(s\) bloquant\(s\)/)).toBeInTheDocument();
  });

  it("compte les points à compléter quand rien n'est bloquant", () => {
    renderRevue({
      revue: revueFixture({
        pret_pour_export: true, bloquants: 0, total: 1,
        manques: [{ phase: 5, phase_libelle: "Résilience & E3R", champ: "Politique de sauvegarde", gravite: "recommande" }],
      }),
    });
    expect(screen.getByText(/1 point\(s\) à compléter/)).toBeInTheDocument();
  });

  it("affiche les manques bloquants avant les recommandations", () => {
    renderRevue();
    const libelles = screen.getAllByRole("button").map((b) => b.textContent ?? "");
    expect(libelles[0]).toContain("Périmètre technique");
    expect(libelles[1]).toContain("Cible de reprise");
  });

  it("permet de sauter à la phase concernée", async () => {
    const user = userEvent.setup();
    const { onAllerALaPhase } = renderRevue();

    await user.click(screen.getByText("Cible de reprise (RTO)").closest("button")!);

    expect(onAllerALaPhase).toHaveBeenCalledWith(5);
  });

  it("explique pourquoi compléter avant de transmettre", () => {
    renderRevue();
    expect(screen.getByText(/remplacent les champs vides/i)).toBeInTheDocument();
  });
});
