import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReferentielsPanel } from "./ReferentielsPanel";
import type { Framework, FrameworkDetail } from "../types";

const FRAMEWORKS: Framework[] = [
  { id: "iso27001", name: "ISO/IEC 27001:2022", description: "", requirements_count: 4 },
  { id: "perso", name: "[Perso] Secteur santé", description: "", requirements_count: 2 },
];

function detail(overrides: Partial<FrameworkDetail> = {}): FrameworkDetail {
  return {
    id: "perso",
    name: "Secteur santé",
    description: "Exigences complémentaires",
    requirements: [{ id: "SANTE-01", title: "Hébergeur HDS" }],
    personnel: true,
    ...overrides,
  };
}

function renderPanel(overrides: Partial<Parameters<typeof ReferentielsPanel>[0]> = {}) {
  const props = {
    frameworks: FRAMEWORKS,
    onCharger: vi.fn().mockResolvedValue(detail()),
    onEnregistrer: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
  render(<ReferentielsPanel {...props} />);
  return props;
}

describe("ReferentielsPanel", () => {
  it("rend visible le nombre d'exigences de chaque référentiel", () => {
    renderPanel();
    // Les pastilles d'inventaire portent « Nom · N exigence(s) » ; le même nom
    // figure aussi dans les <option> du sélecteur, d'où le filtrage.
    const pastilles = screen
      .getAllByText(/exigence\(s\)/)
      .filter((n) => n.tagName !== "OPTION");
    expect(pastilles.length).toBeGreaterThan(0);
    const texte = pastilles.map((n) => n.textContent ?? "").join(" ");
    expect(texte).toContain("4");   // ISO 27001 : 4 exigences
    expect(texte).toContain("2");   // référentiel personnel : 2 exigences
  });

  it("rappelle de ne pas recopier le texte des normes (F3)", () => {
    renderPanel();
    expect(screen.getByText(/copyright ISO\/AFNOR/i)).toBeInTheDocument();
    expect(screen.getByText(/intitulé court reformulé/i)).toBeInTheDocument();
  });

  it("charge un référentiel existant pour l'enrichir", async () => {
    const user = userEvent.setup();
    const { onCharger } = renderPanel();

    await user.selectOptions(screen.getByLabelText(/Référentiel à ouvrir/i), "perso");

    expect(onCharger).toHaveBeenCalledWith("perso");
    expect(await screen.findByDisplayValue("Secteur santé")).toBeInTheDocument();
    expect(screen.getByText("SANTE-01")).toBeInTheDocument();
  });

  it("avertit qu'un référentiel livré n'est pas modifiable sous son identifiant", async () => {
    const user = userEvent.setup();
    renderPanel({ onCharger: vi.fn().mockResolvedValue(detail({ id: "iso27001", personnel: false })) });

    await user.selectOptions(screen.getByLabelText(/Référentiel à ouvrir/i), "iso27001");

    expect(await screen.findByText(/livré avec l'application/i)).toBeInTheDocument();
  });

  it("ajoute une exigence à la liste", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.type(screen.getByLabelText(/Identifiant de l'exigence/i), "SANTE-02");
    await user.type(screen.getByLabelText(/Intitulé de l'exigence/i), "Chiffrement des données de santé");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(screen.getByText("SANTE-02")).toBeInTheDocument();
    expect(screen.getByText("Chiffrement des données de santé")).toBeInTheDocument();
  });

  it("refuse une exigence sans identifiant ou sans intitulé", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.type(screen.getByLabelText(/Identifiant de l'exigence/i), "SANTE-02");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(screen.getByText(/besoin d'un identifiant et d'un intitulé/i)).toBeInTheDocument();
  });

  it("refuse une exigence en doublon", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.selectOptions(screen.getByLabelText(/Référentiel à ouvrir/i), "perso");
    await screen.findByText("SANTE-01");

    await user.type(screen.getByLabelText(/Identifiant de l'exigence/i), "SANTE-01");
    await user.type(screen.getByLabelText(/Intitulé de l'exigence/i), "Doublon");
    await user.click(screen.getByRole("button", { name: /ajouter/i }));

    expect(screen.getByText(/existe déjà dans ce référentiel/i)).toBeInTheDocument();
  });

  it("retire une exigence", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.selectOptions(screen.getByLabelText(/Référentiel à ouvrir/i), "perso");
    await screen.findByText("SANTE-01");

    await user.click(screen.getByRole("button", { name: /Retirer l'exigence SANTE-01/i }));

    expect(screen.queryByText("SANTE-01")).not.toBeInTheDocument();
  });

  it("enregistre le référentiel avec ses exigences", async () => {
    const user = userEvent.setup();
    const { onEnregistrer } = renderPanel();

    await user.type(screen.getByLabelText(/Identifiant du référentiel/i), "secteur_sante");
    await user.type(screen.getByLabelText(/Nom du référentiel/i), "Secteur santé");
    await user.type(screen.getByLabelText(/Identifiant de l'exigence/i), "SANTE-01");
    await user.type(screen.getByLabelText(/Intitulé de l'exigence/i), "Hébergeur HDS");
    await user.click(screen.getByRole("button", { name: /^ajouter$/i }));
    await user.click(screen.getByRole("button", { name: /enregistrer le référentiel/i }));

    expect(onEnregistrer).toHaveBeenCalledWith({
      id: "secteur_sante",
      name: "Secteur santé",
      description: "",
      requirements: [{ id: "SANTE-01", title: "Hébergeur HDS", description: "" }],
    });
  });

  it("refuse d'enregistrer sans identifiant ni nom", async () => {
    const user = userEvent.setup();
    const { onEnregistrer } = renderPanel();

    await user.click(screen.getByRole("button", { name: /enregistrer le référentiel/i }));

    expect(onEnregistrer).not.toHaveBeenCalled();
    expect(screen.getByText(/identifiant et un nom sont obligatoires/i)).toBeInTheDocument();
  });

  it("remonte le refus de collision de l'API", async () => {
    const user = userEvent.setup();
    renderPanel({
      onEnregistrer: vi.fn().mockRejectedValue(
        new Error("« iso27001 » est un référentiel livré avec l'application.")),
    });

    await user.type(screen.getByLabelText(/Identifiant du référentiel/i), "iso27001");
    await user.type(screen.getByLabelText(/Nom du référentiel/i), "Ma version");
    await user.click(screen.getByRole("button", { name: /enregistrer le référentiel/i }));

    expect(await screen.findByText(/référentiel livré avec l'application/i)).toBeInTheDocument();
  });
});
