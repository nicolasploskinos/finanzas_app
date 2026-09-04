import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import { COMPARACION } from "./content";
import type { Bi } from "./content";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

/** Una celda de plan: tilde, guion, o el valor cuando no es un sí/no. */
function Celda({ valor, lang, pro }: { valor: boolean | Bi; lang: "es" | "en"; pro?: boolean }) {
  if (valor === true) return <span className={pro ? css.pSiPro : css.pSi}>✓</span>;
  if (valor === false) return <span className={css.pNo}>—</span>;
  return <span className={pro ? css.pValorPro : css.pValor}>{valor[lang]}</span>;
}

export function PricingSection({ contenedor }: { contenedor: HTMLElement | null }) {
  const { lang } = usePreferencias();

  return (
    <section className={css.section} id="precio">
      <div className={css.sectionLabel}>
        <span className={css.num}>04</span> — <span>{lang === "en" ? "Pricing" : "Precio"}</span>
      </div>
      <h2 className={css.h2}>
        {lang === "en"
          ? "Free forever. Pro when you outgrow it."
          : "Gratis para siempre. Pro cuando te quede chico."}
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
              <th className={css.thQue}>
                <span className={css.thQueTexto}>
                  {lang === "en" ? "What you get" : "Qué incluye"}
                </span>
              </th>
              <th className={css.thPlan}>
                <div className={css.planNombre}>{lang === "en" ? "FREE" : "GRATIS"}</div>
                <div className={css.planPrecio}>$0</div>
                <div className={css.planNota}>{lang === "en" ? "forever" : "para siempre"}</div>
                <Link to="/montor/login" className={css.planBtn}>
                  {lang === "en" ? "Create account →" : "Crear cuenta →"}
                </Link>
              </th>
              <th className={`${css.thPlan} ${css.thPro}`}>
                {/* La cinta ancla visualmente la columna que queremos que
                    elijan: sin ella las dos pesaban igual y la tabla se leía
                    como información, no como una decisión. */}
                <div className={css.cinta}>{lang === "en" ? "RECOMMENDED" : "RECOMENDADO"}</div>
                <div className={`${css.planNombre} ${css.proNombre}`}>PRO</div>
                <div className={css.planPrecio}>
                  $6.000<span>{lang === "en" ? "/mo" : "/mes"}</span>
                </div>
                <div className={css.planAhorro}>
                  {lang === "en" ? "$60.000/yr · " : "$60.000/año · "}
                  <strong>{lang === "en" ? "save 2 months" : "ahorrás 2 meses"}</strong>
                </div>
                <Link to="/montor/login" className={`${css.planBtn} ${css.planBtnPro}`}>
                  {lang === "en" ? "Get Pro →" : "Elegir Pro →"}
                </Link>
              </th>
            </tr>
          </thead>
          <tbody>
            {COMPARACION.map((fila) => (
              <tr key={fila.que.es} className={css.filaTabla}>
                <td className={css.tdQue}>
                  <span className={css.filaIcono} aria-hidden="true">
                    {fila.icono}
                  </span>
                  {fila.que[lang]}
                </td>
                <td className={css.tdPlan}>
                  <Celda valor={fila.gratis} lang={lang} />
                </td>
                <td className={`${css.tdPlan} ${css.tdPro}`}>
                  <Celda valor={fila.pro} lang={lang} pro />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>

      <p className={css.tablaPie}>
        <span className={css.piePill}>
          {lang === "en"
            ? "✨ Every new account starts with 7 days of Pro"
            : "✨ Toda cuenta nueva arranca con 7 días de Pro"}
        </span>
        <span className={css.pieNota}>
          {lang === "en" ? "Payments with Mercado Pago" : "Pagos con Mercado Pago"}
        </span>
      </p>
    </section>
  );
}
