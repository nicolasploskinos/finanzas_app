import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/client";
import type {
  Cotizaciones,
  Cuenta,
  ImportPreview,
  InflacionPunto,
  Presupuesto,
  Recurrente,
  Sesion,
  StatsMes,
  Transaccion,
  TransaccionViaje,
  Viaje,
  ViajeDetalle,
  ViajePayload,
  WhatsappEstado,
} from "@/api/types";

export const claves = {
  sesion: ["sesion"] as const,
  transacciones: ["transacciones"] as const,
  transaccionesRango: (r: { desde: string | null; hasta: string | null }) =>
    ["transacciones", r.desde ?? "inicio", r.hasta ?? "hoy"] as const,
  categorias: ["categorias"] as const,
  authConfig: ["auth-config"] as const,
  viajes: ["viajes"] as const,
  viaje: (id: number) => ["viajes", id] as const,
  cotizaciones: ["cotizaciones"] as const,
  presupuestos: ["presupuestos"] as const,
  recurrentes: ["recurrentes"] as const,
  stats: (mes: number, anio: number) => ["stats", mes, anio] as const,
  inflacion: ["inflacion"] as const,
  whatsappEstado: ["whatsapp", "estado"] as const,
  cuenta: ["cuenta"] as const,
};

export function useSesion() {
  return useQuery({
    queryKey: claves.sesion,
    queryFn: () => api.get<Sesion>("/api/montor/me"),
    staleTime: 5 * 60 * 1000,
  });
}

/** Ventana de fechas a pedir. `null` en un extremo = sin tope de ese lado. */
export type RangoFechas = { desde: string | null; hasta: string | null };

/**
 * Trae sólo el rango que la pantalla está mostrando, en vez de bajarse todo
 * el historial en cada carga: con años de movimientos esa consulta crecía
 * sin techo. Cada rango se cachea por separado, así volver a un período ya
 * visitado es instantáneo, y mientras llega uno nuevo se siguen mostrando
 * los datos anteriores en lugar de vaciar la pantalla.
 */
export function useTransacciones(rango: RangoFechas = { desde: null, hasta: null }) {
  const params = new URLSearchParams();
  if (rango.desde) params.set("desde", rango.desde);
  if (rango.hasta) params.set("hasta", rango.hasta);
  const qs = params.toString();

  return useQuery({
    queryKey: claves.transaccionesRango(rango),
    queryFn: () => api.get<Transaccion[]>(`/api/montor${qs ? `?${qs}` : ""}`),
    placeholderData: keepPreviousData,
  });
}

/**
 * Categorías ya usadas, con su frecuencia. Van por separado de las
 * transacciones porque esas ahora llegan recortadas al período visible, y
 * el autocompletado y el filtro por categoría necesitan todo el historial.
 */
export function useCategorias() {
  return useQuery({
    queryKey: claves.categorias,
    queryFn: () => api.get<Array<{ nombre: string; usos: number }>>("/api/montor/categorias"),
    staleTime: 5 * 60 * 1000,
  });
}

// `habilitado` en true por default: en la página de Viajes siempre hace
// falta. El panel principal (selector de viaje en el modal de carga) lo
// pasa en false para usuarios free, que no tienen acceso a este endpoint.
export function useViajes(habilitado = true) {
  return useQuery({
    queryKey: claves.viajes,
    queryFn: () => api.get<Viaje[]>("/api/montor/viajes"),
    enabled: habilitado,
  });
}

export function useViaje(id: number | null) {
  return useQuery({
    queryKey: claves.viaje(id ?? 0),
    queryFn: () => api.get<ViajeDetalle>(`/api/montor/viajes/${id}`),
    enabled: id !== null,
  });
}

/** Crea o edita según venga `id`; en los dos casos la lista queda obsoleta. */
export function useGuardarViaje() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...datos }: ViajePayload & { id?: number }) =>
      id
        ? api.put<Viaje>(`/api/montor/viajes/${id}`, datos)
        : api.post<Viaje>("/api/montor/viajes", datos),
    // `exact` en la lista no es opcional: las claves de detalle son
    // ["viajes", id], así que invalidar ["viajes"] sin `exact` las arrastra a
    // todas por prefijo. Acá el detalle se invalida a propósito y solo el que
    // se editó.
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: claves.viajes, exact: true });
      if (id) qc.invalidateQueries({ queryKey: claves.viaje(id) });
    },
  });
}

