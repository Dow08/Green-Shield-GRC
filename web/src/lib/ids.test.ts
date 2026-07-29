import { describe, it, expect } from "vitest";
import { nextId } from "./ids";

describe("nextId", () => {
  it("démarre à 01 sur une liste vide", () => {
    expect(nextId("BS", [])).toBe("BS-01");
  });

  it("incrémente à partir du plus grand numéro existant", () => {
    expect(nextId("BS", ["BS-01", "BS-03"])).toBe("BS-04");
  });

  it("ignore les id d'un autre préfixe", () => {
    expect(nextId("BS", ["VM-01", "VM-02"])).toBe("BS-01");
  });

  it("ignore les id non numériques du même préfixe (gabarits historiques)", () => {
    expect(nextId("BS", ["BS-AD", "BS-01"])).toBe("BS-02");
  });

  it("évite toute collision même si un numéro a été saisi manuellement plus haut", () => {
    expect(nextId("BS", ["BS-01", "BS-02", "BS-04"])).toBe("BS-05");
  });

  it("gère un préfixe contenant un tiret (id de gabarit composé)", () => {
    expect(nextId("VM-BDD", ["VM-BDD-01"])).toBe("VM-BDD-02");
    expect(nextId("VM-BDD", [])).toBe("VM-BDD-01");
  });

  it("ne confond pas deux préfixes qui se chevauchent partiellement", () => {
    // "BS-AD" ne doit pas être compté comme un id du préfixe "BS".
    expect(nextId("BS", ["BS-AD-05"])).toBe("BS-01");
  });
});
