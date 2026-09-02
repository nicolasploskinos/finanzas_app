export type Tipo = "Gasto" | "Ingreso";
export type Moneda = "ARS" | "USD" | "EUR";

export type Transaccion = {
  id: number;
  tipo: Tipo;
  categoria: string | null;
  descripcion: string | null;
  monto: number;
  moneda: Moneda | null;
  fecha: string; // YYYY-MM-DD
  cotizacion_usd: number | null;
  cotizacion_eur: number | null;
  viaje_id: number | null;
};

export type Sesion = {
  username: string;
  is_pro: boolean;
  is_trial: boolean;
  trial_dias: number;
  whatsapp_habilitado: boolean;
};

export type Viaje = {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  /** Total gastado en el viaje, convertido a cada moneda por el backend. */
  gastado?: Record<Moneda, number>;
};

/** Transacción de un viaje: el detalle agrega el monto ya pasado a dólares. */
export type TransaccionViaje = Transaccion & { monto_usd: number | null };

export type ViajeDetalle = {
  viaje: Viaje;
  transacciones: TransaccionViaje[];
  totales: Record<Moneda, number>;
  por_categoria: Record<Moneda, Array<{ nombre: string; total: number }>>;
};

export type ViajePayload = {
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
};

export type Cotizaciones = { USD: number | null; EUR: number | null };

export type Frecuencia = "semanal" | "mensual";

export type Recurrente = {
  id: number;
  tipo: Tipo;
  monto: number;
  categoria: string | null;
  descripcion: string | null;
  moneda: Moneda | null;
  frecuencia: Frecuencia;
  proxima_fecha: string;
  activo: boolean;
  creado_en: string;
};

export type Presupuesto = {
  id: number;
  categoria: string;
  monto: number;
  moneda: Moneda | null;
};

export type StatsCategoria = { nombre: string; total: number };

export type StatsResumen = {
  gastos_actual: number;
  ingresos_actual: number;
  gastos_anterior: number;
  ingresos_anterior: number;
  mes_actual: string;
  mes_anterior: string;
};

export type StatsMes = {
  categorias: StatsCategoria[];
  resumen: StatsResumen;
  count_mes: number;
};

export type InflacionPunto = { mes: string; ipc: number };

export type WhatsappEstado =
  | { vinculado: true; telefono_oculto: string }
  | { vinculado: false };

export type ImportRow = {
  fecha: string;
  tipo: Tipo;
  monto: number;
  descripcion: string;
  categoria: string;
  moneda: Moneda;
};

export type ImportPreview = {
  ok: true;
  transacciones: ImportRow[];
  errores: number;
};
