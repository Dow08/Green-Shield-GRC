/**
 * Coordonnée polaire -> cartésienne, partagée par les visualisations SVG
 * dessinées à la main (roue NIST CSF, radar de maturité) : le projet
 * s'interdit toute dépendance de graphes qui alourdirait l'exécutable.
 *
 * `deg` est décalé de -90° : 0° pointe donc vers le haut plutôt que vers la
 * droite, la convention habituelle des roues/cadrans plutôt que celle de la
 * trigonométrie standard.
 */
export function polaire(cx: number, cy: number, r: number, deg: number): [number, number] {
  const a = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}
