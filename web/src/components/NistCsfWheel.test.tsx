import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { NistCsfWheel } from "./NistCsfWheel";
import { api } from "../lib/api";
import type { CarteNist } from "../types";

vi.mock("../lib/api", () => ({
  api: { projects: { nistCsf: vi.fn() } },
}));

const carte = (over: Partial<CarteNist> = {}): CarteNist => ({
  mode: "indicatif",
  referentiels: ["iso27001"],
  total_rattaches: 7,
  note: "Rattachement indicatif via le catalogue de mesures. Il ne couvre qu'une partie.",
  fonctions: [
    { code: "GV", libelle: "Gouverner", rattaches: 2, couverts: 2, taux: 100, codes: ["A.5.1"] },
    { code: "ID", libelle: "Identifier", rattaches: 1, couverts: 0, taux: 0, codes: ["A.5.9"] },
    { code: "PR", libelle: "Protéger", rattaches: 4, couverts: 2, taux: 50, codes: ["A.5.17", "A.8.5"] },
    { code: "DE", libelle: "Détecter", rattaches: 0, couverts: 0, taux: null, codes: [] },
    { code: "RS", libelle: "Répondre", rattaches: 0, couverts: 0, taux: null, codes: [] },
    { code: "RC", libelle: "Rétablir", rattaches: 0, couverts: 0, taux: null, codes: [] },
    ...( [] as never[] ),
  ],
  ...over,
});

beforeEach(() => vi.clearAllMocks());

describe("NistCsfWheel", () => {
  it("affiche les six fonctions du CSF", async () => {
    vi.mocked(api.projects.nistCsf).mockResolvedValue(carte());
    render(<NistCsfWheel projectId="p1" />);
    // Chaque libellé figure à la fois dans la roue (SVG) et dans la légende :
    // on attend le rendu puis on vérifie au moins une occurrence par fonction.
    await screen.findAllByText("Gouverner");
    for (const f of ["Gouverner", "Identifier", "Protéger", "Détecter", "Répondre", "Rétablir"]) {
      expect(screen.getAllByText(f).length).toBeGreaterThan(0);
    }
  });

  it("affiche toujours l'avertissement sur la portée du rattachement indicatif", async () => {
    vi.mocked(api.projects.nistCsf).mockResolvedValue(carte());
    render(<NistCsfWheel projectId="p1" />);
    expect(await screen.findByText(/ne couvre qu'une partie/)).toBeTruthy();
  });

  it("montre un tiret et non « 0% » pour une fonction non rattachée", async () => {
    vi.mocked(api.projects.nistCsf).mockResolvedValue(carte());
    render(<NistCsfWheel projectId="p1" />);
    // Détecter n'a aucun contrôle rattaché : le libellé porte « — », pas « 0% ».
    const bouton = await screen.findByRole("button", { name: /Détecter/ });
    expect(bouton.textContent).toContain("—");
    expect(bouton.textContent).not.toContain("0%");
  });

  it("détaille les codes rattachés au clic sur une fonction", async () => {
    vi.mocked(api.projects.nistCsf).mockResolvedValue(carte());
    render(<NistCsfWheel projectId="p1" />);
    const bouton = await screen.findByRole("button", { name: /Protéger/ });
    fireEvent.click(bouton);
    await waitFor(() => {
      expect(screen.getByText("2/4 couvert(s)")).toBeTruthy();
      expect(screen.getByText("A.5.17")).toBeTruthy();
      expect(screen.getByText("A.8.5")).toBeTruthy();
    });
  });

  it("indique clairement qu'une fonction sélectionnée n'a aucun contrôle rattaché", async () => {
    vi.mocked(api.projects.nistCsf).mockResolvedValue(carte());
    render(<NistCsfWheel projectId="p1" />);
    const bouton = await screen.findByRole("button", { name: /Détecter/ });
    fireEvent.click(bouton);
    await waitFor(() =>
      expect(screen.getByText(/ne relie aucun contrôle décidé/)).toBeTruthy(),
    );
  });
});
