import { Link } from "react-router-dom";
import { useEffect, useRef } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import css from "./Landing.module.css";

export function Hero() {
  const { lang } = usePreferencias();
  const heroRef = useRef<HTMLElement | null>(null);
  const blob1Ref = useRef<HTMLDivElement | null>(null);
  const blob2Ref = useRef<HTMLDivElement | null>(null);

  // Parallax sutil de los blobs de fondo siguiendo el mouse. Va directo a
  // .style.transform (no a un estado de React): son 60 eventos por segundo
  // mientras el mouse se mueve, y pasar eso por un re-render de React sería
  // trabajo de sobra para algo puramente decorativo.
  useEffect(() => {
    const hero = heroRef.current;
    const blob1 = blob1Ref.current;
    const blob2 = blob2Ref.current;
    if (!hero || !blob1 || !blob2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(pointer: fine)").matches) return;

    const alMover = (e: MouseEvent) => {
      const r = hero.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      blob1.style.transform = `translate(${x * 30}px, ${y * 30}px)`;
      blob2.style.transform = `translate(${x * -24}px, ${y * -24}px)`;
    };
    hero.addEventListener("mousemove", alMover);
    return () => hero.removeEventListener("mousemove", alMover);
  }, []);

  return (
    <section className={css.hero} id="hero" ref={heroRef}>
      <div ref={blob1Ref} className={`${css.heroBlob} ${css.heroBlob1}`} />
      <div ref={blob2Ref} className={`${css.heroBlob} ${css.heroBlob2}`} />
      <div className={css.heroInner}>
        <div className={css.heroCopy}>
          <div className={css.heroEyebrow}>
            <span className={css.num}>$</span>{" "}
            <span>{lang === "en" ? "Personal finance app for Argentina" : "App de finanzas para Argentina"}</span>
          </div>
          <h1 className={css.heroH1}>
            <span className={css.line}>{lang === "en" ? "Control" : "Controlá"}</span>
            <span className={`${css.line} ${css.accent}`}>{lang === "en" ? "your finances" : "tus finanzas"}</span>
            <span className={css.line}>{lang === "en" ? "without the hassle" : "sin complicaciones"}</span>
          </h1>
          <p className={css.heroP}>
            {lang === "en"
              ? "Track income and expenses in ARS, USD, and EUR. The official BNA exchange rate updates itself."
              : "Registrá ingresos y gastos en ARS, USD y EUR. La cotización oficial BNA se actualiza sola."}
          </p>
          <div className={css.heroBtns}>
            <Link to="/montor/login" className={css.btnPrimary}>
              {lang === "en" ? "I want free access →" : "Quiero acceso gratis →"}
            </Link>
            <a href="#demo" className={css.btnSecondary}>
              {lang === "en" ? "See how it works" : "Ver cómo funciona"}
            </a>
          </div>
          <div className={css.trustStrip}>
            <span className={css.item}>
              🔒 <span>{lang === "en" ? "Password-protected access" : "Acceso protegido con contraseña"}</span>
            </span>
            <span className={css.item}>
              🇦🇷 <span>{lang === "en" ? "Official BNA exchange rate" : "Cotización oficial BNA"}</span>
            </span>
            <span className={css.item}>
              ⚡{" "}
              <span>
                {lang === "en"
                  ? "Nothing to install, ready in 2 minutes"
                  : "Sin instalar nada, listo en 2 minutos"}
              </span>
            </span>
          </div>
        </div>
        <a href="#demo" className={css.heroVisual} aria-label="Ver cómo funciona la app">
          <div className={css.phoneFrame}>
            <span className={css.phoneNotch} />
            <img
              src="/static/screenshots/dashboard-mobile.png"
              alt="Dashboard real de Montor, desde el celular"
              loading="eager"
              width={780}
              height={1688}
            />
          </div>
        </a>
      </div>
    </section>
  );
}
