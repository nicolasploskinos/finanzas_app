import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/client";
import type {
  Sesion,
  Transaccion,
  TransaccionViaje,
  Viaje,
  ViajeDetalle,
  ViajePayload,
} from "@/api/types";

export const claves = {
  sesion: ["sesion"] as const,
  transacciones: ["transacciones"] as const,
  viajes: ["viajes"] as const,
  viaje: (id: number) => ["viajes", id] as const,
};

export function useSesion() {
  return useQuery({
    queryKey: claves.sesion,
    queryFn: () => api.get<Sesion>("/api/montor/me"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTransacciones() {
  return useQuery({
    queryKey: claves.transacciones,
    queryFn: () => api.get<Transaccion[]>("/api/montor"),
  });
}

export function useViajes() {
  return useQuery({
    queryKey: claves.viajes,
    queryFn: () => api.get<Viaje[]>("/api/montor/viajes"),
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
      qc.invalidateQueries({ queryKey: claves.transacciones });
    },
  });
}
