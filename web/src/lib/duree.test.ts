import { describe, it, expect } from "vitest";
import { formatDuree } from "./duree";

describe("formatDuree", () => {
  it("affiche les durées de moins d'une heure en minutes", () => {
    expect(formatDuree(45)).toBe("45 min");
  });

  it("affiche les heures pleines sans minutes", () => {
    expect(formatDuree(120)).toBe("2 h");
  });

  it("affiche heures et minutes, minutes sur deux chiffres", () => {
    expect(formatDuree(90)).toBe("1 h 30");
    expect(formatDuree(125)).toBe("2 h 05");
  });

  it("gère zéro", () => {
    expect(formatDuree(0)).toBe("0 min");
  });

  it("gère une durée longue (plusieurs journées cumulées)", () => {
    expect(formatDuree(2000)).toBe("33 h 20");
  });
});
