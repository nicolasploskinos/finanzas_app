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
