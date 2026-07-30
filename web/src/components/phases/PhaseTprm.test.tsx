import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PhaseTprm } from "./PhaseTprm";
import { api } from "../../lib/api";
import type { ProjectState, Tiers } from "../../types";

vi.mock("../../lib/api", () => ({
  api: {
    projects: {
      addTiers: vi.fn(),
      setExigenceTiers: vi.fn(),
      recalculerTprm: vi.fn(),
    },
  },
}));

const AWS: Tiers = {
  name: "Hébergeur Cloud (AWS)", dependence: 5, penetration: 5, maturity: 4, trust: 4,
  score: 1.56, rating: "Moyen", methode: "ratio_anssi",
};
const ESN: Tiers = {
  name: "Prestataire Infogérance (ESN)", dependence: 4, penetration: 5, maturity: 3, trust: 3,
  score: 2.22, rating: "Élevé", methode: "ratio_anssi",
};

function mission(type: "consulting" | "grc", tiers: Tiers[]): ProjectState {
  return {
    id: "m1", name: "Mission", client: "ACME", type, status: "en_cours",
    progress: 40, created_at: "", updated_at: "",
    steps: { tprm: { tiers } },
  } as unknown as ProjectState;
}

function renderPhase(projet: ProjectState) {
  const props = {
    activeProject: projet,
    updateStepData: vi.fn(),
    handleSaveProject: vi.fn(),
    onProjectReplaced: vi.fn(),
  };
  render(<PhaseTprm {...props} />);
  return props;
}

beforeEach(() => vi.clearAllMocks());

describe("PhaseTprm — volet Consulting", () => {
  it("affiche le ratio et le niveau de chaque tiers", () => {
    renderPhase(mission("consulting", [AWS, ESN]));
    expect(screen.getByText(/Moyen \(ratio 1\.56\)/)).toBeInTheDocument();
    expect(screen.getByText(/Élevé \(ratio 2\.22\)/)).toBeInTheDocument();
  });

  it("annonce la formule ANSSI plutôt qu'une moyenne", () => {
    renderPhase(mission("consulting", []));
    expect(screen.getByText(/dépendance × pénétration\) \/ \(maturité × confiance\)/i)).toBeInTheDocument();
  });

  it("n'envoie que les curseurs au serveur, jamais un score", async () => {
    const user = userEvent.setup();
    const projet = mission("consulting", []);
    vi.mocked(api.projects.addTiers).mockResolvedValue(mission("consulting", [AWS]));
    renderPhase(projet);

    await user.type(screen.getByLabelText(/Nom du tiers/i), "Nouveau tiers");
    await user.click(screen.getByRole("button", { name: /Enregistrer et évaluer/i }));

    expect(api.projects.addTiers).toHaveBeenCalledWith("m1", {
      name: "Nouveau tiers", dependence: 3, penetration: 3, maturity: 3, trust: 3,
    });
    const envoye = vi.mocked(api.projects.addTiers).mock.calls[0][1];
    expect(envoye).not.toHaveProperty("score");
    expect(envoye).not.toHaveProperty("rating");
  });

  it("remplace la mission par celle que renvoie le serveur", async () => {
    const user = userEvent.setup();
    const apres = mission("consulting", [AWS]);
    vi.mocked(api.projects.addTiers).mockResolvedValue(apres);
    const { onProjectReplaced } = renderPhase(mission("consulting", []));

    await user.type(screen.getByLabelText(/Nom du tiers/i), "AWS");
    await user.click(screen.getByRole("button", { name: /Enregistrer et évaluer/i }));

    await waitFor(() => expect(onProjectReplaced).toHaveBeenCalledWith(apres));
  });

  it("n'appelle pas le serveur sans nom de tiers", async () => {
    const user = userEvent.setup();
    renderPhase(mission("consulting", []));
    await user.click(screen.getByRole("button", { name: /Enregistrer et évaluer/i }));
    expect(api.projects.addTiers).not.toHaveBeenCalled();
  });

  it("affiche l'erreur renvoyée par le serveur au lieu d'échouer en silence", async () => {
    const user = userEvent.setup();
    vi.mocked(api.projects.addTiers).mockRejectedValue(new Error("Le nom du tiers est obligatoire."));
    renderPhase(mission("consulting", []));

    await user.type(screen.getByLabelText(/Nom du tiers/i), "X");
    await user.click(screen.getByRole("button", { name: /Enregistrer et évaluer/i }));

    expect(await screen.findByText(/Le nom du tiers est obligatoire/)).toBeInTheDocument();
  });
});

