import { describe, expect, it } from "vitest";

import type { Cotizaciones, Transaccion } from "@/api/types";
import {
  calcularAnalisis,
  categoriasDisponibles,
  FILTROS_INICIALES,
  normalizar,
  rangoMeses,
  rangoPeriodo,
  toARS,
} from "./analytics";
import type { Filtros } from "./analytics";

/** Transacción mínima; sólo se completan los campos que la lógica mira. */
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
const SIN_COTIZ: Cotizaciones = { USD: null, EUR: null };

describe("toARS", () => {
  it("deja los pesos como están", () => {
    expect(toARS(tx({ monto: 1500, fecha: "2026-08-01" }), COTIZ)).toBe(1500);
  });

  it("usa la cotización guardada en la fila, no la de hoy", () => {
    const t = tx({ monto: 100, fecha: "2026-08-01", moneda: "USD", cotizacion_usd: 1200 });
    expect(toARS(t, COTIZ)).toBe(120_000); // no 150.000
  });

  it("cae a la cotización de hoy en filas viejas sin foto guardada", () => {
    const t = tx({ monto: 100, fecha: "2020-01-01", moneda: "USD", cotizacion_usd: null });
    expect(toARS(t, COTIZ)).toBe(150_000);
  });

  it("devuelve null recién cuando tampoco hay cotización de hoy", () => {
    const t = tx({ monto: 100, fecha: "2026-08-01", moneda: "EUR", cotizacion_eur: null });
    expect(toARS(t, SIN_COTIZ)).toBeNull();
  });

  it("trata una moneda ausente como pesos", () => {
    expect(toARS(tx({ monto: 50, fecha: "2026-08-01", moneda: null }), COTIZ)).toBe(50);
  });
});

describe("rangoPeriodo", () => {
  const hoy = new Date(2026, 7, 15); // 15 de agosto de 2026

  it("'todo' no recorta por ninguno de los dos lados", () => {
    expect(rangoPeriodo("todo", hoy)).toEqual({ desde: null, hasta: null });
  });

  it("'1m' arranca el primero del mes en curso", () => {
    const { desde, hasta } = rangoPeriodo("1m", hoy);
    expect(desde).toEqual(new Date(2026, 7, 1));
    expect(hasta).toBeNull();
  });

  it("'3m' cuenta el mes actual más los dos anteriores", () => {
    expect(rangoPeriodo("3m", hoy).desde).toEqual(new Date(2026, 5, 1));
  });

  it("'1a' arranca en enero del año en curso", () => {
    expect(rangoPeriodo("1a", hoy).desde).toEqual(new Date(2026, 0, 1));
  });

  it("'mes_pasado' es el último mes completo, con tope incluido", () => {
    const { desde, hasta } = rangoPeriodo("mes_pasado", hoy);
    expect(desde).toEqual(new Date(2026, 6, 1)); // 1 de julio
    expect(hasta).toEqual(new Date(2026, 6, 31)); // 31 de julio
  });

  it("'mes_pasado' cruza bien el cambio de año", () => {
    const enero = new Date(2026, 0, 10);
    const { desde, hasta } = rangoPeriodo("mes_pasado", enero);
    expect(desde).toEqual(new Date(2025, 11, 1));
    expect(hasta).toEqual(new Date(2025, 11, 31));
  });
});

describe("rangoMeses", () => {
  const hoy = new Date(2026, 7, 15);

  it("los períodos fijos no dependen de los datos", () => {
    expect(rangoMeses("3m", [], hoy)).toEqual({ n: 3, endOffset: 0 });
    expect(rangoMeses("mes_pasado", [], hoy)).toEqual({ n: 1, endOffset: 1 });
  });

  it("'todo' se estira hasta la transacción más vieja", () => {
    const lista = [tx({ monto: 1, fecha: "2026-06-10" }), tx({ monto: 1, fecha: "2026-08-02" })];
    expect(rangoMeses("todo", lista, hoy).n).toBe(3); // junio, julio, agosto
  });

  it("'todo' sin datos dibuja un solo mes", () => {
    expect(rangoMeses("todo", [], hoy)).toEqual({ n: 1, endOffset: 0 });
  });

  it("'todo' corta en 60 meses aunque el historial sea más largo", () => {
    const viejo = [tx({ monto: 1, fecha: "2000-01-01" })];
    expect(rangoMeses("todo", viejo, hoy).n).toBe(60);
  });
});

