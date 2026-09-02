export const MESES_ES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];
export const MESES_EN = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

/** El backend siempre devuelve el nombre del mes en español (ver
 *  montor_server._stats_mes); esto lo traduce si el idioma activo es inglés. */
export function mesTraducido(nombreEs: string, lang: "es" | "en"): string {
  if (lang === "es") return nombreEs;
  const idx = MESES_ES.indexOf(nombreEs);
  return idx >= 0 ? MESES_EN[idx] : nombreEs;
}
