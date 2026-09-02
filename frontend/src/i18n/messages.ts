export type Lang = "es" | "en";

/** Claves de texto. `as const` para que `tr()` solo acepte claves reales. */
export const MSG = {
  ingresos_totales: { es: "Ingresos totales", en: "Total income" },
  gastos_totales: { es: "Gastos totales", en: "Total expenses" },
  balance_neto: { es: "Balance neto", en: "Net balance" },
  promedio_mensual: { es: "Promedio mensual de gasto", en: "Avg. monthly spend" },
  sin_categoria: { es: "Sin categoría", en: "No category" },
  todas_categorias: { es: "Todas las categorías", en: "All categories" },
  analisis: { es: "Análisis", en: "Analytics" },
  menu: { es: "Menú", en: "Menu" },
  inicio: { es: "Inicio", en: "Home" },
  nueva_transaccion: { es: "Nueva transacción", en: "New transaction" },
  viajes: { es: "Viajes", en: "Trips" },
  plan_pro: { es: "Plan Pro", en: "Pro plan" },
  plan_gratis: { es: "Plan gratis", en: "Free plan" },
  este_mes: { es: "Este mes", en: "This month" },
  mes_pasado: { es: "Mes pasado", en: "Last month" },
  tres_meses: { es: "3 meses", en: "3 months" },
  seis_meses: { es: "6 meses", en: "6 months" },
  este_anio: { es: "Este año", en: "This year" },
  todo: { es: "Todo", en: "All" },
  todas: { es: "Todas", en: "All" },
  gasto: { es: "Gasto", en: "Expense" },
  ingreso: { es: "Ingreso", en: "Income" },
  ing_vs_gas: {
    es: "Ingresos vs. gastos por mes (ARS)",
    en: "Income vs. expenses per month (ARS)",
  },
  cat_principales: { es: "Categorías principales (ARS)", en: "Top categories (ARS)" },
  tendencia_saldo: { es: "Tendencia del saldo (ARS)", en: "Balance trend (ARS)" },
  sin_datos: { es: "Todavía no hay suficientes datos", en: "Not enough data yet" },
  sin_gastos: { es: "Sin gastos registrados", en: "No expenses recorded" },
  solo_pro: { es: "Análisis es una función Pro", en: "Analytics is a Pro feature" },
  solo_pro_detalle: {
    es: "Pasate a Pro para ver tendencias, comparativas por mes y tus categorías principales.",
    en: "Upgrade to Pro to see trends, month-over-month comparisons and your top categories.",
  },
  ver_planes: { es: "Ver planes →", en: "See plans →" },
  cargando: { es: "Cargando…", en: "Loading…" },
  error_carga: {
    es: "No se pudieron cargar los datos.",
    en: "Could not load the data.",
  },
  reintentar: { es: "Reintentar", en: "Retry" },
} as const;

export type MsgKey = keyof typeof MSG;

export function tr(key: MsgKey, lang: Lang): string {
  return MSG[key][lang];
}

export const MESES_CORTOS: Record<Lang, string[]> = {
  es: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
};
