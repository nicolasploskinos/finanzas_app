import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

import css from "./Confirmacion.module.css";

/**
 * Reemplazo de `confirm()` del navegador.
 *
 * El nativo es un cuadro gris del sistema que no se parece en nada a la app,
 * no se puede escribir distinto según la acción, y en la PWA de iOS a veces
 * aparece cortado. Este va con los colores de Montor y distingue la acción
 * destructiva (rojo) de la común.
 *
 * Se usa igual que antes, sólo que esperando la respuesta:
 *     if (!(await confirmar({ titulo, mensaje, confirmar: "Eliminar" }))) return;
 */

export type OpcionesConfirmar = {
  titulo: string;
  mensaje?: string;
  /** Rótulo del botón que sigue adelante. */
  confirmar: string;
  cancelar: string;
  /** Pinta de rojo el botón de confirmar: borrar, cancelar suscripción, etc. */
  peligro?: boolean;
};

type Pedido = OpcionesConfirmar & { resolver: (ok: boolean) => void };

const Ctx = createContext<((o: OpcionesConfirmar) => Promise<boolean>) | null>(null);

export function useConfirmar() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useConfirmar necesita <ProveedorConfirmacion> más arriba");
  return ctx;
}

export function ProveedorConfirmacion({ children }: { children: ReactNode }) {
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const botonCancelar = useRef<HTMLButtonElement | null>(null);

  const confirmar = useCallback(
    (o: OpcionesConfirmar) =>
      new Promise<boolean>((resolver) => setPedido({ ...o, resolver })),
    [],
  );

  function responder(ok: boolean) {
    pedido?.resolver(ok);
    setPedido(null);
  }

  // Escape cancela. El foco arranca en "Cancelar" y no en el botón de
  // confirmar: si la acción borra algo, no queremos que un Enter de más la
  // dispare sin leer.
  useEffect(() => {
    if (!pedido) return;
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        pedido.resolver(false);
        setPedido(null);
      }
    };
    document.addEventListener("keydown", alTeclear, true);
    botonCancelar.current?.focus();
    return () => document.removeEventListener("keydown", alTeclear, true);
  }, [pedido]);

  return (
    <Ctx.Provider value={confirmar}>
      {children}
      {pedido && (
        <div
          className={css.fondo}
          role="alertdialog"
          aria-modal="true"
          aria-label={pedido.titulo}
          onClick={(e) => {
            if (e.target === e.currentTarget) responder(false);
          }}
        >
          <div className={css.caja}>
            <h3 className={css.titulo}>{pedido.titulo}</h3>
            {pedido.mensaje && <p className={css.mensaje}>{pedido.mensaje}</p>}
            <div className={css.botones}>
              <button type="button" ref={botonCancelar} className={css.btnCancelar} onClick={() => responder(false)}>
                {pedido.cancelar}
              </button>
              <button
                type="button"
                className={`${css.btnOk} ${pedido.peligro ? css.btnPeligro : ""}`}
                onClick={() => responder(true)}
              >
                {pedido.confirmar}
              </button>
            </div>
          </div>
        </div>
      )}
    </Ctx.Provider>
  );
}
