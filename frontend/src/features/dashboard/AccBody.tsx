import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

import css from "./Dashboard.module.css";

const prefiereMenosMovimiento = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Acordeón que anima max-height al alto real del contenido (medido con
 * scrollHeight) en vez de un valor fijo genérico — con un tope grande fijo
 * el contenido corto "salta" casi instantáneo porque la transición es
 * proporcional al valor declarado, no al contenido real. Al terminar de
 * abrir se saca el límite (max-height:none) para que contenido que se
 * carga después (el gráfico de "Resumen del mes", por ejemplo) no quede
 * recortado.
 */
export function AccBody({ open, children }: { open: boolean; children: ReactNode }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let cancelado = false;

    if (prefiereMenosMovimiento()) {
      el.classList.toggle(css.open, open);
      el.style.maxHeight = open ? "none" : "0px";
      return;
    }

    if (open) {
      el.classList.add(css.open);
      el.style.maxHeight = el.scrollHeight + "px";
      const alTerminar = (e: TransitionEvent) => {
        if (e.propertyName !== "max-height") return;
        el.style.maxHeight = "none";
      };
      el.addEventListener("transitionend", alTerminar);
      return () => el.removeEventListener("transitionend", alTerminar);
    }

    el.style.maxHeight = el.scrollHeight + "px";
    // Doble rAF: hay que dejar que el navegador confirme el valor en
    // píxeles recién asignado antes de pasar a 0, porque una transición que
    // arranca desde max-height:none no anima.
    requestAnimationFrame(() => {
      if (cancelado) return;
      requestAnimationFrame(() => {
        if (cancelado) return;
        el.classList.remove(css.open);
        el.style.maxHeight = "0px";
      });
    });
    return () => {
      cancelado = true;
    };
  }, [open]);

  return (
    <div ref={ref} className={css.accBody}>
      {children}
    </div>
  );
}
