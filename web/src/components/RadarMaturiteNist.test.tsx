import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RadarMaturiteNist } from "./RadarMaturiteNist";
import { api } from "../lib/api";
import type { ProfilMaturiteNist } from "../types";

vi.mock("../lib/api", () => ({
  api: { projects: { maturiteNist: vi.fn(), definirMaturiteNist: vi.fn() } },
}));

const profil = (over: Partial<ProfilMaturiteNist> = {}): ProfilMaturiteNist => ({
  nb_evaluees: 3,
  note: "Auto-évaluation déclarative du consultant, distincte du rattachement de contrôles.",
  fonctions: [
    { code: "GV", libelle: "Gouverner", tier: 2, tier_nom: "Risk Informed", tier_description: "Conscience du risque, mais pas de processus formel à l'échelle de l'organisation", justification: "Politique existante." },
    { code: "ID", libelle: "Identifier", tier: 3, tier_nom: "Repeatable", tier_description: "Politiques formelles, application cohérente, processus de gestion des risques formalisé", justification: "" },
    { code: "PR", libelle: "Protéger", tier: 3, tier_nom: "Repeatable", tier_description: "Politiques formelles, application cohérente, processus de gestion des risques formalisé", justification: "" },
    { code: "DE", libelle: "Détecter", tier: null, tier_nom: null, tier_description: null, justification: "" },
    { code: "RS", libelle: "Répondre", tier: null, tier_nom: null, tier_description: null, justification: "" },
    { code: "RC", libelle: "Rétablir", tier: null, tier_nom: null, tier_description: null, justification: "" },
  ],
  ...over,
});

beforeEach(() => vi.clearAllMocks());

describe("RadarMaturiteNist", () => {
  it("affiche les six fonctions du CSF", async () => {
    vi.mocked(api.projects.maturiteNist).mockResolvedValue(profil());
    render(<RadarMaturiteNist projectId="p1" onProjectUpdate={vi.fn()} />);
    await screen.findAllByText("Gouverner");
    for (const f of ["Gouverner", "Identifier", "Protéger", "Détecter", "Répondre", "Rétablir"]) {
      expect(screen.getAllByText(f).length).toBeGreaterThan(0);
    }
  });

  it("affiche toujours la note de distinction avec la roue de rattachement", async () => {
    vi.mocked(api.projects.maturiteNist).mockResolvedValue(profil());
    render(<RadarMaturiteNist projectId="p1" onProjectUpdate={vi.fn()} />);
    expect(await screen.findByText(/reflète un jugement professionnel/)).toBeTruthy();
  });

  it("montre « non évalué » et jamais un faux tier pour une fonction non déclarée", async () => {
    vi.mocked(api.projects.maturiteNist).mockResolvedValue(profil());
    render(<RadarMaturiteNist projectId="p1" onProjectUpdate={vi.fn()} />);
    const bouton = await screen.findByRole("button", { name: /Détecter/ });
    expect(bouton.textContent).toContain("—");
    expect(bouton.textContent).not.toMatch(/Tier|Partial|Adaptive|Repeatable|Risk Informed/);
  });

  it("le clic sur une fonction ouvre le panneau avec son tier courant", async () => {
    vi.mocked(api.projects.maturiteNist).mockResolvedValue(profil());
    render(<RadarMaturiteNist projectId="p1" onProjectUpdate={vi.fn()} />);
    const bouton = await screen.findByRole("button", { name: /Identifier/ });
    fireEvent.click(bouton);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "3 · Repeatable" })).toBeTruthy();
      expect(screen.getByPlaceholderText("Justification (optionnelle)")).toBeTruthy();
    });
  });

  it("choisir un tier puis Enregistrer appelle definirMaturiteNist avec la bonne fonction", async () => {
    vi.mocked(api.projects.maturiteNist).mockResolvedValue(profil());
    vi.mocked(api.projects.definirMaturiteNist).mockResolvedValue({} as never);
    render(<RadarMaturiteNist projectId="p1" onProjectUpdate={vi.fn()} />);
    const bouton = await screen.findByRole("button", { name: /Détecter/ });
    fireEvent.click(bouton);

    const tier1 = await screen.findByRole("button", { name: "1 · Partial" });
    fireEvent.click(tier1);
    fireEvent.click(screen.getByRole("button", { name: /Enregistrer/ }));

    await waitFor(() => {
      expect(api.projects.definirMaturiteNist).toHaveBeenCalledWith(
        "p1", "DE", { tier: 1, justification: "" },
      );
    });
  });

  it("recliquer le tier déjà actif envoie tier: null à l'enregistrement", async () => {
    vi.mocked(api.projects.maturiteNist).mockResolvedValue(profil());
    vi.mocked(api.projects.definirMaturiteNist).mockResolvedValue({} as never);
    render(<RadarMaturiteNist projectId="p1" onProjectUpdate={vi.fn()} />);
    const bouton = await screen.findByRole("button", { name: /Identifier/ });
    fireEvent.click(bouton);

    // Identifier est déjà à Repeatable (tier 3) : recliquer l'efface.
    const tier3 = await screen.findByRole("button", { name: "3 · Repeatable" });
    fireEvent.click(tier3);
    fireEvent.click(screen.getByRole("button", { name: /Enregistrer/ }));

    await waitFor(() => {
      expect(api.projects.definirMaturiteNist).toHaveBeenCalledWith(
        "p1", "ID", { tier: null, justification: "" },
      );
    });
  });
});
