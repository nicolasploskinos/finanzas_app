import { useState } from "react";

import type { Cotizaciones, Moneda } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon } from "@/lib/formato";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

const MONEDAS: Moneda[] = ["ARS", "USD", "EUR"];
const LABEL: Record<Moneda, string> = { ARS: "ARS $", USD: "USD", EUR: "EUR €" };

export function CotizacionesCard({ cotiz, cargando }: { cotiz: Cotizaciones; cargando: boolean }) {
  const { lang } = usePreferencias();
  const [abierto, setAbierto] = useState(false);
  const [monto, setMonto] = useState("");
  const [from, setFrom] = useState<Moneda>("ARS");
  const [to, setTo] = useState<Moneda>("USD");

  const rateTxt = cargando
    ? trd("cargando_puntos", lang)
    : `USD ${cotiz.USD ? "$" + cotiz.USD.toLocaleString("es-AR") : "—"} | EUR ${cotiz.EUR ? "$" + cotiz.EUR.toLocaleString("es-AR") : "—"}`;

  const montoNum = parseFloat(monto.replace(",", "."));
  let resultado: string | null = null;
  if (monto && !isNaN(montoNum)) {
    if (!cotiz.USD || !cotiz.EUR) {
      resultado = trd("sin_cotizacion", lang);
    } else {
      const enARS = from === "ARS" ? montoNum : from === "USD" ? montoNum * cotiz.USD : montoNum * cotiz.EUR;
      const salida = to === "ARS" ? enARS : to === "USD" ? enARS / cotiz.USD : enARS / cotiz.EUR;
      resultado = fmtMon(salida, to);
    }
  }

  return (
    <div className={css.cotCard}>
      <div className={css.cotHeader} onClick={() => setAbierto((v) => !v)}>
        <span className={css.cotTitle}>{trd("cotizaciones_oficiales", lang)}</span>
        <span className={css.cotRates}>{rateTxt}</span>
      </div>
      <div className={`${css.cotBody} ${abierto ? css.open : ""}`}>
        <div style={{ height: 12 }} />
        <div className={css.convRow}>
          <input
            type="text"
            placeholder={trd("monto", lang)}
            inputMode="decimal"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
          />
          <select value={from} onChange={(e) => setFrom(e.target.value as Moneda)}>
            {MONEDAS.map((m) => (
              <option key={m} value={m}>
                {LABEL[m]}
              </option>
            ))}
          </select>
          <span className={css.convArrow}>→</span>
          <select value={to} onChange={(e) => setTo(e.target.value as Moneda)}>
            {MONEDAS.map((m) => (
              <option key={m} value={m}>
                {LABEL[m]}
              </option>
            ))}
          </select>
        </div>
        <div className={css.convResult}>{resultado ?? "—"}</div>
        <div className={css.convNota}>{resultado ? trd("tipo_cambio_oficial", lang) : ""}</div>
      </div>
    </div>
  );
}
