import { useEffect, useRef, useState } from "react";

type Props = {
  valor: number;
  contenedor: HTMLElement | null;
};

const prefiereMenosMovimiento = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** "$6.000" — el precio cuenta de 0 al valor real la primera vez que entra
 *  en pantalla, con el mismo ease-out cúbico que el resto de la app. */
export function CountUpOnView({ valor, contenedor }: Props) {
  const ref = useRef<HTMLSpanElement | null>(null);
  const [mostrado, setMostrado] = useState(prefiereMenosMovimiento() ? valor : 0);

  useEffect(() => {
    const el = ref.current;
    if (!el || prefiereMenosMovimiento()) return;

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          io.unobserve(el);
          const inicio = performance.now();
          const dur = 1100;
          const paso = (ahora: number) => {
            const p = Math.min((ahora - inicio) / dur, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            setMostrado(Math.round(valor * eased));
            if (p < 1) requestAnimationFrame(paso);
          };
          requestAnimationFrame(paso);
        }
      },
      { root: contenedor, threshold: 0.5 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [valor, contenedor]);

  return <span ref={ref}>${mostrado.toLocaleString("es-AR")}</span>;
}
