import { useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { Sesion, Transaccion } from "@/api/types";

export function useTransacciones() {
  return useQuery({
    queryKey: ["transacciones"],
    queryFn: () => api.get<Transaccion[]>("/api/montor"),
  });
}

export function useSesion() {
  return useQuery({
    queryKey: ["sesion"],
    queryFn: () => api.get<Sesion>("/api/montor/me"),
    staleTime: 5 * 60 * 1000,
  });
}
