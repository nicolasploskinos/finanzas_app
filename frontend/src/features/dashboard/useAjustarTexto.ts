import { useEffect, useRef } from "react";

/**
 * Achica el font-size de a 1px hasta que el texto entre completo en una
 * línea (para los montos grandes del consolidado/stats, que con clamp()
 * ya son responsivos pero un número muy largo — "$1.234.567,89" — igual
 * puede desbordar la tarjeta). Se re-mide en cada render porque el texto
 * cambia constantemente (animación de conteo, cambio de filtro).
 */
export function useAjustarTexto<T extends HTMLElement>(texto: string, min = 6) {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Se espera al próximo repintado para medir sobre el layout ya
    // definitivo (si el valor recién cambió, el navegador todavía no
    // aplicó el nuevo ancho de contenido en este mismo tick).
    const raf = requestAnimationFrame(() => {
      el.style.fontSize = "";
      let size = Math.ceil(parseFloat(getComputedStyle(el).fontSize));
      while (el.scrollWidth > el.clientWidth && size > min) {
        size -= 1;
        el.style.fontSize = size + "px";
      }
    });
    return () => cancelAnimationFrame(raf);
  }, [texto, min]);

  return ref;
}
