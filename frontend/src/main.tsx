import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "@/App";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { PreferenciasProvider } from "@/hooks/usePreferencias";
import { ToastProvider } from "@/hooks/useToast";
import { escucharErroresGlobales } from "@/lib/reportarError";
import "@/styles/tokens.css";
import "@/styles/base.css";

escucharErroresGlobales();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 30_000,
      retry: 1,
    },
  },
});

const contenedor = document.getElementById("root");
if (!contenedor) throw new Error("Falta el div #root en la plantilla");

createRoot(contenedor).render(
  <StrictMode>
    {/* Afuera de todo: si el que explota es un provider, la pantalla de error
        tiene que seguir siendo capaz de renderizarse. */}
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <PreferenciasProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </PreferenciasProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
);
