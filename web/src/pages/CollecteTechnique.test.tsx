import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CollecteTechnique } from "./CollecteTechnique";
import type { FingerprintResult, ProjectState } from "../types";

function projectFixture(): ProjectState[] {
  return [
    {
      id: "acme", name: "Acme", client: "Acme Corp", type: "grc", status: "en_cours",
      progress: 25, created_at: "2026-07-28", updated_at: "2026-07-28",
      steps: {} as any,
    } as ProjectState,
  ];
}

function fingerprintFixture(): FingerprintResult {
  return {
    filename: "sshd_config",
    detected_type: "sshd_config",
    service: "Service SSH (OpenSSH)",
    version: null,
    directive_count: 3,
    flags: ["PermitRootLogin yes", "PasswordAuthentication yes"],
    suggested_asset: {
      name: "Serveur SSH (OpenSSH)",
      type: "Réseau",
      description: "Accès distant administrateur — 3 directive(s) relevée(s) dans sshd_config.",
      owner: "",
    },
  };
}

function mockFetch(opts: { projects?: ProjectState[]; fingerprint?: FingerprintResult; importedState?: ProjectState }) {
  return vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/projects") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(opts.projects ?? []) } as unknown as Response);
    }
    if (url === "/api/collecte/fingerprint" && init?.method === "POST") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(opts.fingerprint) } as unknown as Response);
    }
    if (url === "/api/projects/acme/collecte/import" && init?.method === "POST") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(opts.importedState ?? {}) } as unknown as Response);
    }
    return Promise.reject(new Error(`URL non mockée : ${url}`));
  });
}

describe("CollecteTechnique", () => {
  it("lance une empreinte et affiche le résultat factuel relevé", async () => {
    globalThis.fetch = mockFetch({ projects: projectFixture(), fingerprint: fingerprintFixture() }) as any;
    const user = userEvent.setup();
    render(<CollecteTechnique />);

    await user.type(screen.getByPlaceholderText(/collez ici/i), "Port 22\nPermitRootLogin yes\n");
    await user.click(screen.getByRole("button", { name: /lancer l'empreinte/i }));

    await waitFor(() => expect(screen.getByText("Service SSH (OpenSSH)")).toBeInTheDocument());
    expect(screen.getByText("PermitRootLogin yes")).toBeInTheDocument();
    const summaryPanel = screen.getByText("Service SSH (OpenSSH)").closest("div")!.parentElement!;
    expect(summaryPanel).toHaveTextContent("3 directive(s)/champ(s) relevé(s)");
  });

  it("ne permet pas de lancer une empreinte sans contenu", async () => {
    globalThis.fetch = mockFetch({ projects: projectFixture() }) as any;
    render(<CollecteTechnique />);
    expect(screen.getByRole("button", { name: /lancer l'empreinte/i })).toBeDisabled();
  });

  it("pré-remplit le formulaire d'import avec l'actif suggéré par l'empreinte", async () => {
    globalThis.fetch = mockFetch({ projects: projectFixture(), fingerprint: fingerprintFixture() }) as any;
    const user = userEvent.setup();
    render(<CollecteTechnique />);

    await user.type(screen.getByPlaceholderText(/collez ici/i), "Port 22\n");
    await user.click(screen.getByRole("button", { name: /lancer l'empreinte/i }));

    await waitFor(() => expect(screen.getByDisplayValue("Serveur SSH (OpenSSH)")).toBeInTheDocument());
  });

  it("ajoute l'actif au registre de la mission sélectionnée", async () => {
    const fetchMock = mockFetch({ projects: projectFixture(), fingerprint: fingerprintFixture(), importedState: {} as ProjectState });
    globalThis.fetch = fetchMock as any;
    const user = userEvent.setup();
    render(<CollecteTechnique />);

    await user.type(screen.getByPlaceholderText(/collez ici/i), "Port 22\n");
    await user.click(screen.getByRole("button", { name: /lancer l'empreinte/i }));
    await waitFor(() => screen.getByDisplayValue("Serveur SSH (OpenSSH)"));
    expect(screen.getByText("Acme — Acme Corp")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /ajouter au registre/i }));

    await waitFor(() => {
      const importCall = fetchMock.mock.calls.find(([url]) => url === "/api/projects/acme/collecte/import");
      expect(importCall).toBeDefined();
      const body = JSON.parse((importCall as any)[1].body);
      expect(body.name).toBe("Serveur SSH (OpenSSH)");
      expect(body.type).toBe("Réseau");
    });
    expect(await screen.findByText(/ajouté au registre/i)).toBeInTheDocument();
  });
});
