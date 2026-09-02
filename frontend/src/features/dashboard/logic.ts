import type { Cotizaciones, Moneda, Tipo, Transaccion } from "@/api/types";

export const PERIODOS = ["1m", "3m", "6m", "1a", "todo"] as const;
export type Periodo = (typeof PERIODOS)[number];

export type Filtros = {
  periodo: Periodo;
  tipo: Tipo | "";
  moneda: Moneda | "";
  categoria: string;
  busqueda: string;
  /** Rango de días puntual; cuando está activo, reemplaza al período. */
  dia: { desde: string; hasta: string } | null;
};

export const FILTROS_INICIALES: Filtros = {
  periodo: "1m",
  tipo: "",
  moneda: "",
  categoria: "",
  busqueda: "",
  dia: null,
};

export function normalizar(s: string | null | undefined): string {
  return (s ?? "")
    .toString()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

/** Rango de días normalizado (desde <= hasta), o null si no hay filtro. */
export function normalizarRangoDia(desde: string, hasta: string): { desde: string; hasta: string } | null {
  if (!desde && !hasta) return null;
  const d = desde || hasta;
  const h = hasta || desde;
  return d > h ? { desde: h, hasta: d } : { desde: d, hasta: h };
}

/** Fecha desde la que arranca el período (null = "todo", sin recorte). */
export function desdePeriodo(periodo: Periodo, hoy: Date): Date | null {
  if (periodo === "todo") return null;
  const d = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  if (periodo === "3m") d.setMonth(d.getMonth() - 2);
  else if (periodo === "6m") d.setMonth(d.getMonth() - 5);
  else if (periodo === "1a") d.setMonth(0);
  return d;
}

export function filtrarTransacciones(datos: Transaccion[], f: Filtros, hoy: Date): Transaccion[] {
  const desde = f.dia ? null : desdePeriodo(f.periodo, hoy);
  const busq = normalizar(f.busqueda.trim());

  return datos
    .filter((t) => {
      if (f.dia) {
        if (t.fecha < f.dia.desde || t.fecha > f.dia.hasta) return false;
      } else if (desde) {
        const fecha = new Date(t.fecha + "T00:00:00");
        if (fecha < desde) return false;
      }
      if (f.tipo && t.tipo !== f.tipo) return false;
      if (f.moneda && (t.moneda ?? "ARS") !== f.moneda) return false;
      if (f.categoria && normalizar(t.categoria) !== normalizar(f.categoria)) return false;
      if (busq) {
        const coincide =
          normalizar(t.categoria).includes(busq) ||
          normalizar(t.descripcion).includes(busq) ||
          String(t.monto).includes(busq);
        if (!coincide) return false;
      }
      return true;
    })
    .sort((a, b) => b.fecha.localeCompare(a.fecha));
}

/** Para el datalist de autocompletado (formulario de carga y presupuestos):
 *  las más usadas primero, así lo que escribís más seguido aparece arriba. */
export function categoriasPorFrecuencia(datos: Transaccion[]): string[] {
  const freq = new Map<string, number>();
  for (const t of datos) {
    const c = (t.categoria ?? "").trim();
    if (c) freq.set(c, (freq.get(c) ?? 0) + 1);
  }
  return [...freq.entries()].sort((a, b) => b[1] - a[1]).map(([c]) => c);
}

/** Para el <select> de filtro por categoría: alfabético, es lo esperable
 *  para elegir de una lista, no para escribir. */
export function categoriasDisponibles(datos: Transaccion[]): string[] {
  const vistas = new Map<string, string>();
  for (const t of datos) {
    if (t.categoria && !vistas.has(normalizar(t.categoria))) vistas.set(normalizar(t.categoria), t.categoria);
  }
  return [...vistas.values()].sort((a, b) => normalizar(a).localeCompare(normalizar(b)));
}

/**
 * ARS de una transacción, usando la cotización que quedó guardada en la
 * propia fila (la del día en que se cargó) por sobre la de hoy — así el
 * consolidado no se revalúa solo cada vez que cambia el dólar/euro. Las
 * filas viejas, cargadas antes de que existiera esa foto, caen a la
 * cotización actual (`cotiz`).
 */
export function toARS(t: Transaccion, cotiz: Cotizaciones): number | null {
  const moneda = t.moneda ?? "ARS";
  if (moneda === "ARS") return Number(t.monto);
  const tasa = moneda === "USD" ? (t.cotizacion_usd ?? cotiz.USD) : (t.cotizacion_eur ?? cotiz.EUR);
  return tasa ? Number(t.monto) * tasa : null;
}

export function fromARS(ars: number, moneda: Moneda, cotiz: Cotizaciones): number | null {
  if (moneda === "ARS") return ars;
  if (moneda === "USD") return cotiz.USD ? ars / cotiz.USD : null;
  if (moneda === "EUR") return cotiz.EUR ? ars / cotiz.EUR : null;
  return ars;
}
