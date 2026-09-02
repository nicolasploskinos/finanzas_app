import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AnalisisPage } from "@/features/analisis/AnalisisPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { PrivacidadPage } from "@/features/legal/PrivacidadPage";
import { TerminosPage } from "@/features/legal/TerminosPage";
import { ViajesPage } from "@/features/viajes/ViajesPage";

/**
 * Todas las páginas de la app ya están migradas. Solo quedan afuera de
 * este router los endpoints que no son HTML (la API, el manifest/service
 * worker de la PWA) y los webhooks de pagos/WhatsApp, que Flask sigue
 * sirviendo directo.
 */
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/montor" element={<DashboardPage />} />
        <Route path="/montor/analisis" element={<AnalisisPage />} />
        <Route path="/montor/viajes" element={<ViajesPage />} />
        <Route path="/montor/login" element={<LoginPage />} />
        <Route path="/terminos" element={<TerminosPage />} />
        <Route path="/privacidad" element={<PrivacidadPage />} />
        <Route path="/" element={<LandingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
