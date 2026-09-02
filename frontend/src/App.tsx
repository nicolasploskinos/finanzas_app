import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AnalisisPage } from "@/features/analisis/AnalisisPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { PrivacidadPage } from "@/features/legal/PrivacidadPage";
import { TerminosPage } from "@/features/legal/TerminosPage";
import { ViajesPage } from "@/features/viajes/ViajesPage";

/**
 * Solo las rutas ya migradas viven acá. El panel (`/montor` y sus
 * subpáginas restantes) sigue en Flask con Jinja, así que se enlaza con
 * <a> normales y no pasa por este router.
 */
export function App() {
  return (
    <BrowserRouter>
      <Routes>
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
