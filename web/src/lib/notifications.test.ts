/**
 * Règles de la file de notifications (09/09/2026).
 *
 * Testé ici sans DOM : les durées et le dédoublonnage sont des règles du
 * magasin, pas du rendu. Le test du composant (Notifications.test.tsx) vérifie
 * de son côté les rôles ARIA et la fermeture manuelle.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { lireNotifications, messageErreur, notifier } from "./notifications";

describe("file de notifications", () => {
  beforeEach(() => {
    notifier.reinitialiser();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    notifier.reinitialiser();
  });

  it("efface seule une confirmation de succès, au rythme de la pastille « Enregistré » (2,5 s)", () => {
    notifier.succes("Mission enregistrée");
    expect(lireNotifications()).toHaveLength(1);

    vi.advanceTimersByTime(2499);
    expect(lireNotifications()).toHaveLength(1);

    vi.advanceTimersByTime(2);
    expect(lireNotifications()).toHaveLength(0);
  });

  it("efface seule une information", () => {
    notifier.info("Aucun bug à exporter.");
    vi.advanceTimersByTime(5001);
    expect(lireNotifications()).toHaveLength(0);
  });

  it("garde une erreur à l'écran jusqu'à fermeture explicite", () => {
    const id = notifier.erreur("Échec téléversement : Failed to fetch");

    // Dix minutes : on ne fait pas disparaître un échec avant lecture.
    vi.advanceTimersByTime(600_000);
    expect(lireNotifications()).toHaveLength(1);

    notifier.fermer(id);
    expect(lireNotifications()).toHaveLength(0);
  });

  it("rafraîchit la même carte au lieu d'empiler quand la clé est identique", () => {
    // Cas de la sauvegarde automatique : une panne d'API produit un échec
    // toutes les 60 s, qui ne doit pas devenir une avalanche de notifications.
    notifier.erreur("Sauvegarde automatique impossible : tentative 1", { cle: "sauvegarde-auto" });
    notifier.erreur("Sauvegarde automatique impossible : tentative 2", { cle: "sauvegarde-auto" });
    notifier.erreur("Sauvegarde automatique impossible : tentative 3", { cle: "sauvegarde-auto" });

    const restantes = lireNotifications();
    expect(restantes).toHaveLength(1);
    expect(restantes[0].message).toContain("tentative 3");
  });

  it("referme la notification d'une clé quand l'opération finit par réussir", () => {
    notifier.erreur("Sauvegarde automatique impossible", { cle: "sauvegarde-auto" });
    notifier.fermerParCle("sauvegarde-auto");
    expect(lireNotifications()).toHaveLength(0);
  });

  it("plafonne la pile en sacrifiant les messages éphémères avant les erreurs", () => {
    notifier.succes("succès 1");
    notifier.info("info 1");
    notifier.erreur("erreur 1");
    notifier.erreur("erreur 2");
    notifier.erreur("erreur 3");

    const restantes = lireNotifications();
    expect(restantes).toHaveLength(4);
    expect(restantes.map((n) => n.message)).toEqual(["info 1", "erreur 1", "erreur 2", "erreur 3"]);
  });

  it("garde la même référence d'instantané tant que rien ne change (useSyncExternalStore)", () => {
    notifier.erreur("Panne API");
    expect(lireNotifications()).toBe(lireNotifications());
  });

  it("retombe sur un libellé exploitable quand le rejet n'est pas une Error", () => {
    expect(messageErreur(new Error("Failed to fetch"), "repli")).toBe("Failed to fetch");
    expect(messageErreur("403 Forbidden", "repli")).toBe("403 Forbidden");
    expect(messageErreur({ code: 500 }, "Échec de la génération")).toBe("Échec de la génération");
    expect(messageErreur(new Error(""), "Échec de la génération")).toBe("Échec de la génération");
  });
});
