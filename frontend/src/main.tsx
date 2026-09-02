import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "@/App";
import { PreferenciasProvider } from "@/hooks/usePreferencias";
import { ToastProvider } from "@/hooks/useToast";
import "@/styles/tokens.css";
import "@/styles/base.css";

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
    <QueryClientProvider client={queryClient}>
      <PreferenciasProvider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </PreferenciasProvider>
    </QueryClientProvider>
  </StrictMode>,
);
