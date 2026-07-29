/**
 * Formatage des durées de temps consommé (F19).
 * Fonction pure isolée du composant : elle est réutilisable par les exports et
 * le tableau de bord, et son export depuis un fichier de composant casserait
 * le Fast Refresh (règle react-refresh/only-export-components).
 */
export function formatDuree(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} h`;
  return `${h} h ${String(m).padStart(2, "0")}`;
}