describe("calcularAnalisis: monedas por lado", () => {
  const hoy = new Date(2026, 7, 15);
  // Ingresos: 800.000 ARS + 100 USD (=100.000). Gastos: 20.000 ARS + 50 USD (=50.000).
  const datos = [
    tx({ tipo: "Ingreso", monto: 800_000, fecha: "2026-08-01", categoria: "Sueldo" }),
    tx({ tipo: "Ingreso", monto: 100, fecha: "2026-08-02", moneda: "USD", cotizacion_usd: 1000, categoria: "Freelance" }),
    tx({ tipo: "Gasto", monto: 20_000, fecha: "2026-08-03", categoria: "Super" }),
    tx({ tipo: "Gasto", monto: 50, fecha: "2026-08-04", moneda: "USD", cotizacion_usd: 1000, categoria: "Viaje" }),
  ];

  it("por defecto suma todas las monedas, convertidas a ARS", () => {
    const r = calcularAnalisis(datos, filtros(), "es", COTIZ, hoy);
    expect(r.ingTotal).toBe(900_000);
    expect(r.gasTotal).toBe(70_000);
    expect(r.balanceNeto).toBe(830_000);
  });

  it("recorta sólo el lado elegido: gastos en ARS, ingresos en todas", () => {
    const r = calcularAnalisis(datos, filtros({ monedasGas: ["ARS"] }), "es", COTIZ, hoy);
    expect(r.ingTotal).toBe(900_000);
    expect(r.gasTotal).toBe(20_000);
  });

  it("permite el corte inverso: ingresos en USD, gastos en todas", () => {
    const r = calcularAnalisis(datos, filtros({ monedasIng: ["USD"] }), "es", COTIZ, hoy);
    expect(r.ingTotal).toBe(100_000);
    expect(r.gasTotal).toBe(70_000);
  });

  it("admite dos monedas de un lado", () => {
    const r = calcularAnalisis(datos, filtros({ monedasGas: ["USD", "EUR"] }), "es", COTIZ, hoy);
    expect(r.gasTotal).toBe(50_000);
  });

  it("sin monedas de un lado, ese lado queda en cero y el otro intacto", () => {
    const r = calcularAnalisis(datos, filtros({ monedasIng: [] }), "es", COTIZ, hoy);
    expect(r.ingTotal).toBe(0);
    expect(r.gasTotal).toBe(70_000);
  });

  it("el desglose por categoría respeta el filtro de monedas de gastos", () => {
    const r = calcularAnalisis(datos, filtros({ monedasGas: ["ARS"] }), "es", COTIZ, hoy);
    expect(r.categorias).toEqual([{ nombre: "Super", total: 20_000 }]);
  });
});

