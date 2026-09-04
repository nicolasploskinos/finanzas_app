/**
 * Envío de errores del frontend al server.
 *
 * Reglas que importan acá:
 * - Reportar no puede romper nada ni encadenar más errores: todo va dentro de
 *   try/catch y se ignora la respuesta.
 * - Se descartan los repetidos. Un componente que falla en loop dispararía el
 *   mismo error decenas de veces por segundo; interesa el primero.
 */

const yaReportados = new Set<string>();
const MAX_DISTINTOS = 10;

export function reportarError(error: unknown, stackExtra?: string) {
  try {
    const err = error instanceof Error ? error : new Error(String(error));
    const mensaje = err.message || "Error sin mensaje";

    // Clave por mensaje + primera línea del stack: distingue dos fallas
    // distintas sin dejar pasar la misma repetida.
    const clave = `${mensaje}|${(err.stack ?? "").split("\n")[1] ?? ""}`;
    if (yaReportados.has(clave) || yaReportados.size >= MAX_DISTINTOS) return;
    yaReportados.add(clave);

    void fetch("/api/montor/errores", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      // Que no retenga la navegación si el usuario se va de la página.
      keepalive: true,
      body: JSON.stringify({
        mensaje,
        stack: [err.stack, stackExtra].filter(Boolean).join("\n---\n"),
        ruta: window.location.pathname + window.location.search,
      }),
    }).catch(() => {});
  } catch {
    // Ni el reporte de errores puede ser fuente de errores.
  }
}

/** Errores que no pasan por React: async sueltos, promesas sin catch. */
export function escucharErroresGlobales() {
  window.addEventListener("error", (e) => {
    reportarError(e.error ?? e.message);
  });
  window.addEventListener("unhandledrejection", (e) => {
    reportarError(e.reason);
  });
}
