import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ObligationsAIPD } from "./ObligationsAIPD";
import { api } from "../lib/api";
import type { AIPDData, ReferenceObligationAIPD } from "../types";

vi.mock("../lib/api", () => ({
  api: { aipd: { obligations: vi.fn() } },
}));

const REFERENCE: ReferenceObligationAIPD[] = [
  { id: "DPO", libelle: "Avis du délégué à la protection des données recueilli",
    reference: "RGPD Art. 35 §2", aide: "Obligatoire dès qu'un DPO est désigné.", conditionnelle: false },
  { id: "PERSONNES", libelle: "Avis des personnes concernées recueilli",
    reference: "RGPD Art. 35 §9", aide: "À solliciter le cas échéant.", conditionnelle: false },
  { id: "ART36", libelle: "Consultation préalable de la CNIL avant mise en œuvre",
    reference: "RGPD Art. 36 §1", aide: "Due si un risque résiduel élevé subsiste.", conditionnelle: true },
];

function aipd(overrides: Partial<AIPDData> = {}): AIPDData {
  return {
    treatment_description: "", necessity_eval: "", risks_eval: "", mitigation_measures: "",
    risque_residuel: "acceptable",
    obligations: [{ id: "DPO", satisfait: false, commentaire: "" }],
    ...overrides,
  };
}

function renderObligations(donnees: AIPDData = aipd()) {
  const onChange = vi.fn();
  render(<ObligationsAIPD aipd={donnees} onChange={onChange} />);
  return onChange;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.aipd.obligations).mockResolvedValue(REFERENCE);
});

describe("ObligationsAIPD", () => {
  it("lit les intitulés depuis l'API plutôt que d'en tenir une copie", async () => {
    renderObligations();
    expect(await screen.findByText(/délégué à la protection des données/i)).toBeInTheDocument();
    expect(api.aipd.obligations).toHaveBeenCalled();
  });

  it("affiche l'article de référence de chaque obligation", async () => {
    renderObligations();
    expect(await screen.findByText(/RGPD Art. 35 §2/)).toBeInTheDocument();
  });

  it("coche une obligation sans toucher aux autres", async () => {
    const user = userEvent.setup();
    const onChange = renderObligations();
    await screen.findByText(/délégué à la protection/i);

    await user.click(screen.getByRole("checkbox", { name: /délégué à la protection/i }));

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        obligations: [{ id: "DPO", satisfait: true, commentaire: "" }],
      }),
    );
  });

  it("crée l'entrée d'une obligation encore absente de la mission", async () => {
    const user = userEvent.setup();
    const onChange = renderObligations(aipd({ obligations: [] }));
    await screen.findByText(/personnes concernées/i);

    await user.click(screen.getByRole("checkbox", { name: /personnes concernées/i }));

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        obligations: [{ id: "PERSONNES", satisfait: true, commentaire: "" }],
      }),
    );
  });

  it("consigne le commentaire de preuve", async () => {
    const user = userEvent.setup();
    const onChange = renderObligations();
    await screen.findByText(/délégué à la protection/i);

    await user.type(screen.getByLabelText(/Commentaire — Avis du délégué/i), "A");

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        obligations: [{ id: "DPO", satisfait: false, commentaire: "A" }],
      }),
    );
  });

  it("qualifie le risque résiduel sans le déduire", async () => {
    const user = userEvent.setup();
    const onChange = renderObligations();

    await user.selectOptions(screen.getByLabelText(/Risque résiduel/i), "eleve");

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ risque_residuel: "eleve" }));
  });

  it("neutralise la consultation CNIL tant que le risque n'est pas élevé", async () => {
    renderObligations(aipd({ risque_residuel: "acceptable" }));
    await screen.findByText(/délégué à la protection/i);

    expect(screen.getByRole("checkbox", { name: /CNIL avant mise en œuvre/i })).toBeDisabled();
    expect(screen.getByText(/Non applicable tant que le risque résiduel/i)).toBeInTheDocument();
  });

  it("active la consultation CNIL sur risque résiduel élevé", async () => {
    renderObligations(aipd({ risque_residuel: "eleve" }));
    await screen.findByText(/CNIL avant mise en œuvre/i);

    expect(screen.getByRole("checkbox", { name: /CNIL avant mise en œuvre/i })).toBeEnabled();
  });

  it("avertit qu'un risque élevé non soumis interdit la mise en œuvre", async () => {
    renderObligations(aipd({ risque_residuel: "eleve" }));
    expect(await screen.findByText(/ne peut pas être mis en œuvre avant consultation/i)).toBeInTheDocument();
  });

  it("lève l'avertissement une fois la CNIL consultée", async () => {
    renderObligations(aipd({
      risque_residuel: "eleve",
      obligations: [{ id: "ART36", satisfait: true, commentaire: "Saisine du 04/07" }],
    }));
    await screen.findByText(/CNIL avant mise en œuvre/i);

    expect(screen.queryByText(/ne peut pas être mis en œuvre/i)).not.toBeInTheDocument();
  });

  it("ne compte pas l'obligation non exigible dans l'avancement", async () => {
    renderObligations(aipd({ risque_residuel: "acceptable" }));
    expect(await screen.findByText("0 / 2 traitée(s)")).toBeInTheDocument();
  });

  it("compte l'obligation conditionnelle dès qu'elle est due", async () => {
    renderObligations(aipd({ risque_residuel: "eleve" }));
    expect(await screen.findByText("0 / 3 traitée(s)")).toBeInTheDocument();
  });

  it("signale un référentiel indisponible au lieu d'afficher une liste vide", async () => {
    vi.mocked(api.aipd.obligations).mockRejectedValue(new Error("réseau"));
    renderObligations();
    expect(await screen.findByText(/Référentiel des obligations indisponible/i)).toBeInTheDocument();
  });
});