describe("calcularAnalisis: totales y promedio", () => {
  const hoy = new Date(2026, 7, 15); // agosto

  it("el promedio mensual ignora el mes en curso, que todavía no terminó", () => {
    const datos = [
      tx({ tipo: "Gasto", monto: 30_000, fecha: "2026-06-10" }),
      tx({ tipo: "Gasto", monto: 10_000, fecha: "2026-07-10" }),
      tx({ tipo: "Gasto", monto: 999_999, fecha: "2026-08-10" }), // mes en curso
    ];
    const r = calcularAnalisis(datos, filtros({ periodo: "3m" }), "es", COTIZ, hoy);
    expect(r.gasTotal).toBe(1_039_999); // el total sí lo cuenta
    expect(r.promedioMensual).toBe(20_000); // (30.000 + 10.000) / 2 meses terminados
  });

  it("deja afuera lo que cae antes del período", () => {
    const datos = [
      tx({ tipo: "Gasto", monto: 5_000, fecha: "2026-01-05" }),
      tx({ tipo: "Gasto", monto: 7_000, fecha: "2026-08-05" }),
    ];
    expect(calcularAnalisis(datos, filtros({ periodo: "1m" }), "es", COTIZ, hoy).gasTotal).toBe(7_000);
    expect(calcularAnalisis(datos, filtros({ periodo: "1a" }), "es", COTIZ, hoy).gasTotal).toBe(12_000);
  });

  // Regresión: los movimientos en USD/EUR cargados antes de que existiera la
  // foto de cotización quedaban afuera de los gráficos, y Análisis mostraba
  // un total distinto al del panel para los mismos datos.
  it("cuenta los movimientos viejos en moneda extranjera usando la cotización de hoy", () => {
    const datos = [
      tx({ tipo: "Gasto", monto: 1_000, fecha: "2026-08-05" }),
      tx({ tipo: "Gasto", monto: 100, fecha: "2026-08-06", moneda: "USD", cotizacion_usd: null }),
    ];
    expect(calcularAnalisis(datos, filtros(), "es", COTIZ, hoy).gasTotal).toBe(151_000);
  });

  it("saltea las transacciones que no se pueden convertir por ningún lado", () => {
    const datos = [
      tx({ tipo: "Gasto", monto: 10, fecha: "2026-08-05", moneda: "EUR", cotizacion_eur: null }),
      tx({ tipo: "Gasto", monto: 1_000, fecha: "2026-08-06" }),
    ];
    expect(calcularAnalisis(datos, filtros(), "es", SIN_COTIZ, hoy).gasTotal).toBe(1_000);
  });

  it("los gastos sin categoría caen en una etiqueta traducida", () => {
    const datos = [tx({ tipo: "Gasto", monto: 100, fecha: "2026-08-05", categoria: "  " })];
    const r = calcularAnalisis(datos, filtros(), "es", COTIZ, hoy);
    expect(r.categorias[0].nombre).toBe("Sin categoría");
  });

  it("corta el ranking de categorías en 8", () => {
    const datos = Array.from({ length: 12 }, (_, i) =>
      tx({ tipo: "Gasto", monto: (i + 1) * 100, fecha: "2026-08-05", categoria: `cat${i}` }),
    );
    const r = calcularAnalisis(datos, filtros(), "es", COTIZ, hoy);
    expect(r.categorias).toHaveLength(8);
    expect(r.categorias[0].nombre).toBe("cat11"); // el más caro primero
  });
});

describe("categoriasDisponibles", () => {
  it("no repite categorías que sólo difieren en tildes o mayúsculas", () => {
    const datos = [
      tx({ monto: 1, fecha: "2026-08-01", categoria: "Comida" }),
      tx({ monto: 1, fecha: "2026-08-02", categoria: "comida" }),
      tx({ monto: 1, fecha: "2026-08-03", categoria: "Almacén" }),
      tx({ monto: 1, fecha: "2026-08-04", categoria: "almacen" }),
    ];
    expect(categoriasDisponibles(datos)).toEqual(["Almacén", "Comida"]);
  });

  it("ignora las vacías", () => {
    expect(categoriasDisponibles([tx({ monto: 1, fecha: "2026-08-01", categoria: "   " })])).toEqual([]);
  });
});

describe("normalizar", () => {
  it("saca tildes y pasa a minúscula", () => {
    expect(normalizar("Almacén")).toBe("almacen");
  });

  it("tolera null y undefined", () => {
    expect(normalizar(null)).toBe("");
    expect(normalizar(undefined)).toBe("");
  });
});
