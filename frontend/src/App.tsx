import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AnalisisPage } from "@/features/analisis/AnalisisPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { PrivacidadPage } from "@/features/legal/PrivacidadPage";
import { TerminosPage } from "@/features/legal/TerminosPage";
import { ViajesPage } from "@/features/viajes/ViajesPage";

/**
 * Solo las rutas ya migradas viven acá. La landing (`/`) y el panel
 * (`/montor`) siguen en Flask con Jinja, así que se enlazan con <a>
 * normales y no pasan por este router.
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
        <Route path="*" element={<Navigate to="/montor/analisis" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
