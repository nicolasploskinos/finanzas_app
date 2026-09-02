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
