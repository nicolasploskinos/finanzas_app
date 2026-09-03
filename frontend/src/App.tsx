import { lazy, Suspense, useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

/**
 * Cada página se baja por separado (code splitting): el bundle inicial deja
 * de arrastrar Chart.js y el resto de las pantallas que quizás nunca se
 * abren. Los componentes son exports nombrados, de ahí el `.then`.
 */
const DashboardPage = lazy(() =>
  import("@/features/dashboard/DashboardPage").then((m) => ({ default: m.DashboardPage })),
);
const AnalisisPage = lazy(() =>
  import("@/features/analisis/AnalisisPage").then((m) => ({ default: m.AnalisisPage })),
);
const ViajesPage = lazy(() =>
  import("@/features/viajes/ViajesPage").then((m) => ({ default: m.ViajesPage })),
);
const LoginPage = lazy(() =>
  import("@/features/auth/LoginPage").then((m) => ({ default: m.LoginPage })),
);
const LandingPage = lazy(() =>
  import("@/features/landing/LandingPage").then((m) => ({ default: m.LandingPage })),
);
const TerminosPage = lazy(() =>
  import("@/features/legal/TerminosPage").then((m) => ({ default: m.TerminosPage })),
);
const PrivacidadPage = lazy(() =>
  import("@/features/legal/PrivacidadPage").then((m) => ({ default: m.PrivacidadPage })),
);

/**
 * Con navegación del lado del cliente el navegador ya no reinicia el scroll
 * solo: si venías scrolleado abajo en el panel, Análisis abría a mitad de
 * página. Esto lo devuelve arriba en cada cambio de ruta.
 */
function IrArribaAlNavegar() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

/** Puente mientras se baja el pedazo de la página; en cache es imperceptible. */
function Cargando() {
  return <div style={{ minHeight: "100vh", background: "var(--bg)" }} />;
}

/**
 * Todas las páginas de la app ya están migradas. Solo quedan afuera de
 * este router los endpoints que no son HTML (la API, el manifest/service
 * worker de la PWA) y los webhooks de pagos/WhatsApp, que Flask sigue
 * sirviendo directo.
 */
export function App() {
  return (
    <BrowserRouter>
      <IrArribaAlNavegar />
      <Suspense fallback={<Cargando />}>
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
      </Suspense>
    </BrowserRouter>
  );
}
