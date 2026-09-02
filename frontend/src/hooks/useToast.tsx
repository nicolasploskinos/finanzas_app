import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

import css from "@/components/Toast.module.css";

const Ctx = createContext<((mensaje: string) => void) | null>(null);

const DURACION_MS = 2500;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [mensaje, setMensaje] = useState("");
  const [visible, setVisible] = useState(false);
  const timer = useRef<number | undefined>(undefined);

  const toast = useCallback((texto: string) => {
    setMensaje(texto);
    setVisible(true);
    // Un toast nuevo reinicia el reloj en vez de heredar el del anterior.
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setVisible(false), DURACION_MS);
  }, []);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  return (
    <Ctx.Provider value={toast}>
      {children}
      <div className={`${css.toast} ${visible ? css.show : ""}`} role="status" aria-live="polite">
        {mensaje}
      </div>
    </Ctx.Provider>
  );
}

export function useToast() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast necesita estar dentro de <ToastProvider>");
  return ctx;
}
