import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { DemandesPreuvesPanel } from "./DemandesPreuvesPanel";
import { api } from "../lib/api";
import type { RegistreDemandesPreuves, ProjectState } from "../types";

/**
 * Le registre est un fait de conduite de mission : ces tests vérifient qu'il
 * affiche l'attente et la relance sans jamais masquer un manque.
 */

vi.mock("../lib/api", () => ({
  api: {
    projects: {
      demandesPreuves: vi.fn(),
      addDemandePreuve: vi.fn(),
      updateDemandePreuve: vi.fn(),
      deleteDemandePreuve: vi.fn(),
    },
  },
}));

const registre = (partiel: Partial<RegistreDemandesPreuves> = {}): RegistreDemandesPreuves => ({
  demandes: [],
  synthese: { total: 0, en_attente: 0, recues: 0, refusees: 0, a_relancer: 0,
              plus_ancienne_jours: null, delai_relance_jours: 7 },
  controles_sans_justificatif: [],
  ...partiel,
});

const demande = (over = {}) => ({
  id: "DEM-01", libelle: "PSSI signée", destinataire: "RSSI", statut: "relancee" as const,
  date_demande: "2026-07-01", date_relance: "2026-07-20", date_reponse: "", echeance: "",
  note: "", controles_lies: [], preuve_id: "", ...over,
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DemandesPreuvesPanel", () => {
  it("affiche les quatre compteurs de statut", async () => {
    vi.mocked(api.projects.demandesPreuves).mockResolvedValue(
      registre({ synthese: { total: 4, en_attente: 1, recues: 2, refusees: 1, a_relancer: 1,
                             plus_ancienne_jours: 3, delai_relance_jours: 7 } }),
    );
    render(<DemandesPreuvesPanel projectId="p1" onProjectUpdate={vi.fn()} />);
    expect(await screen.findByText("En attente")).toBeTruthy();
    expect(screen.getByText("À relancer")).toBeTruthy();
    expect(screen.getByText("Reçues")).toBeTruthy();
    expect(screen.getByText("Refusées")).toBeTruthy();
  });

  it("alerte quand une demande dépasse le délai de relance", async () => {
    vi.mocked(api.projects.demandesPreuves).mockResolvedValue(
      registre({
        demandes: [demande()],
        synthese: { total: 1, en_attente: 1, recues: 0, refusees: 0, a_relancer: 1,
                    plus_ancienne_jours: 16, delai_relance_jours: 7 },
      }),
    );
    render(<DemandesPreuvesPanel projectId="p1" onProjectUpdate={vi.fn()} />);
    expect(await screen.findByText(/attend une réponse depuis 16 jours/)).toBeTruthy();
  });

  it("ne réclame pas de preuve sur un registre vide mais invite à en ajouter", async () => {
    vi.mocked(api.projects.demandesPreuves).mockResolvedValue(registre());
    render(<DemandesPreuvesPanel projectId="p1" onProjectUpdate={vi.fn()} />);
    expect(await screen.findByText(/Aucune demande enregistrée/)).toBeTruthy();
  });

  it("signale les contrôles conformes sans preuve ni demande", async () => {
    vi.mocked(api.projects.demandesPreuves).mockResolvedValue(
      registre({ controles_sans_justificatif: [
        { referentiel_id: "iso27001", control_id: "ISO-A.5", titre: "Politiques" },
      ] }),
    );
    render(<DemandesPreuvesPanel projectId="p1" onProjectUpdate={vi.fn()} />);
    expect(await screen.findByText(/sans preuve ni/)).toBeTruthy();
    expect(screen.getByText(/ISO-A.5 — Politiques/)).toBeTruthy();
  });

  it("propage la mission mise à jour après un changement de statut", async () => {
    vi.mocked(api.projects.demandesPreuves)
      .mockResolvedValueOnce(registre({ demandes: [demande()],
        synthese: { total: 1, en_attente: 1, recues: 0, refusees: 0, a_relancer: 0,
                    plus_ancienne_jours: 2, delai_relance_jours: 7 } }))
      .mockResolvedValueOnce(registre({ demandes: [demande({ statut: "recue" })],
        synthese: { total: 1, en_attente: 0, recues: 1, refusees: 0, a_relancer: 0,
                    plus_ancienne_jours: null, delai_relance_jours: 7 } }));
    const miseAJour = { id: "p1" } as ProjectState;
    vi.mocked(api.projects.updateDemandePreuve).mockResolvedValue(miseAJour);
    const onUpdate = vi.fn();

    render(<DemandesPreuvesPanel projectId="p1" onProjectUpdate={onUpdate} />);
    const boutonRecue = await screen.findByText("Reçue");
    await act(async () => { fireEvent.click(boutonRecue); });

    await waitFor(() => {
      expect(api.projects.updateDemandePreuve).toHaveBeenCalledWith("p1", "DEM-01", { statut: "recue" });
      expect(onUpdate).toHaveBeenCalledWith(miseAJour);
    });
  });

  it("refuse d'ajouter une demande sans libellé", async () => {
    vi.mocked(api.projects.demandesPreuves).mockResolvedValue(registre());
    render(<DemandesPreuvesPanel projectId="p1" onProjectUpdate={vi.fn()} />);
    const bouton = await screen.findByText("Ajouter");
    await act(async () => { fireEvent.click(bouton); });
    expect(await screen.findByText(/Indiquez le document réclamé/)).toBeTruthy();
    expect(api.projects.addDemandePreuve).not.toHaveBeenCalled();
  });
});
