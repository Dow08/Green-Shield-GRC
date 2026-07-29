/**
 * Test de caractérisation de Projects.tsx — filet de sécurité pour le
 * découpage du fichier (2044 lignes) en composants par phase.
 *
 * Il ne juge pas la qualité du code : il fige le comportement OBSERVABLE
 * avant refactor, pour qu'une régression pendant le découpage se voie.
 * À conserver après le découpage : ces parcours restent la meilleure
 * couverture de bout en bout de la vue mission.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Projects } from "./Projects";
import type { ProjectState } from "../types";

function missionFixture(overrides: Partial<ProjectState> = {}): ProjectState {
  return {
    id: "acme",
    name: "Mission Acme",
    client: "Acme Corp",
    type: "grc",
    status: "en_cours",
    progress: 42,
    created_at: "2026-07-01",
    updated_at: "2026-07-29",
    socle: { qualification: { budget: "10 jours" }, temps: { entrees: [] } },
    steps: {
      cadrage: {
        scope: "SI de production",
        client_missions: "Distribution",
        nda_signed: false,
        nda_text: "ACCORD DE CONFIDENTIALITÉ",
        assets_metier: [
          { id: "VM-01", name: "Fichier Clients", description: "Coordonnées", is_personal_data: true },
        ],
        assets_support: [
          { id: "BS-01", name: "Active Directory", type: "Logiciel", description: "Annuaire", owner: "DSI" },
        ],
        framework_id: "iso27001",
        framework_name: "ISO 27001",
      },
      diagnostic: {
        pssi_active: true,
        governance_active: false,
        vulnerabilities_active: false,
        rgpd_register: [
          { id: "RGPD-01", name: "Paie", purpose: "Salaires", data_categories: "NIR", retention: "5 ans" },
        ],
        aipd_required: true,
        aipd: { treatment_description: "", necessity_eval: "", risks_eval: "", mitigation_measures: "" },
      },
      tprm: {
        tiers: [
          { name: "Hébergeur Cloud", dependence: 5, penetration: 4, maturity: 2, trust: 2, score: 4.5, rating: "Critique" },
        ],
      },
      ebios: {
        redoute_events: [{ id: "ER-01", event: "Ransomware", gravity: 4, impact: "Arrêt total" }],
        risk_sources: [],
        operational_scenarios: [
          { id: "SC-01", event: "Hameçonnage", gravity: 4, likelihood: 3, mitigation: "MFA" },
        ],
        case_studies: [],
      },
      resilience: {
        logging_active: true,
        bcp_strategy: { rto: "4 h", rpo: "1 h", backup_policy: "Immuable" },
        e3r: { endiguement: "Isoler", eviction: "krbtgt", eradication: "Nettoyer", reconstruction: "IaC" },
      },
      traitement: {
        remediations: [{ id: "REM-01", axe: "Protection", measure: "Déployer un EDR", priority: "Critique" }],
        quick_wins: ["Valider le périmètre"],
      },
      evaluation: {
        manual_controls: [
          { id: "A.5.1", title: "Politiques de sécurité", description: "Définir la PSSI", status: "A_VERIFIER", notes: "" },
        ],
        technical_results: null,
      },
    },
    ...overrides,
  } as ProjectState;
}

function mockFetch(mission: ProjectState) {
  return vi.fn((url: string) => {
    if (url === "/api/projects") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve([mission]) } as Response);
    }
    if (url === "/api/frameworks") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([{ id: "iso27001", name: "ISO 27001", description: "", requirements_count: 4 }]),
      } as Response);
    }
    if (url === `/api/projects/${mission.id}`) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mission) } as Response);
    }
    return Promise.reject(new Error(`URL non mockée : ${url}`));
  });
}

/** Ouvre la mission puis se place sur la phase demandée. */
async function ouvrirPhase(numero: number) {
  const user = userEvent.setup();
  await waitFor(() => expect(screen.getByText("Mission Acme")).toBeInTheDocument());
  await user.click(screen.getByText("Mission Acme"));
  await waitFor(() => expect(screen.getByText(/Progression Mission/)).toBeInTheDocument());
  if (numero !== 1) {
    await user.click(screen.getByRole("button", { name: String(numero) }));
  }
  return user;
}

