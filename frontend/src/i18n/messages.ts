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
  pasar_a_pro: { es: "⭐ Pasar a Pro", en: "⭐ Upgrade to Pro" },
  perfil_tab: { es: "Perfil", en: "Profile" },
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
    es: "Ingresos vs. gastos por mes",
    en: "Income vs. expenses per month",
  },
  cat_principales: { es: "Categorías principales", en: "Top categories" },
  tendencia_saldo: { es: "Tendencia del saldo", en: "Balance trend" },
  // Filtro de monedas por lado (ingresos / gastos)
  ingresos: { es: "Ingresos", en: "Income" },
  gastos: { es: "Gastos", en: "Expenses" },
  monedas: { es: "Monedas", en: "Currencies" },
  nota_conversion: {
    es: "Los totales suman todas las monedas elegidas, convertidas a ARS con la cotización del día de cada movimiento.",
    en: "Totals add up every selected currency, converted to ARS using each transaction's own exchange rate.",
  },
  sin_monedas: {
    es: "Elegí al menos una moneda para ver datos.",
    en: "Pick at least one currency to see data.",
  },
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
  // Viajes
  viajes_solo_pro: { es: "⭐ Viajes es una función Pro", en: "⭐ Trips is a Pro feature" },
  viajes_solo_pro_detalle: {
    es: "Organizá tus viajes y mirá cuánto gastaste en cada uno, por día. Necesitás una cuenta Pro para usar esta sección.",
    en: "Organize your trips and see how much you spent on each one, per day. You need a Pro account to use this section.",
  },
  volver_a_montor: { es: "Volver a Montor", en: "Back to Montor" },
  nuevo_viaje: { es: "Nuevo viaje", en: "New trip" },
  editar_viaje: { es: "Editar viaje", en: "Edit trip" },
  nombre: { es: "Nombre", en: "Name" },
  desde: { es: "Desde", en: "From" },
  hasta: { es: "Hasta", en: "To" },
  ejemplo_viaje: { es: "Ej: Brasil 2026", en: "E.g.: Brazil 2026" },
  guardar_viaje: { es: "Guardar viaje", en: "Save trip" },
  guardando: { es: "Guardando…", en: "Saving…" },
  editar: { es: "Editar", en: "Edit" },
  eliminar: { es: "Eliminar", en: "Delete" },
  gastado: { es: "Gastado", en: "Spent" },
  total_gastado: { es: "Total gastado", en: "Total spent" },
  gasto_por_categoria_usd: { es: "Gasto por categoría (USD)", en: "Spend by category (USD)" },
  ver_dias_puntuales: { es: "📅 Ver días puntuales:", en: "📅 View specific days:" },
  a: { es: "a", en: "to" },
  limpiar: { es: "Limpiar ×", en: "Clear ×" },
  sin_viajes: {
    es: "Todavía no armaste ningún viaje. Tocá + para crear el primero.",
    en: "You haven't created any trips yet. Tap + to create the first one.",
  },
  sin_gastos_reg_todavia: { es: "Sin gastos registrados todavía", en: "No expenses recorded yet" },
  sin_gastos_registrados: { es: "Sin gastos registrados", en: "No expenses recorded" },
  todavia_no_cargaste: {
    es: "Todavía no cargaste gastos de este viaje.",
    en: "You haven't logged any expenses for this trip yet.",
  },
  sin_gastos_filtro: { es: "No hay gastos con ese filtro.", en: "No expenses match that filter." },
  sin_tx_viaje: {
    es: "Sin transacciones etiquetadas a este viaje todavía. Etiquetalas desde el formulario de carga en Montor.",
    en: "No transactions tagged to this trip yet. Tag them from the entry form in Montor.",
  },
  missing_trip_fields: { es: "Completá nombre y fechas", en: "Fill in name and dates" },
  fecha_hasta_invalida: {
    es: "La fecha 'hasta' no puede ser anterior a 'desde'",
    en: "The 'to' date can't be before 'from'",
  },
  error_guardar_viaje: { es: "Error al guardar el viaje", en: "Error saving the trip" },
  viaje_guardado: { es: "✓ Viaje guardado", en: "✓ Trip saved" },
  confirm_borrar_viaje: {
    es: "¿Eliminar este viaje? Las transacciones no se borran, solo se desvinculan.",
    en: "Delete this trip? The transactions won't be deleted, just unlinked.",
  },
  no_pudo_cargar_viaje: { es: "No se pudo cargar el viaje", en: "Couldn't load the trip" },
  quitado_del_viaje: { es: "Quitado del viaje", en: "Removed from the trip" },
  quitar_del_viaje: { es: "Quitar del viaje", en: "Remove from the trip" },
  // Login / registro
  montor: { es: "Montor", en: "Montor" },
  administra_ingresos_gastos: {
    es: "Administrá tus ingresos y gastos",
    en: "Manage your income and expenses",
  },
  ingresar: { es: "Ingresar", en: "Sign in" },
  registrarse: { es: "Registrarse", en: "Sign up" },
  usuario: { es: "Usuario", en: "Username" },
  contrasena: { es: "Contraseña", en: "Password" },
  crear_cuenta: { es: "Crear cuenta", en: "Create account" },
  terminos: { es: "Términos", en: "Terms" },
  politica_privacidad: { es: "Política de Privacidad", en: "Privacy Policy" },
  invalid_credentials: {
    es: "Usuario o contraseña incorrectos",
    en: "Incorrect username or password",
  },
  missing_fields: { es: "Completá todos los campos", en: "Fill in all fields" },
  username_taken: { es: "Ese nombre de usuario ya está en uso", en: "That username is already taken" },
  weak_password: {
    es: "La contraseña tiene que tener al menos 8 caracteres",
    en: "Password must be at least 8 characters",
  },
  too_many_attempts: {
    es: "Demasiados intentos. Probá de nuevo en unos minutos",
    en: "Too many attempts. Try again in a few minutes",
  },
  continuar_con_google: { es: "Continuar con Google", en: "Continue with Google" },
  o: { es: "o", en: "or" },
  // Panel de marca del login (solo se ve en pantallas anchas).
  login_titular: {
    es: "Tus pesos y tus dólares, en un solo número",
    en: "Your pesos and your dollars, in a single number",
  },
  login_bajada: {
    es: "La app de finanzas personales que entiende que en Argentina la moneda es complicada.",
    en: "The personal finance app that gets how complicated currency is in Argentina.",
  },
  login_punto_monedas: { es: "Multi-moneda real", en: "Real multi-currency" },
  login_punto_monedas_d: {
    es: "ARS, USD y EUR a cotización oficial BNA",
    en: "ARS, USD, and EUR at the official BNA rate",
  },
  login_punto_viajes: { es: "Viajes en dólares", en: "Trips in dollars" },
  login_punto_viajes_d: {
    es: "El total del viaje, sin importar en qué moneda gastaste",
    en: "The trip total, no matter what currency you spent in",
  },
  login_punto_ia: { es: "Resumen mensual con IA", en: "AI monthly summary" },
  login_punto_ia_d: {
    es: "Un análisis escrito de cero cada mes, no una plantilla",
    en: "An analysis written fresh every month, not a template",
  },
  // Errores que llegan como ?error= al volver de Google.
  google: {
    es: "No pudimos completar el ingreso con Google. Probá de nuevo",
    en: "We couldn't complete the Google sign-in. Please try again",
  },
  google_email: {
    es: "Google no nos dio un email verificado para esa cuenta",
    en: "Google didn't give us a verified email for that account",
  },
  google_state: {
    es: "El ingreso con Google venció. Probá de nuevo",
    en: "The Google sign-in expired. Please try again",
  },
  google_no_configurado: {
    es: "El ingreso con Google no está disponible por ahora",
    en: "Google sign-in isn't available right now",
  },
} as const;

export type MsgKey = keyof typeof MSG;

export function tr(key: MsgKey, lang: Lang): string {
  return MSG[key][lang];
}

export const MESES_CORTOS: Record<Lang, string[]> = {
  es: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
};
