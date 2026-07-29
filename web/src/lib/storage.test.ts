import { describe, it, expect, vi, afterEach } from "vitest";
import { safeGetItem, safeSetItem } from "./storage";

afterEach(() => {
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe("safeGetItem", () => {
  it("lit une valeur existante", () => {
    window.localStorage.setItem("k", "v");
    expect(safeGetItem("k")).toBe("v");
  });

  it("renvoie null pour une clé absente", () => {
    expect(safeGetItem("absent")).toBeNull();
  });

  it("renvoie null au lieu de planter si localStorage lève une exception (mode privé)", () => {
    vi.spyOn(window.localStorage.__proto__, "getItem").mockImplementation(() => {
      throw new Error("SecurityError");
    });
    expect(safeGetItem("k")).toBeNull();
  });
});

describe("safeSetItem", () => {
  it("écrit une valeur et renvoie true", () => {
    expect(safeSetItem("k", "v")).toBe(true);
    expect(window.localStorage.getItem("k")).toBe("v");
  });

  it("renvoie false au lieu de planter si le quota est dépassé", () => {
    vi.spyOn(window.localStorage.__proto__, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });
    expect(safeSetItem("k", "v")).toBe(false);
  });
});
