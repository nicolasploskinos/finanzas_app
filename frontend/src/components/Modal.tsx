import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

import css from "./Modal.module.css";

type Props = {
  abierto: boolean;
  titulo: string;
  onCerrar: () => void;
  children: ReactNode;
  /** Modales con más campos (nueva transacción, presupuestos, importar) usan
   *  una hoja más ancha en escritorio que la genérica de 560px. */
  grande?: boolean;
};

/** Todo lo que puede recibir foco adentro de la hoja, en orden. */
const FOCUSABLES =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({ abierto, titulo, onCerrar, children, grande = false }: Props) {
  const hoja = useRef<HTMLDivElement | null>(null);
  /** Quién tenía el foco antes de abrir, para devolvérselo al cerrar. */
  const disparador = useRef<HTMLElement | null>(null);

  // Escape cierra, y Tab queda encerrado adentro. Sin lo segundo, tabulando
  // se sale a los controles de atrás —que están tapados por el modal— y el
  // foco desaparece de la vista.
  useEffect(() => {
    if (!abierto) return;
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCerrar();
        return;
      }
      if (e.key !== "Tab" || !hoja.current) return;
      const items = [...hoja.current.querySelectorAll<HTMLElement>(FOCUSABLES)].filter(
        (el) => el.offsetParent !== null,
      );
      if (items.length === 0) return;
      const primero = items[0];
      const ultimo = items[items.length - 1];
      // Al llegar a la punta, vuelve al otro extremo en vez de salirse.
      if (e.shiftKey && document.activeElement === primero) {
        e.preventDefault();
        ultimo.focus();
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault();
        primero.focus();
      }
    };
    document.addEventListener("keydown", alTeclear);
    return () => document.removeEventListener("keydown", alTeclear);
  }, [abierto, onCerrar]);

  // El fondo no tiene que scrollear con el modal abierto: en el celular,
  // arrastrar dentro de la hoja arrastraba también la página de atrás, y al
  // cerrar aparecías en otro lugar del que estabas.
  useEffect(() => {
    if (!abierto) return;
    const previo = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previo;
    };
  }, [abierto]);

  // Foco: al abrir va al primer campo (así se puede tipear de una, sin tener
  // que ir al mouse), y al cerrar vuelve al botón que lo abrió.
  useEffect(() => {
    if (!abierto) {
      disparador.current?.focus?.();
      disparador.current = null;
      return;
    }
    disparador.current = document.activeElement as HTMLElement | null;
    // El siguiente cuadro: antes de eso la hoja todavía está en su
    // transición de entrada y el foco no agarra.
    const id = requestAnimationFrame(() => {
      const items = hoja.current?.querySelectorAll<HTMLElement>(FOCUSABLES);
      const campo = [...(items ?? [])].find(
        (el) => el.offsetParent !== null && el.tagName !== "BUTTON",
      );
      // Si no hay campos (un modal solo informativo) no se fuerza nada: mover
      // el foco a un botón invita a apretarlo sin querer.
      campo?.focus();
    });
    return () => cancelAnimationFrame(id);
  }, [abierto]);

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
      aria-label={titulo}
    >
      <div className={`${css.modal} ${grande ? css.grande : ""}`} ref={hoja}>
        <div className={css.handle} />
        <h2 className={css.titulo}>{titulo}</h2>
        {children}
      </div>
    </div>
  );
}
