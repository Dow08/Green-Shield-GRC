import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ArchivePanel } from "./ArchivePanel";

function renderPanel(overrides: Partial<Parameters<typeof ArchivePanel>[0]> = {}) {
  const props = {
    missionName: "Acme",
    onExport: vi.fn().mockResolvedValue(undefined),
    onImport: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
  render(<ArchivePanel {...props} />);
  return props;
}

describe("ArchivePanel", () => {
  it("nomme la mission concernée par l'export", () => {
    renderPanel();
    expect(screen.getByText(/Exporter « Acme »/)).toBeInTheDocument();
  });

  it("exporte avec le mot de passe saisi", async () => {
    const user = userEvent.setup();
    const { onExport } = renderPanel();

    await user.type(screen.getByLabelText(/Mot de passe de chiffrement/i), "motdepasse123");
    await user.click(screen.getByRole("button", { name: /exporter l'archive/i }));

    expect(onExport).toHaveBeenCalledWith("motdepasse123");
  });

  it("refuse un mot de passe trop court sans appeler l'API", async () => {
    const user = userEvent.setup();
    const { onExport } = renderPanel();

    await user.type(screen.getByLabelText(/Mot de passe de chiffrement/i), "court");
    await user.click(screen.getByRole("button", { name: /exporter l'archive/i }));

    expect(onExport).not.toHaveBeenCalled();
    expect(screen.getByText(/au moins 8 caractères/i)).toBeInTheDocument();
  });

  it("rappelle après export que le mot de passe est indispensable", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.type(screen.getByLabelText(/Mot de passe de chiffrement/i), "motdepasse123");
    await user.click(screen.getByRole("button", { name: /exporter l'archive/i }));

    expect(await screen.findByText(/Conservez le mot de passe/i)).toBeInTheDocument();
  });

  it("affiche le message d'erreur métier renvoyé par l'API", async () => {
    const user = userEvent.setup();
    renderPanel({ onExport: vi.fn().mockRejectedValue(new Error("Mot de passe incorrect")) });

    await user.type(screen.getByLabelText(/Mot de passe de chiffrement/i), "motdepasse123");
    await user.click(screen.getByRole("button", { name: /exporter l'archive/i }));

    expect(await screen.findByText("Mot de passe incorrect")).toBeInTheDocument();
  });

  it("refuse d'importer sans fichier sélectionné", async () => {
    const user = userEvent.setup();
    const { onImport } = renderPanel();

    await user.click(screen.getByRole("button", { name: /restaurer/i }));

    expect(onImport).not.toHaveBeenCalled();
    expect(screen.getByText(/Sélectionnez une archive/i)).toBeInTheDocument();
  });

  it("importe le fichier choisi avec son mot de passe", async () => {
    const user = userEvent.setup();
    const { onImport } = renderPanel();

    const fichier = new File(["PK"], "mission_acme.zip", { type: "application/zip" });
    await user.upload(screen.getByLabelText(/Fichier archive à sélectionner/i), fichier);
    await user.type(screen.getByLabelText(/Mot de passe de déchiffrement/i), "secret123");
    await user.click(screen.getByRole("button", { name: /restaurer/i }));

    expect(onImport).toHaveBeenCalledWith(fichier, "secret123");
  });

  it("confirme la restauration réussie", async () => {
    const user = userEvent.setup();
    renderPanel();

    const fichier = new File(["PK"], "m.zip", { type: "application/zip" });
    await user.upload(screen.getByLabelText(/Fichier archive à sélectionner/i), fichier);
    await user.click(screen.getByRole("button", { name: /restaurer/i }));

    expect(await screen.findByText(/Mission restaurée/i)).toBeInTheDocument();
  });

  it("annonce explicitement que l'archive est chiffrée", () => {
    renderPanel();
    expect(screen.getByText(/chiffrée en AES-256/i)).toBeInTheDocument();
  });
});
