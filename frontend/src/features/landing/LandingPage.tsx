import { useCallback, useEffect, useRef, useState } from "react";

import { CtaFinal } from "./CtaFinal";
import { DemoSection } from "./DemoSection";
import { FaqSection } from "./FaqSection";
import { FeaturesSection } from "./FeaturesSection";
import { Footer } from "./Footer";
import { Hero } from "./Hero";
import css from "./Landing.module.css";
import { Marquee } from "./Marquee";
import { Nav } from "./Nav";
import { ParaQuienSection } from "./ParaQuienSection";
import { PricingSection } from "./PricingSection";

export function LandingPage() {
  const progressRef = useRef<HTMLDivElement | null>(null);
  // El div de la página es el que realmente scrollea (position:fixed +
  // overflow-y:auto), no la ventana — así que la barra de progreso y el
  // root de cada IntersectionObserver (ver Reveal/CountUpOnView) tienen que
  // apuntar acá. Se guarda en estado (no un ref suelto) para que los hijos
  // se vuelvan a renderizar una vez que el nodo existe de verdad.
  const [contenedor, setContenedor] = useState<HTMLDivElement | null>(null);
  const pageRef = useCallback((node: HTMLDivElement | null) => setContenedor(node), []);

  useEffect(() => {
    const el = contenedor;
    const bar = progressRef.current;
    if (!el || !bar) return;
    const actualizar = () => {
      const max = el.scrollHeight - el.clientHeight;
      bar.style.width = (max > 0 ? (el.scrollTop / max) * 100 : 0) + "%";
    };
    el.addEventListener("scroll", actualizar, { passive: true });
    actualizar();
    return () => el.removeEventListener("scroll", actualizar);
  }, [contenedor]);

  return (
    <div className={css.page} ref={pageRef}>
      <div ref={progressRef} className={css.scrollProgress} />

      <Nav />
      <Hero />
      <Marquee />
      <DemoSection contenedor={contenedor} />

      <div className={css.divider} />
      <FeaturesSection contenedor={contenedor} />

      <ParaQuienSection />

      <div className={css.divider} />
      <PricingSection contenedor={contenedor} />

      <div className={css.divider} />
      <FaqSection contenedor={contenedor} />

      <CtaFinal />
      <Footer />
    </div>
  );
}