describe("PhaseTprm — migration au ratio ANSSI", () => {
  const ancien: Tiers = { ...ESN, score: 3.75, methode: "moyenne_historique" };

  it("signale les tiers encore notés à l'ancienne méthode", () => {
    renderPhase(mission("consulting", [AWS, ancien]));
    expect(screen.getByText(/1 tiers est noté selon l'ancienne moyenne/)).toBeInTheDocument();
    expect(screen.getByText(/ancienne méthode/)).toBeInTheDocument();
  });

  it("prévient que le recalcul modifiera la criticité déjà présentée", () => {
    renderPhase(mission("consulting", [ancien]));
    expect(screen.getByText(/un instantané est pris avant/i)).toBeInTheDocument();
  });

  it("ne recalcule rien tant que le consultant ne le demande pas", () => {
    renderPhase(mission("consulting", [ancien]));
    expect(api.projects.recalculerTprm).not.toHaveBeenCalled();
    expect(screen.getByText(/Élevé \(ratio 3\.75\)/)).toBeInTheDocument();
  });

  it("recalcule sur action explicite", async () => {
    const user = userEvent.setup();
    const apres = mission("consulting", [ESN]);
    vi.mocked(api.projects.recalculerTprm).mockResolvedValue({ status: "ok", recalcules: 1, state: apres });
    const { onProjectReplaced } = renderPhase(mission("consulting", [ancien]));

    await user.click(screen.getByRole("button", { name: /Recalculer au ratio ANSSI/i }));

    expect(api.projects.recalculerTprm).toHaveBeenCalledWith("m1");
    await waitFor(() => expect(onProjectReplaced).toHaveBeenCalledWith(apres));
  });

  it("n'affiche aucun bandeau quand tous les tiers sont à jour", () => {
    renderPhase(mission("consulting", [AWS, ESN]));
    expect(screen.queryByRole("button", { name: /Recalculer/i })).not.toBeInTheDocument();
  });
});

describe("PhaseTprm — volet GRC", () => {
  const exigences = [
    { id: "DORA-28.3", libelle: "Inscrit au registre d'information (DORA Art. 28.3)", satisfait: true, preuve: "" },
    { id: "DORA-30", libelle: "Clauses contractuelles obligatoires signées (DORA Art. 30)", satisfait: false, preuve: "" },
  ];
  const prestataire: Tiers = { ...AWS, exigences };

  it("n'affiche aucun score de risque", () => {
    renderPhase(mission("grc", [prestataire]));
    expect(screen.queryByText(/ratio 1\.56/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Moyen \(/)).not.toBeInTheDocument();
  });

  it("explique que la conformité se démontre par des preuves, pas par une note", () => {
    renderPhase(mission("grc", []));
    expect(screen.getByText(/ne produit pas de score de risque/i)).toBeInTheDocument();
  });

  it("affiche les exigences DORA du tiers", () => {
    renderPhase(mission("grc", [prestataire]));
    expect(screen.getByText(/registre d'information \(DORA Art. 28.3\)/)).toBeInTheDocument();
    expect(screen.getByText(/Clauses contractuelles obligatoires signées/)).toBeInTheDocument();
  });

  it("bascule une exigence via le serveur", async () => {
    const user = userEvent.setup();
    vi.mocked(api.projects.setExigenceTiers).mockResolvedValue(mission("grc", [prestataire]));
    renderPhase(mission("grc", [prestataire]));

    await user.click(screen.getByRole("checkbox", { name: /Clauses contractuelles/i }));

    expect(api.projects.setExigenceTiers).toHaveBeenCalledWith("m1", 0, "DORA-30", {
      satisfait: true, preuve: "",
    });
  });

  it("décoche une exigence déjà satisfaite", async () => {
    const user = userEvent.setup();
    vi.mocked(api.projects.setExigenceTiers).mockResolvedValue(mission("grc", [prestataire]));
    renderPhase(mission("grc", [prestataire]));

    await user.click(screen.getByRole("checkbox", { name: /registre d'information/i }));

    expect(api.projects.setExigenceTiers).toHaveBeenCalledWith("m1", 0, "DORA-28.3", {
      satisfait: false, preuve: "",
    });
  });

  it("compte les prestataires sans écart, pas une criticité", () => {
    const conforme: Tiers = { ...AWS, name: "Conforme", exigences: exigences.map((e) => ({ ...e, satisfait: true })) };
    renderPhase(mission("grc", [prestataire, conforme]));
    expect(screen.getByText(/1 \/ 2 prestataire\(s\) sans écart/)).toBeInTheDocument();
  });

  it("ne propose jamais de recalcul sur ce volet", () => {
    const ancien: Tiers = { ...prestataire, methode: "moyenne_historique" };
    renderPhase(mission("grc", [ancien]));
    expect(screen.queryByRole("button", { name: /Recalculer/i })).not.toBeInTheDocument();
  });
});
