import type { Cotizaciones, Moneda, Tipo, Transaccion } from "@/api/types";
import type { Lang } from "@/i18n/messages";
import { MESES_CORTOS, tr } from "@/i18n/messages";

export const PERIODOS = ["1m", "mes_pasado", "3m", "6m", "1a", "todo"] as const;
export type Periodo = (typeof PERIODOS)[number];

export const MONEDAS: Moneda[] = ["ARS", "USD", "EUR"];

/**
 * Las monedas se eligen por separado para ingresos y para gastos: se puede
 * mirar, por ejemplo, los ingresos sólo en dólares contra los gastos en las
 * tres monedas. Todo lo seleccionado se suma junto, convertido a ARS con la
 * cotización que guardó cada movimiento (ver `toARS`).
 */
export type Filtros = {
  periodo: Periodo;
  tipo: Tipo | "";
  monedasIng: Moneda[];
  monedasGas: Moneda[];
  categoria: string;
};

export const FILTROS_INICIALES: Filtros = {
  periodo: "1m",
  tipo: "",
  monedasIng: [...MONEDAS],
  monedasGas: [...MONEDAS],
  categoria: "",
};

export type MesSerie = {
  key: string;
  label: string;
  ing: number;
  gas: number;
};

export type Analisis = {
  meses: MesSerie[];
  ingTotal: number;
  gasTotal: number;
  balanceNeto: number;
  promedioMensual: number;
  categorias: Array<{ nombre: string; total: number }>;
  hayDatosMensuales: boolean;
};

