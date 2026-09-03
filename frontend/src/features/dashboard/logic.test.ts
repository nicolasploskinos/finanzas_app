import { describe, expect, it } from "vitest";

import type { Cotizaciones, Transaccion } from "@/api/types";
import {
  categoriasDisponibles,
  categoriasPorFrecuencia,
  desdePeriodo,
  FILTROS_INICIALES,
  filtrarTransacciones,
  fromARS,
  normalizarRangoDia,
  toARS,
} from "./logic";
import type { Filtros } from "./logic";

function tx(p: Partial<Transaccion> & { monto: number; fecha: string }): Transaccion {
  return {
    id: Math.random(),
    tipo: "Gasto",
    categoria: null,
    descripcion: null,
    moneda: "ARS",
    cotizacion_usd: null,
    cotizacion_eur: null,
    viaje_id: null,
    ...p,
  } as Transaccion;
}

const filtros = (extra: Partial<Filtros> = {}): Filtros => ({ ...FILTROS_INICIALES, ...extra });
const COTIZ: Cotizaciones = { USD: 1500, EUR: 1700 };

describe("toARS", () => {
  it("prefiere la cotización guardada en la fila antes que la de hoy", () => {
    const t = tx({ monto: 100, fecha: "2026-08-01", moneda: "USD", cotizacion_usd: 1000 });
    expect(toARS(t, COTIZ)).toBe(100_000); // no 150.000
  });

  it("cae a la cotización actual en filas viejas sin foto guardada", () => {
    const t = tx({ monto: 100, fecha: "2020-01-01", moneda: "USD", cotizacion_usd: null });
    expect(toARS(t, COTIZ)).toBe(150_000);
  });

  it("devuelve null si tampoco hay cotización actual", () => {
    const t = tx({ monto: 100, fecha: "2020-01-01", moneda: "USD", cotizacion_usd: null });
    expect(toARS(t, { USD: null, EUR: null })).toBeNull();
  });
});

describe("fromARS", () => {
  it("convierte a la moneda pedida", () => {
    expect(fromARS(150_000, "USD", COTIZ)).toBe(100);
    expect(fromARS(150_000, "ARS", COTIZ)).toBe(150_000);
  });

  it("devuelve null si falta la cotización", () => {
    expect(fromARS(1000, "EUR", { USD: 1500, EUR: null })).toBeNull();
  });
});

describe("normalizarRangoDia", () => {
  it("sin fechas no hay filtro", () => {
    expect(normalizarRangoDia("", "")).toBeNull();
  });

  it("con una sola fecha, el rango es ese único día", () => {
    expect(normalizarRangoDia("2026-08-10", "")).toEqual({ desde: "2026-08-10", hasta: "2026-08-10" });
    expect(normalizarRangoDia("", "2026-08-10")).toEqual({ desde: "2026-08-10", hasta: "2026-08-10" });
  });

  it("da vuelta el rango si vino al revés", () => {
    expect(normalizarRangoDia("2026-08-20", "2026-08-10")).toEqual({
      desde: "2026-08-10",
      hasta: "2026-08-20",
    });
  });
});

describe("desdePeriodo", () => {
  const hoy = new Date(2026, 7, 15); // agosto 2026

  it("'todo' no recorta", () => {
    expect(desdePeriodo("todo", hoy)).toBeNull();
  });

  it("cuenta el mes actual dentro del período", () => {
    expect(desdePeriodo("1m", hoy)).toEqual(new Date(2026, 7, 1));
    expect(desdePeriodo("3m", hoy)).toEqual(new Date(2026, 5, 1));
    expect(desdePeriodo("6m", hoy)).toEqual(new Date(2026, 2, 1));
    expect(desdePeriodo("1a", hoy)).toEqual(new Date(2026, 0, 1));
  });

  it("'3m' cruza bien el cambio de año", () => {
    expect(desdePeriodo("3m", new Date(2026, 0, 15))).toEqual(new Date(2025, 10, 1));
  });
});

describe("filtrarTransacciones", () => {
  const hoy = new Date(2026, 7, 15);
  const datos = [
    tx({ monto: 1000, fecha: "2026-08-10", categoria: "Comida", descripcion: "Almacén" }),
    tx({ monto: 2000, fecha: "2026-08-12", categoria: "Transporte", moneda: "USD", cotizacion_usd: 1000 }),
    tx({ tipo: "Ingreso", monto: 5000, fecha: "2026-06-05", categoria: "Sueldo" }),
    tx({ monto: 300, fecha: "2025-12-20", categoria: "Comida" }),
  ];

  it("ordena de más nuevo a más viejo", () => {
    const r = filtrarTransacciones(datos, filtros({ periodo: "todo" }), hoy);
    expect(r.map((t) => t.fecha)).toEqual(["2026-08-12", "2026-08-10", "2026-06-05", "2025-12-20"]);
  });

  it("recorta por período", () => {
    expect(filtrarTransacciones(datos, filtros({ periodo: "1m" }), hoy)).toHaveLength(2);
    expect(filtrarTransacciones(datos, filtros({ periodo: "3m" }), hoy)).toHaveLength(3);
  });

  it("filtra por tipo, moneda y categoría", () => {
    expect(filtrarTransacciones(datos, filtros({ periodo: "todo", tipo: "Ingreso" }), hoy)).toHaveLength(1);
    expect(filtrarTransacciones(datos, filtros({ periodo: "todo", moneda: "USD" }), hoy)).toHaveLength(1);
    expect(filtrarTransacciones(datos, filtros({ periodo: "todo", categoria: "comida" }), hoy)).toHaveLength(2);
  });

  it("la búsqueda ignora tildes y mayúsculas, y mira también el monto", () => {
    const porDescripcion = filtrarTransacciones(datos, filtros({ periodo: "todo", busqueda: "almacen" }), hoy);
    expect(porDescripcion).toHaveLength(1);
    const porMonto = filtrarTransacciones(datos, filtros({ periodo: "todo", busqueda: "5000" }), hoy);
    expect(porMonto).toHaveLength(1);
  });

  it("el rango de días puntual pisa al período", () => {
    const f = filtros({ periodo: "1m", dia: { desde: "2025-12-01", hasta: "2025-12-31" } });
    const r = filtrarTransacciones(datos, f, hoy);
    expect(r.map((t) => t.fecha)).toEqual(["2025-12-20"]);
  });
});

describe("categorías", () => {
  const datos = [
    tx({ monto: 1, fecha: "2026-08-01", categoria: "Comida" }),
    tx({ monto: 1, fecha: "2026-08-02", categoria: "Comida" }),
    tx({ monto: 1, fecha: "2026-08-03", categoria: "Comida" }),
    tx({ monto: 1, fecha: "2026-08-04", categoria: "Alquiler" }),
    tx({ monto: 1, fecha: "2026-08-05", categoria: "Alquiler" }),
    tx({ monto: 1, fecha: "2026-08-06", categoria: "Zapatos" }),
  ];

  it("para el autocompletado van primero las más usadas", () => {
    expect(categoriasPorFrecuencia(datos)).toEqual(["Comida", "Alquiler", "Zapatos"]);
  });

  it("para el select van alfabéticas", () => {
    expect(categoriasDisponibles(datos)).toEqual(["Alquiler", "Comida", "Zapatos"]);
  });
});
