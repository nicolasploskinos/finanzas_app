import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import { COMPARACION } from "./content";
import type { Bi } from "./content";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

/** Una celda de plan: tilde, guion, o el valor cuando no es un sí/no. */
function Celda({ valor, lang }: { valor: boolean | Bi; lang: "es" | "en" }) {
  if (valor === true) return <span className={css.pSi}>✓</span>;
  if (valor === false) return <span className={css.pNo}>—</span>;
  return <span className={css.pValor}>{valor[lang]}</span>;
}

export function PricingSection({ contenedor }: { contenedor: HTMLElement | null }) {
  const { lang } = usePreferencias();

  return (
    <section className={css.section} id="precio">
      <div className={css.sectionLabel}>
        <span className={css.num}>04</span> — <span>{lang === "en" ? "Pricing" : "Precio"}</span>
      </div>
      <h2 className={css.h2}>
        {lang === "en" ? "Two plans, one table" : "Dos planes, una sola tabla"}
      </h2>
      <p className={css.sectionSub}>
        {lang === "en"
          ? "No card to get started. Cancel whenever you want."
          : "Sin tarjeta para empezar. Cancelás cuando quieras."}
      </p>

      <Reveal contenedor={contenedor} index={0} className={css.tablaWrap}>
        <table className={css.tabla}>
          <thead>
            <tr>
              {/* Columna de nombres: sin encabezado propio, el título de cada
                  plan ya dice de qué se trata la fila. */}
              <th className={css.thQue} />
              <th className={css.thPlan}>
                <div className={css.planNombre}>{lang === "en" ? "FREE" : "GRATIS"}</div>
                <div className={css.planPrecio}>$0</div>
                <div className={css.planNota}>{lang === "en" ? "forever" : "para siempre"}</div>
                <Link to="/montor/login" className={css.planBtn}>
                  {lang === "en" ? "Create account →" : "Crear cuenta →"}
                </Link>
              </th>
              <th className={`${css.thPlan} ${css.thPro}`}>
                <div className={`${css.planNombre} ${css.proNombre}`}>⭐ PRO</div>
                <div className={css.planPrecio}>
                  $6.000<span>{lang === "en" ? "/mo" : "/mes"}</span>
                </div>
                <div className={css.planNota}>
                  {lang === "en" ? "or $60.000/yr — " : "o $60.000/año — "}
                  <strong>{lang === "en" ? "2 months free" : "2 meses gratis"}</strong>
                </div>
                <Link to="/montor/login" className={`${css.planBtn} ${css.planBtnPro}`}>
                  {lang === "en" ? "Get Pro →" : "Elegir Pro →"}
                </Link>
              </th>
            </tr>
          </thead>
          <tbody>
            {COMPARACION.map((fila) => (
              <tr key={fila.que.es}>
                <td className={css.tdQue}>{fila.que[lang]}</td>
                <td className={css.tdPlan}>
                  <Celda valor={fila.gratis} lang={lang} />
                </td>
                <td className={`${css.tdPlan} ${css.tdPro}`}>
                  <Celda valor={fila.pro} lang={lang} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>

      <p className={css.tablaPie}>
        {lang === "en"
          ? "Every new account gets 7 days of Pro to try it out. Payments with Mercado Pago."
          : "Toda cuenta nueva arranca con 7 días de Pro para probarlo. Pagos con Mercado Pago."}
      </p>
    </section>
  );
}
