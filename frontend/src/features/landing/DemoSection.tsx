import { usePreferencias } from "@/hooks/usePreferencias";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

export function DemoSection({ contenedor }: { contenedor: HTMLElement | null }) {
  const { lang } = usePreferencias();

  return (
    <section className={css.demoSection} id="demo">
      <div className={css.sectionLabel}>
        <span className={css.num}>01</span> — <span>{lang === "en" ? "Real screenshots" : "Capturas reales"}</span>
      </div>
      <h2 className={css.h2}>
        {lang === "en" ? "This is the actual app — not a mockup" : "Así es la app de verdad, no un mockup"}
      </h2>
      <p className={css.sectionSub}>
        {lang === "en"
          ? "No stock photos here. This is a live screenshot of Montor running on a computer."
          : "Nada de fotos de stock. Esta es una captura real de Montor andando desde la computadora."}
      </p>

      <Reveal contenedor={contenedor} className={css.demoFrame}>
        <div className={css.demoChrome}>
          <div className={css.demoChromeTitlebar}>
            <div className={css.demoChromeTab}>
              <svg
                className={css.demoChromeTabIcon}
                viewBox="0 0 100 100"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" strokeWidth="7" />
                <rect x="28" y="48" width="9" height="22" rx="3" fill="currentColor" />
                <rect x="45" y="38" width="9" height="32" rx="3" fill="currentColor" />
                <rect x="62" y="28" width="9" height="42" rx="3" fill="currentColor" />
              </svg>
              <span>Montor</span>
              <span className={css.demoChromeTabX}>✕</span>
            </div>
            <div className={css.demoChromeWinctl}>
              <span className={css.demoChromeBtn}>─</span>
              <span className={css.demoChromeBtn}>▢</span>
              <span className={`${css.demoChromeBtn} ${css.demoChromeBtnClose}`}>✕</span>
            </div>
          </div>
          <div className={css.demoChromeAddr}>
            <span className={css.demoChromeNav}>←</span>
            <span className={css.demoChromeNav}>→</span>
            <span className={css.demoChromeNav}>⟳</span>
            <div className={css.demoChromeUrl}>🔒 montor.app</div>
          </div>
        </div>

        <div className={css.demoShot}>
          <img
            src="/static/screenshots/dashboard-desktop.png"
            alt="Dashboard real de Montor con saldo consolidado, presupuestos y movimientos, desde la computadora"
            loading="lazy"
            width={3360}
            height={1802}
          />
        </div>
      </Reveal>
    </section>
  );
}
