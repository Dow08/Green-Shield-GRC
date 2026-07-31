import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CopilotGRC } from "./CopilotGRC";
import type { CopilotContext } from "../types";

function contextFixture(overrides: Partial<CopilotContext> = {}): CopilotContext {
  return {
    total_projects: 2,
    by_type: { grc: 1, consulting: 1 },
    avg_progress: 42,
    tiers_critiques: [
      { project: "Acme", project_id: "acme", tiers_name: "Infogéreur X", score: 4.5, rating: "Critique" },
    ],
    redoute_events: [
      { project: "Acme", project_id: "acme", event: "Ransomware sur SI production", gravity: 4 },
    ],
    non_conformites: [
      { project: "Acme", project_id: "acme", control: "PermitRootLogin activé", severity: "Critique" },
    ],
    quick_wins_en_attente: 3,
    ...overrides,
  };
}

function mockFetch(context: CopilotContext, askResponse?: any) {
  return vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/copilot/context") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(context) } as Response);
    }
    if (url === "/api/copilot/ask" && init?.method === "POST") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(askResponse) } as Response);
    }
    return Promise.reject(new Error(`URL non mockée : ${url}`));
  });
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe("CopilotGRC", () => {
  it("affiche les KPI agrégés réels sans en inventer", async () => {
    globalThis.fetch = mockFetch(contextFixture()) as any;
    render(<CopilotGRC onNavigate={vi.fn()} />);

    await waitFor(() => expect(screen.getByText("2")).toBeInTheDocument()); // total_projects
    expect(screen.getByText("1 / 1")).toBeInTheDocument(); // by_type
    expect(screen.getByText("42%")).toBeInTheDocument();
  });

  it("liste les tiers critiques réels et pas de contenu fantôme quand la liste est vide", async () => {
    globalThis.fetch = mockFetch(contextFixture({ tiers_critiques: [] })) as any;
    render(<CopilotGRC onNavigate={vi.fn()} />);

    await waitFor(() => expect(screen.getByText(/Aucun tiers Critique\/Élevé/i)).toBeInTheDocument());
  });

  it("affiche les tiers critiques quand ils existent", async () => {
    globalThis.fetch = mockFetch(contextFixture()) as any;
    render(<CopilotGRC onNavigate={vi.fn()} />);

    await waitFor(() => expect(screen.getByText("Infogéreur X")).toBeInTheDocument());
    expect(screen.getByText("Ransomware sur SI production")).toBeInTheDocument();
    expect(screen.getByText("PermitRootLogin activé")).toBeInTheDocument();
  });

  it("navigue vers le registre de missions au clic sur une priorité", async () => {
    const onNavigate = vi.fn();
    globalThis.fetch = mockFetch(contextFixture()) as any;
    const user = userEvent.setup();
    render(<CopilotGRC onNavigate={onNavigate} />);

    await waitFor(() => screen.getByText("Infogéreur X"));
    await user.click(screen.getByText("Infogéreur X").closest("button")!);
    expect(onNavigate).toHaveBeenCalledWith("missions");
  });

  it("interroge le copilote et affiche la réponse avec le badge de source hors-ligne", async () => {
    globalThis.fetch = mockFetch(contextFixture(), {
      status: "success",
      response: "### Synthèse\n1. Traiter Infogéreur X",
      source: "offline",
    }) as any;
    const user = userEvent.setup();
    render(<CopilotGRC onNavigate={vi.fn()} />);

    await waitFor(() => screen.getByText("Infogéreur X"));
    await user.type(screen.getByPlaceholderText(/priorités cette semaine/i), "priorise mes risques");
    await user.click(screen.getByRole("button", { name: /demander au copilote/i }));

    await waitFor(() => expect(screen.getByText(/Traiter Infogéreur X/)).toBeInTheDocument());
    expect(screen.getByText("Hors-ligne — intelligence locale")).toBeInTheDocument();
  });

  it("transmet la clé API sauvegardée dans les Réglages à l'appel du copilote", async () => {
    sessionStorage.setItem("copilot_api_key", "ma-cle-secrete");
    const fetchMock = mockFetch(contextFixture(), { status: "success", response: "ok", source: "online" });
    globalThis.fetch = fetchMock as any;
    const user = userEvent.setup();
    render(<CopilotGRC onNavigate={vi.fn()} />);

    await waitFor(() => screen.getByText("Infogéreur X"));
    await user.type(screen.getByPlaceholderText(/priorités cette semaine/i), "test");
    await user.click(screen.getByRole("button", { name: /demander au copilote/i }));

    await waitFor(() => {
      const askCall = fetchMock.mock.calls.find(([url]) => url === "/api/copilot/ask");
      expect(askCall).toBeDefined();
      const body = JSON.parse((askCall as any)[1].body);
      expect(body.key).toBe("ma-cle-secrete");
    });
  });
});
