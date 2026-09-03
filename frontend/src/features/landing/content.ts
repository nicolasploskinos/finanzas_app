export type Bi = { es: string; en: string };

export const NAV_LINKS: Array<{ href: string; label: Bi }> = [
  { href: "#demo", label: { es: "Capturas", en: "Screenshots" } },
  { href: "#features", label: { es: "Funciones", en: "Features" } },
  { href: "#para-quien", label: { es: "Para quién", en: "Who it's for" } },
  { href: "#precio", label: { es: "Precio", en: "Pricing" } },
  { href: "#faq", label: { es: "FAQ", en: "FAQ" } },
];

export const MARQUEE_ITEMS: Bi[] = [
  { es: "Multi-moneda real", en: "Real multi-currency" },
  { es: "Cotización oficial BNA", en: "Official BNA exchange rate" },
  { es: "Gastos recurrentes", en: "Recurring expenses" },
  { es: "Resumen con IA", en: "AI-written summary" },
  { es: "Viajes en dólares", en: "Trips in dollars" },
];

export const HERO_TILES: Array<{ tile: "blue" | "purple" | "green"; icon: string; title: Bi; body: Bi }> = [
  {
    tile: "blue",
    icon: "💵",
    title: { es: "MULTI-MONEDA REAL", en: "REAL MULTI-CURRENCY" },
    body: {
      es: "ARS, USD y EUR, a la cotización oficial BNA.",
      en: "ARS, USD, and EUR, at the official BNA rate.",
    },
  },
  {
    tile: "purple",
    icon: "✈️",
    title: { es: "VIAJES, EN DÓLARES", en: "TRIPS, IN DOLLARS" },
    body: {
      es: "Etiquetá gastos a un viaje y mirá el total, sin importar la moneda.",
      en: "Tag expenses to a trip and see the total, no matter the currency.",
    },
  },
  {
    tile: "green",
    icon: "🤖",
    title: { es: "RESUMEN MENSUAL CON IA", en: "AI MONTHLY SUMMARY" },
    body: {
      es: "Un resumen distinto cada mes, escrito por IA — no una plantilla.",
      en: "A different AI-written summary every month — not a template.",
    },
  },
];

export const FEATURES: Array<{ icon: string; title: Bi; body: Bi; slot?: "converter" }> = [
  {
    icon: "💱",
    title: { es: "Probá la conversión en vivo", en: "Try the conversion live" },
    body: {
      es: "Escribí un monto y mirá cómo se convierte en el momento.",
      en: "Type an amount and watch it convert in real time.",
    },
    slot: "converter",
  },
  {
    icon: "🎯",
    title: { es: "Presupuestos por categoría", en: "Budgets by category" },
    body: {
      es: "Definí un límite mensual por categoría y una barra te avisa cuando te vas pasando.",
      en: "Set a monthly limit per category and a bar warns you as you get close.",
    },
  },
  {
    icon: "🔄",
    title: { es: "Gastos recurrentes", en: "Recurring expenses" },
    body: {
      es: "Alquiler, suscripciones o el gimnasio: configurás una vez y se cargan solos cada mes.",
      en: "Rent, subscriptions, the gym: set it up once and it's added automatically every month.",
    },
  },
  {
    icon: "📈",
    title: { es: "Análisis y tendencias", en: "Trends and analysis" },
    body: {
      es: "Ingresos, gastos y categorías principales, mes a mes.",
      en: "Income, expenses, and top categories, month by month.",
    },
  },
  {
    icon: "📊",
    title: { es: "Saldo consolidado", en: "Consolidated balance" },
    body: {
      es: "Un solo número, en la moneda que elijas, sin importar en cuál ganás o gastás.",
      en: "One single number, in whichever currency you pick — no matter where you earn or spend.",
    },
  },
  {
    icon: "📥",
    title: { es: "Importá tus movimientos", en: "Import your transactions" },
    body: {
      es: "Subí el CSV de tu banco y la app reconoce todo sola. Vos confirmás antes de cargar.",
      en: "Upload your bank's CSV and the app figures it out on its own. You confirm before it loads.",
    },
  },
  {
    icon: "📤",
    title: { es: "Exportá a Excel o PDF", en: "Export to Excel or PDF" },
    body: {
      es: "Descargá tu historial en Excel o PDF, listo para guardar o compartir.",
      en: "Download your history as Excel or PDF, ready to save or share.",
    },
  },
  {
    icon: "🔍",
    title: { es: "Buscá y filtrá rápido", en: "Search and filter fast" },
    body: {
      es: "Buscá por texto, categoría o rango de fechas y encontrá cualquier transacción en segundos.",
      en: "Search by text, category, or date range and find any transaction in seconds.",
    },
  },
  {
    icon: "✏️",
    title: { es: "Editable y simple", en: "Editable and simple" },
    body: {
      es: "¿Te equivocaste de monto? Editás cualquier transacción en dos toques.",
      en: "Wrong amount? Edit any transaction in two taps.",
    },
  },
  {
    icon: "📈",
    title: { es: "Análisis mensual + inflación real", en: "Monthly analysis + real inflation" },
    body: {
      es: "Comparación automática con el mes anterior, más el índice de inflación del INDEC.",
      en: "Automatic comparison with last month, plus INDEC's inflation index.",
    },
  },
  {
    icon: "🔐",
    title: { es: "Tus datos, solo tuyos", en: "Your data, only yours" },
    body: {
      es: "No compartimos ni vendemos tus datos. Borrás tu cuenta y se elimina todo.",
      en: "We don't share or sell your data. Delete your account and everything's gone.",
    },
  },
];