export function useBorrarViaje() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del<{ ok: boolean }>(`/api/montor/viajes/${id}`),
    // El detalle se saca de la cache en vez de invalidarse: invalidarlo lo
    // haría refetchear un viaje que ya no existe y devolver 404.
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: claves.viaje(id) });
      qc.invalidateQueries({ queryKey: claves.viajes, exact: true });
    },
  });
}

/**
 * Desvincular una transacción del viaje es un PUT de la transacción entera con
 * `viaje_id` en null: el endpoint reemplaza la fila, así que hay que mandar
 * todos los campos, no solo el que cambia.
 */
export function useQuitarDelViaje(viajeId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (tx: TransaccionViaje) =>
      api.put<unknown>(`/api/montor/${tx.id}`, { ...tx, viaje_id: null }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.viaje(viajeId) });
      qc.invalidateQueries({ queryKey: claves.viajes, exact: true });
    },
  });
}

export type LoginPayload = { username: string; password: string };

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datos: LoginPayload) => api.post<{ ok: true }>("/api/montor/login", datos),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.sesion }),
  });
}

export function useRegistro() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datos: LoginPayload) => api.post<{ ok: true }>("/api/montor/register", datos),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.sesion }),
  });
}

// ── Panel principal ─────────────────────────────────────────────────────────

export function useCotizaciones() {
  return useQuery({
    queryKey: claves.cotizaciones,
    queryFn: () => api.get<Cotizaciones>("/api/montor/cotizaciones"),
    staleTime: 5 * 60 * 1000,
  });
}

export type TransaccionPayload = {
  tipo: Transaccion["tipo"];
  monto: number;
  fecha: string;
  categoria: string;
  descripcion: string;
  moneda: Transaccion["moneda"];
  viaje_id: number | null;
};

function invalidarTrasEscribirTx(qc: ReturnType<typeof useQueryClient>) {
  // Sin `exact`: las claves por rango son ["transacciones", desde, hasta],
  // así que esto las alcanza a todas por prefijo.
  qc.invalidateQueries({ queryKey: claves.transacciones });
  // La transacción pudo estrenar una categoría nueva.
  qc.invalidateQueries({ queryKey: claves.categorias });
  qc.invalidateQueries({ queryKey: claves.presupuestos });
  // "stats" no lleva `exact` a propósito: cualquier mes pudo cambiar de
  // total, así que se invalidan todas las combinaciones mes/año en caché.
  qc.invalidateQueries({ queryKey: ["stats"] });
}

export function useCrearTx() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (tx: TransaccionPayload) => api.post<Transaccion>("/api/montor", tx),
    onSuccess: () => invalidarTrasEscribirTx(qc),
  });
}

export function useEditarTx() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...tx }: TransaccionPayload & { id: number }) =>
      api.put<Transaccion>(`/api/montor/${id}`, tx),
    onSuccess: () => invalidarTrasEscribirTx(qc),
  });
}

export function useBorrarTx() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del<{ ok: boolean }>(`/api/montor/${id}`),
    onSuccess: () => invalidarTrasEscribirTx(qc),
  });
}

/** Qué formas de ingreso están habilitadas (hoy: si hay Google configurado).
 *  Se consulta para no mostrar un botón que llevaría a un error. */
export function useAuthConfig() {
  return useQuery({
    queryKey: claves.authConfig,
    queryFn: () => api.get<{ google: boolean }>("/api/montor/auth/config"),
    staleTime: Infinity, // depende de la config del server, no cambia en la sesión
  });
}

/** Borra de una los movimientos de ejemplo de la cuenta nueva. */
export function useBorrarEjemplos() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.del<{ ok: boolean }>("/api/montor/ejemplos"),
    onSuccess: () => invalidarTrasEscribirTx(qc),
  });
}

export function usePresupuestos() {
  return useQuery({
    queryKey: claves.presupuestos,
    queryFn: () => api.get<Presupuesto[]>("/api/montor/presupuestos"),
  });
}

export function useGuardarPresupuesto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datos: { categoria: string; monto: number; moneda: Presupuesto["moneda"] }) =>
      api.post<Presupuesto>("/api/montor/presupuestos", datos),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.presupuestos }),
  });
}

