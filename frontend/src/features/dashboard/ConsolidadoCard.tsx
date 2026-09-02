import type { Cotizaciones, Moneda, Transaccion } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon } from "@/lib/formato";
import { fromARS, toARS } from "./logic";
import { trd } from "./messages";
import { Sparkline } from "./Sparkline";
import { useAjustarTexto } from "./useAjustarTexto";
import { useMontoAnimado } from "./useMontoAnimado";
import css from "./Dashboard.module.css";

const MONEDAS: Moneda[] = ["ARS", "USD", "EUR"];
const SIMBOLO: Record<Moneda, string> = { ARS: "$ ARS", USD: "USD", EUR: "€ EUR" };

type Props = {
  filtrados: Transaccion[];
  cotiz: Cotizaciones;
  monedaConsol: Moneda;
  onCambiarMoneda: (m: Moneda) => void;
};

export function ConsolidadoCard({ filtrados, cotiz, monedaConsol, onCambiarMoneda }: Props) {
  const { lang } = usePreferencias();
  const sinCotizacion = !cotiz.USD || !cotiz.EUR;

  let ingARS = 0;
  let gasARS = 0;
  for (const t of filtrados) {
    const ars = toARS(t, cotiz);
    if (ars === null) continue;
    if (t.tipo === "Ingreso") ingARS += ars;
    else gasARS += ars;
  }

  const bloqueado = sinCotizacion && monedaConsol !== "ARS";
  const ing = bloqueado ? 0 : (fromARS(ingARS, monedaConsol, cotiz) ?? 0);
  const gas = bloqueado ? 0 : (fromARS(gasARS, monedaConsol, cotiz) ?? 0);
  const net = ing - gas;

  const ingAnimado = useMontoAnimado(ing);
  const gasAnimado = useMontoAnimado(gas);
  const netAnimado = useMontoAnimado(net);

  const ingTxt = bloqueado ? trd("sin_cotizacion", lang) : fmtMon(ingAnimado, monedaConsol);
  const gasTxt = bloqueado ? trd("sin_cotizacion", lang) : fmtMon(gasAnimado, monedaConsol);
  const netTxt = bloqueado
    ? trd("sin_cotizacion", lang)
    : (netAnimado >= 0 ? "+" : "-") + fmtMon(Math.abs(netAnimado), monedaConsol);

  const ingRef = useAjustarTexto<HTMLDivElement>(ingTxt);
  const gasRef = useAjustarTexto<HTMLDivElement>(gasTxt);
  const netRef = useAjustarTexto<HTMLDivElement>(netTxt);

  // Saldo acumulado día a día (en ARS, luego pasado a la moneda elegida) —
  // no es un balance de cuenta real, es la suma corrida de los movimientos
  // filtrados, para mostrar la tendencia.
  const lista = [...filtrados].sort((a, b) => a.fecha.localeCompare(b.fecha));
  const porDia = new Map<string, number>();
  for (const t of lista) {
    const ars = toARS(t, cotiz);
    if (ars === null) continue;
    const delta = t.tipo === "Ingreso" ? ars : -ars;
    porDia.set(t.fecha, (porDia.get(t.fecha) ?? 0) + delta);
  }
  const fechas = [...porDia.keys()].sort();
  let acc = 0;
  const puntos = fechas.map((f) => {
    acc += porDia.get(f)!;
    return fromARS(acc, monedaConsol, cotiz) ?? 0;
  });

  return (
    <div className={css.consSection}>
      <div className={css.consHeader}>
        <span className={css.consTitle}>{trd("total_consolidado_en", lang)}</span>
        <div className={css.consToggle}>
          {MONEDAS.map((m) => (
            <button
              key={m}
              className={`${css.consBtn} ${monedaConsol === m ? css.active : ""}`}
              onClick={() => onCambiarMoneda(m)}
            >
              {SIMBOLO[m]}
            </button>
          ))}
        </div>
      </div>

      {fechas.length > 0 && (
        <div className={css.consSparkWrap}>
          <Sparkline puntos={puntos} />
        </div>
      )}

      <div className={css.consCards}>
        <div className={css.consCard}>
          <div className={css.consCardLabel}>{trd("ingresos", lang)}</div>
          <div ref={ingRef} className={`${css.consCardValue} ${css.green}`}>
            {ingTxt}
          </div>
        </div>
        <div className={css.consCard}>
          <div className={css.consCardLabel}>{trd("gastos", lang)}</div>
          <div ref={gasRef} className={`${css.consCardValue} ${css.red}`}>
            {gasTxt}
          </div>
        </div>
        <div className={`${css.consCard} ${css.consCardFull}`}>
          <div className={css.consCardLabel}>{trd("balance", lang)}</div>
          <div ref={netRef} className={`${css.consCardValue} ${bloqueado ? "" : netAnimado >= 0 ? css.green : css.red}`}>
            {netTxt}
          </div>
        </div>
      </div>
      <div className={css.consNota}>
        {bloqueado
          ? trd("cargando_cotizacion", lang)
          : monedaConsol === "ARS"
            ? trd("suma_directa_ars", lang)
            : trd("tipo_cambio_oficial", lang)}
      </div>
    </div>
  );
}