export const CHECKLIST: Bi[] = [
  {
    es: "Trabajás en relación de dependencia y también en freelance en dólares",
    en: "You have a regular job and also freelance in dollars",
  },
  {
    es: "Querés saber cuánto gastás por mes, pero en pesos y dólares juntos",
    en: "You want to know how much you spend per month, in pesos and dollars together",
  },
  {
    es: "Tenés gastos fijos que se repiten y te olvidás de anotarlos",
    en: "You have fixed expenses that repeat and you forget to log them",
  },
  {
    es: "Probaste Excel o Google Sheets pero se volvió demasiado complejo",
    en: "You tried Excel or Google Sheets but it got too complicated",
  },
  {
    es: "Querés una app que entienda que en Argentina la moneda es complicada",
    en: "You want an app that understands currency is complicated in Argentina",
  },
];

export type PrecioFeature = { texto: Bi; incluido: boolean };

export const PRECIO_FREE_FEATURES: PrecioFeature[] = [
  {
    incluido: true,
    texto: {
      es: "50 transacciones por mes (la app te avisa cuando te acercás)",
      en: "50 transactions per month (the app warns you as you get close)",
    },
  },
  { incluido: true, texto: { es: "Multi-moneda (ARS, USD, EUR)", en: "Multi-currency (ARS, USD, EUR)" } },
  { incluido: true, texto: { es: "Cotización BNA automática", en: "Automatic BNA exchange rate" } },
  { incluido: true, texto: { es: "Presupuestos por categoría", en: "Budgets by category" } },
  { incluido: true, texto: { es: "Historial últimos 3 meses", en: "Last 3 months of history" } },
  { incluido: false, texto: { es: "Viajes con seguimiento en dólares", en: "Trips tracked in dollars" } },
  { incluido: false, texto: { es: "Gastos recurrentes", en: "Recurring expenses" } },
  { incluido: false, texto: { es: "Gráfico y resumen mensual con IA", en: "Chart and AI-written monthly summary" } },
  { incluido: false, texto: { es: "Exportar a Excel / PDF", en: "Export to Excel / PDF" } },
  { incluido: false, texto: { es: "Importar movimientos bancarios", en: "Import bank statements" } },
];

