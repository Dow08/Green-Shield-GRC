/**
 * Génération d'identifiants séquentiels sans collision, un seul algorithme
 * partagé pour tous les points d'ajout (valeurs métier, biens supports,
 * registre RGPD, remédiations...). Miroir de `_next_bs_id` côté backend
 * (api/modules/collecte_technique.py) : même principe (numéro suivant libre
 * sur le préfixe donné), remplace les anciens id générés par `Math.random()`
 * qui pouvaient se percuter (cf. CLAUDE.md, section Conventions frontend).
 */
function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function nextId(prefix: string, existingIds: string[]): string {
  const pattern = new RegExp(`^${escapeRegExp(prefix)}-(\\d+)$`);
  const numbers = existingIds
    .map((id) => pattern.exec(id)?.[1])
    .filter((n): n is string => n !== undefined)
    .map(Number);

  let next = numbers.length > 0 ? Math.max(...numbers) + 1 : 1;
  const existing = new Set(existingIds);
  let candidate = `${prefix}-${String(next).padStart(2, "0")}`;
  while (existing.has(candidate)) {
    next += 1;
    candidate = `${prefix}-${String(next).padStart(2, "0")}`;
  }
  return candidate;
}