export function useBorrarPresupuesto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del<{ ok: boolean }>(`/api/montor/presupuestos/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.presupuestos }),
  });
}

/** Los recurrentes solo se piden cuando el acordeón está abierto. */
export function useRecurrentes(habilitado: boolean) {
  return useQuery({
    queryKey: claves.recurrentes,
    queryFn: () => api.get<Recurrente[]>("/api/montor/recurrentes"),
    enabled: habilitado,
  });
}

export type RecurrentePayload = TransaccionPayload & { frecuencia: Recurrente["frecuencia"] };

export function useCrearRecurrente() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datos: RecurrentePayload) => api.post<Recurrente>("/api/montor/recurrentes", datos),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.recurrentes }),
  });
}

export function useBorrarRecurrente() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.del<{ ok: boolean }>(`/api/montor/recurrentes/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.recurrentes }),
  });
}

/** Stats (resumen del mes + categorías) solo se piden con el acordeón
 *  abierto y cuenta Pro. */
export function useStats(mes: number, anio: number, habilitado: boolean) {
  return useQuery({
    queryKey: claves.stats(mes, anio),
    queryFn: () => api.get<StatsMes>(`/api/montor/stats?mes=${mes}&anio=${anio}`),
    enabled: habilitado,
  });
}

export function useInflacion(habilitado: boolean) {
  return useQuery({
    queryKey: claves.inflacion,
    queryFn: () => api.get<InflacionPunto[]>("/api/montor/inflacion"),
    enabled: habilitado,
  });
}

/** Resumen con IA: mutation (no query) porque es una acción explícita del
 *  usuario ("Generar resumen"), no algo que se precargue solo. */
export function useResumenIA() {
  return useMutation({
    mutationFn: ({ mes, anio, lang }: { mes: number; anio: number; lang: string }) =>
      api.get<{ ok: boolean; resumen?: string; error?: string }>(
        `/api/montor/resumen-ia?mes=${mes}&anio=${anio}&lang=${lang}`,
      ),
  });
}

export function useWhatsappEstado(habilitado: boolean) {
  return useQuery({
    queryKey: claves.whatsappEstado,
    queryFn: () => api.get<WhatsappEstado>("/api/montor/whatsapp/estado"),
    enabled: habilitado,
  });
}

export function useWhatsappCodigo() {
  return useMutation({
    mutationFn: () =>
      api.post<{ ok: boolean; codigo: string; wa_link: string }>("/api/montor/whatsapp/codigo", {}),
  });
}

export function useWhatsappDesvincular() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.del<{ ok: boolean }>("/api/montor/whatsapp/desvincular"),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.whatsappEstado }),
  });
}

export function useImportPreview() {
  return useMutation({
    mutationFn: (archivo: File) => {
      const fd = new FormData();
      fd.append("archivo", archivo);
      return api.postForm<ImportPreview>("/api/montor/import/preview", fd);
    },
  });
}

export function useImportConfirm() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (transacciones: unknown[]) =>
      api.post<{ ok: boolean; insertados: number }>("/api/montor/import/confirm", { transacciones }),
    onSuccess: () => invalidarTrasEscribirTx(qc),
  });
}

/** Perfil: solo se pide al abrir el modal, no en cada carga del panel. */
export function useCuenta(habilitado: boolean) {
  return useQuery({
    queryKey: claves.cuenta,
    queryFn: () => api.get<Cuenta>("/api/montor/cuenta"),
    enabled: habilitado,
  });
}

export function useCambiarNombre() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (username: string) => api.put<{ ok: boolean; username: string }>("/api/montor/cuenta/nombre", { username }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.cuenta, exact: true });
      qc.invalidateQueries({ queryKey: claves.sesion, exact: true });
    },
  });
}

export function useCambiarPassword() {
  return useMutation({
    mutationFn: (datos: { actual: string; nueva: string }) =>
      api.put<{ ok: boolean }>("/api/montor/cuenta/password", datos),
  });
}

export function useCancelarSuscripcion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ ok: boolean }>("/api/montor/cuenta/cancelar-suscripcion", {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claves.cuenta, exact: true });
      qc.invalidateQueries({ queryKey: claves.sesion, exact: true });
    },
  });
}