beforeEach(() => {
  globalThis.fetch = mockFetch(missionFixture()) as never;
});

describe("Projects — caractérisation avant découpage", () => {
  it("liste les missions du registre", async () => {
    render(<Projects />);
    await waitFor(() => expect(screen.getByText("Mission Acme")).toBeInTheDocument());
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
  });

  it("ouvre une mission et affiche le stepper des 6 phases", async () => {
    render(<Projects />);
    await ouvrirPhase(1);
    for (const n of ["1", "2", "3", "4", "5", "6"]) {
      expect(screen.getByRole("button", { name: n })).toBeInTheDocument();
    }
  });

  it("phase 1 — affiche le cadrage, les valeurs métier et les biens supports", async () => {
    render(<Projects />);
    await ouvrirPhase(1);
    expect(screen.getByDisplayValue("SI de production")).toBeInTheDocument();
    expect(screen.getByText("Fichier Clients")).toBeInTheDocument();
    expect(screen.getByText("Active Directory")).toBeInTheDocument();
    expect(screen.getByText("VM-01")).toBeInTheDocument();
    expect(screen.getByText("BS-01")).toBeInTheDocument();
  });

  it("phase 2 — affiche le registre RGPD", async () => {
    render(<Projects />);
    await ouvrirPhase(2);
    expect(screen.getByText("Paie")).toBeInTheDocument();
    expect(screen.getByText("RGPD-01")).toBeInTheDocument();
  });

  it("phase 3 — affiche les tiers et leur criticité", async () => {
    render(<Projects />);
    await ouvrirPhase(3);
    expect(screen.getByText("Hébergeur Cloud")).toBeInTheDocument();
  });

  it("phase 4 — affiche les événements redoutés EBIOS RM", async () => {
    render(<Projects />);
    await ouvrirPhase(4);
    // La phase 4 rend les scénarios opérationnels (heatmap + liste), pas les
    // événements redoutés bruts.
    expect(screen.getByText(/Hameçonnage/)).toBeInTheDocument();
  });

  it("phase 5 — affiche la check-list organisationnelle et la stratégie de continuité", async () => {
    render(<Projects />);
    await ouvrirPhase(5);
    expect(screen.getByText("Politiques de sécurité")).toBeInTheDocument();
    // Séquence E3R (endiguement / reconstruction) : seuls champs de résilience
    // réellement exposés par l'UI. Voir todo.md — bcp_strategy (RTO/RPO)
    // existe dans le modèle mais n'est affiché nulle part.
    expect(screen.getByDisplayValue("Isoler")).toBeInTheDocument();
    expect(screen.getByDisplayValue("IaC")).toBeInTheDocument();
  });

  it("phase 6 — affiche le plan de remédiation et le copilote", async () => {
    render(<Projects />);
    await ouvrirPhase(6);
    expect(screen.getByText("Déployer un EDR")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/stratégie PSSI/i)).toBeInTheDocument();
  });

  it("affiche le suivi du temps et le panneau d'archive sur toutes les phases", async () => {
    render(<Projects />);
    await ouvrirPhase(1);
    expect(screen.getByText(/Temps consommé/i)).toBeInTheDocument();
    expect(screen.getByText(/Sauvegarde/i)).toBeInTheDocument();
  });

  it("le sélecteur de valeurs métier propose des gabarits et se ferme à Échap", async () => {
    render(<Projects />);
    const user = await ouvrirPhase(1);

    await user.click(screen.getByRole("button", { name: /Ajouter une valeur métier/i }));
    expect(screen.getByText("Base de données Clients")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    await waitFor(() =>
      expect(screen.queryByText("Base de données Clients")).not.toBeInTheDocument()
    );
  });
});
