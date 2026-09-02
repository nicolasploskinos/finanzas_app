import type { Moneda, Transaccion } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon } from "@/lib/formato";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

const ORDEN: Moneda[] = ["ARS", "USD", "EUR"];

/** Saldo real de cada moneda por separado, sin conversión — para ver de un
 *  vistazo cuánto queda "puro" en pesos, dólares y euros (a diferencia del
 *  consolidado, que convierte todo a una sola moneda elegida). */
export function MultiMonedaCard({ filtrados }: { filtrados: Transaccion[] }) {
  const { lang } = usePreferencias();

  const porMoneda = new Map<Moneda, number>();
  for (const t of filtrados) {
    const m = (t.moneda ?? "ARS") as Moneda;
    const signo = t.tipo === "Ingreso" ? 1 : -1;
    porMoneda.set(m, (porMoneda.get(m) ?? 0) + signo * Number(t.monto));
  }
  const monedas = ORDEN.filter((m) => porMoneda.has(m));

  return (
    <div className={css.multimonCard}>
      <div className={css.multimonTitle}>{trd("multi_moneda", lang)}</div>
      {monedas.length ? (
        <div className={css.multimonGrid}>
          {monedas.map((m, i) => {
            const val = porMoneda.get(m)!;
            return (
              <div
                key={m}
                className={`${css.multimonRow} ${css.staggerIn}`}
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <span className={css.multimonMon}>{m}</span>
                <span className={`${css.multimonVal} ${val >= 0 ? css.green : css.red}`}>
                  {val >= 0 ? "+" : "-"}
                  {fmtMon(val, m)}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className={css.presupEmpty}>{trd("sin_movimientos", lang)}</div>
      )}
    </div>
  );
}
