import { useEffect, useState } from "react";

const prefiereMenosMovimiento = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Cuenta desde 0 hasta `valor` con ease-out cúbico, igual que los KPI de la
 * versión anterior: cada vez que cambia el período o un filtro las cifras se
 * recalculan enteras, así que siempre se arranca de 0 y no del valor previo.
 */
export function useCountUp(valor: number, duracionMs = 700): number {
  const [actual, setActual] = useState(valor);

  useEffect(() => {
    if (prefiereMenosMovimiento()) {
      setActual(valor);
      return;
    }

    let raf = 0;
    const inicio = performance.now();

    const paso = (ahora: number) => {
      const p = Math.min((ahora - inicio) / duracionMs, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setActual(valor * eased);
      if (p < 1) raf = requestAnimationFrame(paso);
      else setActual(valor);
    };

    raf = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(raf);
  }, [valor, duracionMs]);

  return actual;
}
