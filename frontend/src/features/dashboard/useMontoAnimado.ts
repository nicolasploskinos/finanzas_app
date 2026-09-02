import { useEffect, useRef, useState } from "react";

const prefiereMenosMovimiento = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * A diferencia de useCountUp (que siempre arranca desde 0, pensado para
 * valores que se recrean enteros), esto interpola desde el ÚLTIMO valor
 * mostrado hasta el nuevo — el consolidado del panel cambia de valor todo
 * el tiempo (cambiar de período, de moneda, cargar una transacción) y
 * volver a 0 cada vez sería un parpadeo constante en vez de una animación.
 */
export function useMontoAnimado(valor: number, duracionMs = 550): number {
  const [mostrado, setMostrado] = useState(valor);
  const desdeRef = useRef(valor);

  useEffect(() => {
    if (prefiereMenosMovimiento() || !isFinite(desdeRef.current) || !isFinite(valor)) {
      setMostrado(valor);
      desdeRef.current = valor;
      return;
    }
    const desde = desdeRef.current;
    const inicio = performance.now();
    let raf = 0;
    const paso = (ahora: number) => {
      const p = Math.min((ahora - inicio) / duracionMs, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setMostrado(desde + (valor - desde) * eased);
      if (p < 1) raf = requestAnimationFrame(paso);
      else desdeRef.current = valor;
    };
    raf = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [valor]);

  return mostrado;
}
