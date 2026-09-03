import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import { CountUpOnView } from "./CountUpOnView";
import { PRECIO_FREE_FEATURES, PRECIO_PRO_FEATURES } from "./content";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

export function PricingSection({ contenedor }: { contenedor: HTMLElement | null }) {
  const { lang } = usePreferencias();

  return (
    <section className={css.section} id="precio">
      <div className={css.sectionLabel}>
        <span className={css.num}>04</span> — <span>{lang === "en" ? "Pricing" : "Precio"}</span>
      </div>
      <h2 className={css.h2}>{lang === "en" ? "Start free, no card required" : "Empezá gratis, sin tarjeta"}</h2>
      <p className={css.sectionSub}>
        {lang === "en"
          ? "The app is free forever. Pro unlocks advanced features if you need them."
          : "La app es gratuita para siempre. Pro desbloquea funciones avanzadas si las necesitás."}
      </p>

      <div className={css.preciosGrid}>
        <Reveal contenedor={contenedor} index={0} className={css.precioCard}>
          <div className={css.precioBadge}>{lang === "en" ? "FREE" : "GRATIS"}</div>
          <div className={css.precioNum}>$0</div>
          <p className={css.precioSub}>
            {lang === "en" ? "Forever · " : "Para siempre · "}
            <strong>{lang === "en" ? "7-day Pro trial included" : "7 días Pro incluidos"}</strong>
          </p>
          <ul className={css.precioFeatures}>
            {PRECIO_FREE_FEATURES.map((f) => (
              <li key={f.texto.es} className={f.incluido ? "" : css.no}>
                {f.texto[lang]}
              </li>
            ))}
          </ul>
          <Link to="/montor/login" className={css.btnPrimary} style={{ display: "block", textAlign: "center" }}>
            {lang === "en" ? "Try 7 days free →" : "Probá 7 días gratis →"}
          </Link>
        </Reveal>

        <Reveal contenedor={contenedor} index={1} className={`${css.precioCard} ${css.pro}`}>
          <div className={`${css.precioBadge} ${css.pro}`}>⭐ PRO</div>
          <div className={css.precioCiclos}>
            <div className={css.precioCicloBox}>
              <div className={css.precioCicloLabel}>{lang === "en" ? "Monthly" : "Mensual"}</div>
              <div className={css.precioCicloMonto}>
                <CountUpOnView valor={6000} contenedor={contenedor} />
                <span>{lang === "en" ? "/mo" : "/mes"}</span>
              </div>
            </div>
            <div className={`${css.precioCicloBox} ${css.destacado}`}>
              <div className={css.precioCicloBadge}>{lang === "en" ? "2 months free" : "2 meses gratis"}</div>
              <div className={css.precioCicloLabel}>{lang === "en" ? "Yearly" : "Anual"}</div>
              <div className={css.precioCicloMonto}>
                <CountUpOnView valor={60000} contenedor={contenedor} />
                <span>{lang === "en" ? "/yr" : "/año"}</span>
              </div>
            </div>
          </div>
          <p className={css.precioSub}>
            {lang === "en"
              ? "Secure payments with Mercado Pago — choose your billing cycle after signing up"
              : "Pagos seguros con Mercado Pago — elegís el ciclo de pago al registrarte"}
          </p>
          <ul className={css.precioFeatures}>
            {PRECIO_PRO_FEATURES.map((f) => (
              <li key={f.texto.es}>{f.texto[lang]}</li>
            ))}
          </ul>
          <Link
            to="/montor/login"
            className={css.btnPrimary}
            style={{ display: "block", textAlign: "center", background: "#d97706" }}
          >
            {lang === "en" ? "Start with Pro →" : "Empezar con Pro →"}
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
