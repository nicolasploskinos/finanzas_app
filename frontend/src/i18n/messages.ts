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
} as const;

export type MsgKey = keyof typeof MSG;

export function tr(key: MsgKey, lang: Lang): string {
  return MSG[key][lang];
}

export const MESES_CORTOS: Record<Lang, string[]> = {
  es: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
};
