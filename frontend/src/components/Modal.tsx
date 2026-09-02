import { useEffect } from "react";
import type { ReactNode } from "react";

import css from "./Modal.module.css";

type Props = {
  abierto: boolean;
  titulo: string;
  onCerrar: () => void;
  children: ReactNode;
};

export function Modal({ abierto, titulo, onCerrar, children }: Props) {
  // Escape cierra, como cualquier modal. El listener solo existe mientras
  // está abierto para no acumular handlers.
  useEffect(() => {
    if (!abierto) return;
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCerrar();
    };
    document.addEventListener("keydown", alTeclear);
    return () => document.removeEventListener("keydown", alTeclear);
  }, [abierto, onCerrar]);

  return (
    <div
      className={`${css.overlay} ${abierto ? css.open : ""}`}
      // Solo el fondo cierra: un click dentro de la hoja no debe propagarse.
      onClick={(e) => {
        if (e.target === e.currentTarget) onCerrar();
      }}
      role="dialog"
      aria-modal="true"
      aria-hidden={!abierto}
    >
      <div className={css.modal}>
        <div className={css.handle} />
        <h2 className={css.titulo}>{titulo}</h2>
        {children}
      </div>
    </div>
  );
}
