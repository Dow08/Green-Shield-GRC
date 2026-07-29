import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RgpdPanel } from "./RgpdPanel";
import type { EcheanceRgpd } from "../types";

function echeance(overrides: Partial<EcheanceRgpd> = {}): EcheanceRgpd {
  return {
    duree_conservation_mois: 36,
    date_fin_mission: "",
    purge_effectuee_le: "",
    date_purge_prevue: "",
    statut: "mission_en_cours",
    jours_restants: null,
    ...overrides,
  };
}

function renderPanel(overrides: Partial<Parameters<typeof RgpdPanel>[0]> = {}) {
  const props = {
    echeance: echeance(),
    donneesPersonnelles: 4,
    onEnregistrer: vi.fn().mockResolvedValue(undefined),
    onPurger: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
  render(<RgpdPanel {...props} />);
  return props;
}

describe("RgpdPanel", () => {
  it("rappelle au consultant qu'il est responsable de traitement", () => {
    renderPanel();
    expect(screen.getByText(/responsable de traitement/i)).toBeInTheDocument();
  });

  it("compte les enregistrements identifiants restants", () => {
    renderPanel();
    expect(screen.getByText(/4 enregistrement\(s\) identifiant\(s\)/i)).toBeInTheDocument();
  });

  it("explique que le délai ne court qu'à partir de la fin de mission", () => {
    renderPanel();
    expect(screen.getByText(/le délai courra à partir de la date de fin/i)).toBeInTheDocument();
  });

  it("affiche l'échéance calculée quand la mission est terminée", () => {
    renderPanel({
      echeance: echeance({ statut: "en_conservation", date_fin_mission: "2026-06-30",
                           date_purge_prevue: "2029-06-30", jours_restants: 900 }),
    });
    expect(screen.getByText("2029-06-30")).toBeInTheDocument();
  });

  it("signale visiblement une échéance dépassée", () => {
    renderPanel({
      echeance: echeance({ statut: "echue", date_purge_prevue: "2025-01-01", jours_restants: -400 }),
    });
    expect(screen.getByText(/purge attendue/i)).toBeInTheDocument();
  });

  it("enregistre la politique de conservation saisie", async () => {
    const user = userEvent.setup();
    const { onEnregistrer } = renderPanel();

    const duree = screen.getByLabelText(/Durée de conservation en mois/i);
    await user.clear(duree);
    await user.type(duree, "24");
    await user.type(screen.getByLabelText(/Date de fin de mission/i), "2026-06-30");
    await user.click(screen.getByRole("button", { name: /enregistrer/i }));

    expect(onEnregistrer).toHaveBeenCalledWith({
      duree_conservation_mois: 24,
      date_fin_mission: "2026-06-30",
    });
  });

  it("refuse une durée hors bornes sans appeler l'API", async () => {
    const user = userEvent.setup();
    const { onEnregistrer } = renderPanel();

    const duree = screen.getByLabelText(/Durée de conservation en mois/i);
    await user.clear(duree);
    await user.type(duree, "999");
    await user.click(screen.getByRole("button", { name: /enregistrer/i }));

    expect(onEnregistrer).not.toHaveBeenCalled();
    expect(screen.getByText(/entre 1 et 120/i)).toBeInTheDocument();
  });

  it("demande confirmation avant de purger", async () => {
    const user = userEvent.setup();
    const { onPurger } = renderPanel();

    await user.click(screen.getByRole("button", { name: /purger les données personnelles/i }));

    expect(onPurger).not.toHaveBeenCalled();
    expect(screen.getByText(/Effacer définitivement les 4/i)).toBeInTheDocument();
  });

  it("purge après confirmation", async () => {
    const user = userEvent.setup();
    const { onPurger } = renderPanel();

    await user.click(screen.getByRole("button", { name: /purger les données personnelles/i }));
    await user.click(screen.getByRole("button", { name: /confirmer la purge/i }));

    expect(onPurger).toHaveBeenCalled();
  });

  it("désactive la purge quand il n'y a plus rien à effacer", () => {
    renderPanel({ donneesPersonnelles: 0 });
    expect(screen.getByRole("button", { name: /purger les données personnelles/i })).toBeDisabled();
  });

  it("précise que les constats d'audit sont conservés", () => {
    renderPanel();
    expect(screen.getByText(/jamais les constats d'audit/i)).toBeInTheDocument();
  });

  it("remonte l'erreur de l'API sans masquer l'échec", async () => {
    const user = userEvent.setup();
    renderPanel({ onPurger: vi.fn().mockRejectedValue(new Error("Projet introuvable")) });

    await user.click(screen.getByRole("button", { name: /purger les données personnelles/i }));
    await user.click(screen.getByRole("button", { name: /confirmer la purge/i }));

    expect(await screen.findByText("Projet introuvable")).toBeInTheDocument();
  });
});
