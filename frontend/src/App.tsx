import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AnalisisPage } from "@/features/analisis/AnalisisPage";
import { ViajesPage } from "@/features/viajes/ViajesPage";

/**
 * Solo las rutas ya migradas viven acá. Las demás (`/montor`, la landing, el
 * login) las sigue sirviendo Flask con Jinja, así que se enlazan con <a>
 * normales y no pasan por este router.
 */
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/montor/analisis" element={<AnalisisPage />} />
        <Route path="/montor/viajes" element={<ViajesPage />} />
        <Route path="*" element={<Navigate to="/montor/analisis" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
