import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { BoutonDictee } from "./BoutonDictee";
import { CHAMPS_SANS_DICTEE, dicteeAutorisee } from "../lib/dictee";

/**
 * La dictée envoie de l'audio à un tiers : ces tests vérifient d'abord ce que
 * l'outil s'interdit d'envoyer, avant de vérifier qu'il fonctionne.
 */

// Objet de reconnaissance simulé : on capture les gestionnaires posés dessus
// pour déclencher une transcription sans micro réel.
class FausseReconnaissance {
  continuous = false;
  interimResults = false;
  lang = "";
  onresult: ((e: unknown) => void) | null = null;
  onerror: ((e: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  demarree = false;
  start() {
    this.demarree = true;
  }
  stop() {
    this.demarree = false;
    this.onend?.();
  }
}

let derniereReconnaissance: FausseReconnaissance | null = null;

function activerDictee(active: boolean) {
  localStorage.setItem("dictee_activee", active ? "1" : "0");
}

beforeEach(() => {
  localStorage.clear();
  derniereReconnaissance = null;
  (window as any).SpeechRecognition = function () {
    derniereReconnaissance = new FausseReconnaissance();
    return derniereReconnaissance;
  };
  (navigator as any).mediaDevices = {
    getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop: vi.fn() }] }),
  };
});

afterEach(() => {
  delete (window as any).SpeechRecognition;
});

describe("politique de confidentialité", () => {
  it("n'affiche aucun micro tant que la dictée n'est pas activée dans les Réglages", () => {
    activerDictee(false);
    const { container } = render(<BoutonDictee onTexte={vi.fn()} libelle="Note" />);
    expect(container.querySelector("button")).toBeNull();
  });

  it.each(Object.keys(CHAMPS_SANS_DICTEE))(
    "refuse la dictée sur un champ de nature « %s » même dictée activée",
    (nature) => {
      activerDictee(true);
      const { container } = render(<BoutonDictee onTexte={vi.fn()} nature={nature} />);
      // Aucun bouton cliquable : l'exclusion n'est pas contournable depuis l'UI.
      expect(container.querySelector("button")).toBeNull();
      expect(dicteeAutorisee(nature)).toBe(false);
    },
  );

  it("explique pourquoi le champ est exclu plutôt que de masquer l'information", () => {
    activerDictee(true);
    const { container } = render(<BoutonDictee onTexte={vi.fn()} nature="entretien" />);
    const indice = container.querySelector("[title]");
    expect(indice?.getAttribute("title")).toContain("données personnelles");
  });

  it("autorise un champ neutre non déclaré sensible", () => {
    activerDictee(true);
    render(<BoutonDictee onTexte={vi.fn()} libelle="Recommandation" />);
    expect(screen.getByRole("button", { name: /Dicter : Recommandation/ })).toBeTruthy();
  });
});

describe("fonctionnement de la dictée", () => {
  it("ne s'affiche pas si le navigateur ne sait pas transcrire", () => {
    activerDictee(true);
    delete (window as any).SpeechRecognition;
    const { container } = render(<BoutonDictee onTexte={vi.fn()} libelle="Note" />);
    expect(container.querySelector("button")).toBeNull();
  });

  it("demande le micro avant de démarrer", async () => {
    activerDictee(true);
    render(<BoutonDictee onTexte={vi.fn()} libelle="Note" />);
    await act(async () => { fireEvent.click(screen.getByRole("button")); });
    await waitFor(() =>
      expect((navigator as any).mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true }),
    );
  });

  it("remonte le texte transcrit à l'appelant", async () => {
    activerDictee(true);
    const onTexte = vi.fn();
    render(<BoutonDictee onTexte={onTexte} libelle="Note" />);
    await act(async () => { fireEvent.click(screen.getByRole("button")); });
    await waitFor(() => expect(derniereReconnaissance?.demarree).toBe(true));

    derniereReconnaissance!.onresult?.({
      resultIndex: 0,
      results: [Object.assign([{ transcript: "premier constat" }], { isFinal: true })],
    });
    expect(onTexte).toHaveBeenCalledWith("premier constat");
  });

  it("ignore les transcriptions provisoires, qui changent encore", async () => {
    activerDictee(true);
    const onTexte = vi.fn();
    render(<BoutonDictee onTexte={onTexte} libelle="Note" />);
    await act(async () => { fireEvent.click(screen.getByRole("button")); });
    await waitFor(() => expect(derniereReconnaissance?.demarree).toBe(true));

    derniereReconnaissance!.onresult?.({
      resultIndex: 0,
      results: [Object.assign([{ transcript: "prem" }], { isFinal: false })],
    });
    expect(onTexte).not.toHaveBeenCalled();
  });

  it("affiche un message compréhensible quand le micro est refusé", async () => {
    activerDictee(true);
    (navigator as any).mediaDevices.getUserMedia = vi.fn().mockRejectedValue(new Error("refus"));
    render(<BoutonDictee onTexte={vi.fn()} libelle="Note" />);
    await act(async () => { fireEvent.click(screen.getByRole("button")); });
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("micro refusé"));
  });

  it("traduit les codes d'erreur du navigateur en langage clair", async () => {
    activerDictee(true);
    render(<BoutonDictee onTexte={vi.fn()} libelle="Note" />);
    await act(async () => { fireEvent.click(screen.getByRole("button")); });
    await waitFor(() => expect(derniereReconnaissance).not.toBeNull());

    derniereReconnaissance!.onerror?.({ error: "audio-capture" });
    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain("Aucun micro détecté"),
    );
  });

  it("signale l'état d'écoute aux technologies d'assistance", async () => {
    activerDictee(true);
    render(<BoutonDictee onTexte={vi.fn()} libelle="Note" />);
    const bouton = screen.getByRole("button");
    expect(bouton.getAttribute("aria-pressed")).toBe("false");
    await act(async () => { fireEvent.click(bouton); });
    await waitFor(() => expect(bouton.getAttribute("aria-pressed")).toBe("true"));
  });
});
