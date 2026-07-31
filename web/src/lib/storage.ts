/**
 * Accès localStorage protégés : le mode privé, un quota dépassé ou une
 * politique navigateur restrictive peuvent faire lever getItem/setItem.
 * Aucun de ces cas ne doit casser l'écran (cf. CLAUDE.md, section
 * Conventions frontend) — on dégrade silencieusement au lieu de planter.
 */
export function safeGetItem(key: string): string | null {
  try {
    if (key === "copilot_api_key") {
      return window.sessionStorage.getItem(key);
    }
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function safeSetItem(key: string, value: string): boolean {
  try {
    if (key === "copilot_api_key") {
      window.sessionStorage.setItem(key, value);
    } else {
      window.localStorage.setItem(key, value);
    }
    return true;
  } catch {
    return false;
  }
}