export function normalizar(s: string | null | undefined): string {
  return (s ?? "")
    .toString()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function fmtARS(n: number): string {
  return "$" + Math.round(n).toLocaleString("es-AR");
}

/**
 * Monto de la transacción llevado a ARS con la cotización que quedó guardada
 * en la propia fila (la del día en que se cargó), igual que el consolidado
 * del panel principal.
 *
 * Las filas cargadas antes de que existiera esa foto la tienen en null: para
 * esas se cae a la cotización de hoy como mejor esfuerzo, igual que hace el
 * panel. Sin ese respaldo quedaban afuera de los gráficos sin aviso, y los
 * totales de Análisis no coincidían con los del panel.
 */
export function toARS(t: Transaccion, cotiz: Cotizaciones): number | null {
  const moneda = t.moneda ?? "ARS";
  if (moneda === "ARS") return Number(t.monto);
  const tasa = moneda === "USD" ? (t.cotizacion_usd ?? cotiz.USD) : (t.cotizacion_eur ?? cotiz.EUR);
  return tasa ? Number(t.monto) * tasa : null;
}

/**
 * Ventana de fechas del período. "3m"/"6m" cuentan el mes actual más los 2/5
 * anteriores, "1a" arranca en enero, "todo" no recorta, y "mes_pasado" es el
 * último mes calendario completo (por eso es el único que necesita `hasta`).
 */
export function rangoPeriodo(periodo: Periodo, hoy: Date): { desde: Date | null; hasta: Date | null } {
  if (periodo === "todo") return { desde: null, hasta: null };
  const desde = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  let hasta: Date | null = null;
  if (periodo === "mes_pasado") {
    desde.setMonth(desde.getMonth() - 1);
    hasta = new Date(hoy.getFullYear(), hoy.getMonth(), 0); // último día del mes anterior
  } else if (periodo === "3m") desde.setMonth(desde.getMonth() - 2);
  else if (periodo === "6m") desde.setMonth(desde.getMonth() - 5);
  else if (periodo === "1a") desde.setMonth(0);
  return { desde, hasta };
}

/**
 * Cuántos meses dibujar y en qué mes terminan (`endOffset` 0 = mes en curso,
 * 1 = mes pasado). Para "todo" se calcula desde la transacción más vieja de
 * `lista`, que llega filtrada por tipo/moneda/categoría pero SIN el recorte
 * de fecha, para saber dónde arranca el historial real.
 */
export function rangoMeses(
  periodo: Periodo,
  lista: Transaccion[],
  hoy: Date,
): { n: number; endOffset: number } {
  if (periodo === "mes_pasado") return { n: 1, endOffset: 1 };
  if (periodo === "1m") return { n: 1, endOffset: 0 };
  if (periodo === "3m") return { n: 3, endOffset: 0 };
  if (periodo === "6m") return { n: 6, endOffset: 0 };
  if (periodo === "1a") return { n: hoy.getMonth() + 1, endOffset: 0 };

  let minFecha: Date | null = null;
  for (const t of lista) {
    const f = parseFecha(t.fecha);
    if (!minFecha || f < minFecha) minFecha = f;
  }
  if (!minFecha) return { n: 1, endOffset: 0 };
  const n =
    (hoy.getFullYear() - minFecha.getFullYear()) * 12 + (hoy.getMonth() - minFecha.getMonth()) + 1;
  return { n: Math.max(1, Math.min(n, 60)), endOffset: 0 };
}

/** Las fechas llegan como YYYY-MM-DD; el sufijo evita que se lean como UTC. */
export function parseFecha(iso: string): Date {
  return new Date(iso + "T00:00:00");
}

function pasaFiltrosNoFecha(t: Transaccion, f: Filtros): boolean {
  if (f.tipo && t.tipo !== f.tipo) return false;
  // Cada lado tiene su propia lista de monedas permitidas.
  const permitidas = t.tipo === "Ingreso" ? f.monedasIng : f.monedasGas;
  if (!permitidas.includes(t.moneda ?? "ARS")) return false;
  if (f.categoria && normalizar(t.categoria) !== normalizar(f.categoria)) return false;
  return true;
}

export function categoriasDisponibles(datos: Transaccion[]): string[] {
  const vistas = new Map<string, string>();
  for (const t of datos) {
    const c = (t.categoria ?? "").trim();
    if (c && !vistas.has(normalizar(c))) vistas.set(normalizar(c), c);
  }
  return [...vistas.values()].sort((a, b) => a.localeCompare(b));
}

export function calcularAnalisis(
  datos: Transaccion[],
  filtros: Filtros,
  lang: Lang,
  cotiz: Cotizaciones,
  hoy: Date = new Date(),
): Analisis {
  const mesesCortos = MESES_CORTOS[lang];

  // Sin recortar por fecha: rangoMeses lo necesita para saber desde cuándo
  // hay historial cuando el período es "todo".
  const sinRecortarFecha = datos.filter((t) => pasaFiltrosNoFecha(t, filtros));
  const { desde, hasta } = rangoPeriodo(filtros.periodo, hoy);
  const lista = sinRecortarFecha.filter((t) => {
    const f = parseFecha(t.fecha);
    if (desde && f < desde) return false;
    if (hasta && f > hasta) return false;
    return true;
  });

  const { n: nMeses, endOffset } = rangoMeses(filtros.periodo, sinRecortarFecha, hoy);

  const meses: MesSerie[] = [];
  for (let i = nMeses - 1; i >= 0; i--) {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - endOffset - i, 1);
    meses.push({
      key: `${d.getFullYear()}-${d.getMonth()}`,
      label: `${mesesCortos[d.getMonth()]} '${String(d.getFullYear()).slice(2)}`,
      ing: 0,
      gas: 0,
    });
  }
  const porMes = new Map(meses.map((m) => [m.key, m]));

  let ingTotal = 0;
  let gasTotal = 0;
  const porCategoria = new Map<string, number>();

  for (const t of lista) {
    const ars = toARS(t, cotiz);
    if (ars === null) continue;
    const f = parseFecha(t.fecha);
    const mes = porMes.get(`${f.getFullYear()}-${f.getMonth()}`);
    if (t.tipo === "Ingreso") {
      ingTotal += ars;
      if (mes) mes.ing += ars;
    } else {
      gasTotal += ars;
      if (mes) mes.gas += ars;
      const cat = (t.categoria ?? "").trim() || tr("sin_categoria", lang);
      porCategoria.set(cat, (porCategoria.get(cat) ?? 0) + ars);
    }
  }

  // El promedio nunca cuenta el mes en curso: todavía no terminó y arrastraría
  // el número para abajo. Siempre corta en el último mes ya terminado.
  const mesActualKey = `${hoy.getFullYear()}-${hoy.getMonth()}`;
  const mesesTerminados = meses.filter((m) => m.key !== mesActualKey);
  const gastoTerminados = mesesTerminados.reduce((s, m) => s + m.gas, 0);
  const mesesConDatos = mesesTerminados.filter((m) => m.ing || m.gas).length || 1;

  const categorias = [...porCategoria.entries()]
    .map(([nombre, total]) => ({ nombre, total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 8);

  return {
    meses,
    ingTotal,
    gasTotal,
    balanceNeto: ingTotal - gasTotal,
    promedioMensual: gastoTerminados / mesesConDatos,
    categorias,
    hayDatosMensuales: meses.some((m) => m.ing || m.gas),
  };
}
