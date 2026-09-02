import { useEffect, useRef, useState } from "react";

const prefiereMenosMovimiento = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Aparición sutil al hacer scroll: `revelado` pasa a true la primera vez que
 * el elemento entra en viewport (nunca vuelve a false). Se guarda en un
 * useState -y no se toca el DOM a mano vía classList- justamente para que
 * sobreviva re-renders del componente (p.ej. al cambiar de idioma, que
 * re-renderiza todo el árbol): si el estado revelado viviera solo en el
 * classList impuesto imperativamente, el próximo render de React lo
 * pisaría con el className "reveal" original (sin "in"), dejando el
 * elemento congelado en la posición de "todavía no revelado" para siempre,
 * porque el observer ya hizo unobserve.
 *
 * `contenedor` es la raíz que scrollea (el div fixed de la página) - no
 * `document`, porque acá el layout usa position:fixed + overflow-y:auto en
 * vez de que la ventana misma scrollee.
 */
export function useReveal<T extends HTMLElement>(contenedor: HTMLElement | null) {
  const ref = useRef<T | null>(null);
  const [revelado, setRevelado] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || revelado) return;
    if (prefiereMenosMovimiento()) {
      setRevelado(true);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setRevelado(true);
            io.unobserve(el);
          }
        }
      },
      { root: contenedor, threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [contenedor, revelado]);

  return { ref, revelado };
}
