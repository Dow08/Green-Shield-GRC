/**
 * Afficheur de notifications (09/09/2026).
 *
 * L'enjeu principal de ces tests est l'accessibilité : `window.alert()`, qu'on
 * remplace, était annoncé nativement par les lecteurs d'écran. Le remplaçant
 * doit l'être aussi — d'où les assertions sur `role="alert"` (erreur, annonce
 * assertive), `role="status"` (succès et information, annonce polie) et sur
 * l'intitulé accessible du bouton de fermeture.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Notifications } from "./Notifications";
import { notifier } from "../lib/notifications";

// Le magasin est un singleton de module : sans remise à zéro, une notification
// d'un test précédent resterait affichée dans le suivant.
beforeEach(() => notifier.reinitialiser());
afterEach(() => notifier.reinitialiser());

describe("Notifications", () => {
  it("n'affiche rien tant qu'aucune notification n'est émise", () => {
    render(<Notifications />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("annonce une erreur en rôle « alert » et la garde à l'écran", () => {
    render(<Notifications />);
    act(() => {
      notifier.erreur("Échec téléversement : Failed to fetch");
    });

    const alerte = screen.getByRole("alert");
    expect(alerte).toHaveTextContent("Échec téléversement : Failed to fetch");
    // Le mot « Erreur » est réservé aux lecteurs d'écran (classe sr-only) :
    // l'icône seule ne dit rien à qui n'a pas la couleur.
    expect(alerte).toHaveTextContent("Erreur :");
  });

  it("annonce une information en rôle « status », pas en alerte", () => {
    render(<Notifications />);
    act(() => {
      notifier.info("Aucun bug à exporter.");
    });

    expect(screen.getByRole("status")).toHaveTextContent("Aucun bug à exporter.");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("ferme une erreur au clic sur son bouton, dont l'intitulé reprend le message", async () => {
    const user = userEvent.setup();
    render(<Notifications />);
    act(() => {
      notifier.erreur("Échec audit technique : port fermé");
    });

    // Le bouton est cherché DANS sa notification, et non par un intitulé qui
    // recopierait le message : depuis l'audit du 09/09/2026 il s'intitule
    // simplement « Fermer », le message étant rattaché par `aria-describedby`.
    // `role="alert"` étant `aria-atomic`, un intitulé reprenant le message le
    // faisait relire en entier par le lecteur d'écran.
    await user.click(
      within(screen.getByRole("alert")).getByRole("button", { name: "Fermer" }),
    );

    await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  });

  it("empile plusieurs notifications simultanées, chacune refermable séparément", async () => {
    const user = userEvent.setup();
    render(<Notifications />);
    act(() => {
      notifier.erreur("Échec de la génération : disque plein");
      notifier.erreur("Échec suppression : fichier verrouillé");
    });

    expect(screen.getAllByRole("alert")).toHaveLength(2);

    // On identifie la bonne carte par son texte, puis on ferme SON bouton :
    // c'est ce que fait l'utilisateur, et cela vérifie au passage que le
    // `aria-describedby` relie bien chaque bouton à son propre message.
    const carteVisee = screen
      .getAllByRole("alert")
      .find((carte) => carte.textContent?.includes("Échec de la génération"))!;
    await user.click(within(carteVisee).getByRole("button", { name: "Fermer" }));

    await waitFor(() => expect(screen.getAllByRole("alert")).toHaveLength(1));
    expect(screen.getByRole("alert")).toHaveTextContent("Échec suppression : fichier verrouillé");
  });

  it("ne double pas la carte d'une panne répétée portant la même clé", () => {
    render(<Notifications />);
    act(() => {
      notifier.erreur("Sauvegarde automatique impossible : tentative 1", { cle: "sauvegarde-auto" });
      notifier.erreur("Sauvegarde automatique impossible : tentative 2", { cle: "sauvegarde-auto" });
    });

    const alertes = screen.getAllByRole("alert");
    expect(alertes).toHaveLength(1);
    expect(alertes[0]).toHaveTextContent("tentative 2");
  });

  it("retire une notification effacée par son émetteur (sauvegarde revenue au vert)", async () => {
    render(<Notifications />);
    act(() => {
      notifier.erreur("Sauvegarde automatique impossible", { cle: "sauvegarde-auto" });
    });
    expect(screen.getByRole("alert")).toBeInTheDocument();

    act(() => notifier.fermerParCle("sauvegarde-auto"));

    await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  });
});