export const PRECIO_PRO_FEATURES: PrecioFeature[] = [
  { incluido: true, texto: { es: "Transacciones ilimitadas", en: "Unlimited transactions" } },
  { incluido: true, texto: { es: "Multi-moneda (ARS, USD, EUR)", en: "Multi-currency (ARS, USD, EUR)" } },
  { incluido: true, texto: { es: "Cotización BNA automática", en: "Automatic BNA exchange rate" } },
  { incluido: true, texto: { es: "Presupuestos por categoría", en: "Budgets by category" } },
  { incluido: true, texto: { es: "Viajes con seguimiento en dólares", en: "Trips tracked in dollars" } },
  { incluido: true, texto: { es: "Gráfico y resumen mensual con IA", en: "Chart and AI-written monthly summary" } },
  { incluido: true, texto: { es: "Historial completo", en: "Full history" } },
  { incluido: true, texto: { es: "Gastos recurrentes automáticos", en: "Automatic recurring expenses" } },
  { incluido: true, texto: { es: "Exportar a Excel, PDF o CSV", en: "Export to Excel, PDF, or CSV" } },
  { incluido: true, texto: { es: "Importar movimientos bancarios", en: "Import bank statements" } },
];

export const FAQ_ITEMS: Array<{ q: Bi; a: Bi }> = [
  {
    q: { es: "¿Es seguro cargar mis gastos acá?", en: "Is it safe to log my expenses here?" },
    a: {
      es: "Sí. No guardamos datos bancarios ni contraseñas de tus cuentas — solo los montos y categorías que vos ingresás. La base de datos está cifrada y tu información no se comparte con nadie.",
      en: "Yes. We don't store bank data or your account passwords — only the amounts and categories you enter. The database is encrypted and your information isn't shared with anyone.",
    },
  },
  {
    q: { es: "¿Puedo cancelar Pro cuando quiera?", en: "Can I cancel Pro whenever I want?" },
    a: {
      es: "Sí, desde tu perfil dentro de la app, en dos toques. Ahí mismo ves cuándo es tu próximo cobro y podés cambiar la tarjeta o dar de baja. No hay contratos ni períodos mínimos: al cancelar, tu cuenta vuelve al plan gratis y conservás tus datos.",
      en: "Yes, from your profile inside the app, in two taps. That's also where you see your next charge date and can change your card or cancel. No contracts or minimum periods: when you cancel, your account goes back to the free plan and you keep your data.",
    },
  },
  {
    q: {
      es: "¿Cómo se actualiza la cotización del dólar?",
      en: "How does the dollar exchange rate get updated?",
    },
    a: {
      es: "Automáticamente cada vez que abrís la app. Usamos la cotización oficial del Banco Nación (BNA) vía la API de bluelytics.com.ar.",
      en: "Automatically every time you open the app. We use the official Banco Nación (BNA) rate via the bluelytics.com.ar API.",
    },
  },
  {
    q: { es: "¿Qué pasa si borro mi cuenta?", en: "What happens if I delete my account?" },
    a: {
      es: "Se eliminan todos tus datos permanentemente. No guardamos copias ni hacemos backups de cuentas borradas.",
      en: "All your data is permanently deleted. We don't keep copies or backups of deleted accounts.",
    },
  },
  {
    q: { es: "¿Funciona en el celular?", en: "Does it work on my phone?" },
    a: {
      es: "Sí, está diseñada primero para móvil. Funciona en cualquier navegador (Chrome, Safari, etc.) sin necesidad de instalar nada. También tiene versión de escritorio para Windows.",
      en: "Yes, it's designed mobile-first. It works in any browser (Chrome, Safari, etc.) with nothing to install. There's also a desktop version for Windows.",
    },
  },
];

export const FOOTER_PRODUCT: Array<{ href: string; label: Bi }> = [
  { href: "#demo", label: { es: "Capturas", en: "Screenshots" } },
  { href: "#features", label: { es: "Funciones", en: "Features" } },
  { href: "#precio", label: { es: "Precio", en: "Pricing" } },
  { href: "#faq", label: { es: "FAQ", en: "FAQ" } },
];

export const FOOTER_LEGAL: Array<{ href: string; label: Bi }> = [
  { href: "/privacidad", label: { es: "Privacidad", en: "Privacy" } },
  { href: "/terminos", label: { es: "Términos", en: "Terms" } },
];

export const FOOTER_CUENTA: Array<{ href: string; label: Bi }> = [
  { href: "/montor", label: { es: "Acceder", en: "Sign in" } },
  { href: "/montor/login", label: { es: "Empezar gratis", en: "Start free" } },
];
