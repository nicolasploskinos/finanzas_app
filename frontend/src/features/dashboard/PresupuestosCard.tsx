import { useEffect, useRef } from "react";

import type { Presupuesto, Transaccion } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon } from "@/lib/formato";
import { normalizar } from "./logic";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

type Props = {
  presupuestos: Presupuesto[];
  /** Todas las transacciones (sin filtrar por período): el progreso del
   *  presupuesto siempre mide el mes calendario en curso, no el filtro
   *  activo en la lista de movimientos. */
  datos: Transaccion[];
  onAgregar: () => void;
};

export function PresupuestosCard({ presupuestos, datos, onAgregar }: Props) {
  const { lang } = usePreferencias();

  const inicio = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
  const gasto = new Map<string, number>();
  for (const t of datos) {
    if (t.tipo !== "Gasto") continue;
    const f = new Date(t.fecha + "T00:00:00");
    if (f < inicio) continue;
    const k = normalizar(t.categoria) + "|" + (t.moneda ?? "ARS");
    gasto.set(k, (gasto.get(k) ?? 0) + parseFloat(String(t.monto)));
  }

  return (
    <div className={css.presupSection}>
      <div className={css.presupHeader}>
        <span className={css.presupTitle}>{trd("presupuestos_del_mes", lang)}</span>
        <button className={css.presupAddBtn} onClick={onAgregar}>
          {trd("agregar", lang)}
        </button>
      </div>

      {!presupuestos.length ? (
        <div className={css.presupEmpty}>{trd("sin_presupuestos", lang)}</div>
      ) : (
        presupuestos.map((p, i) => {
          const moneda = p.moneda ?? "ARS";
          const gastado = gasto.get(normalizar(p.categoria) + "|" + moneda) ?? 0;
          const pct = Math.min((gastado / p.monto) * 100, 100);
          const color = pct >= 100 ? "var(--red)" : pct >= 70 ? "var(--yellow)" : "var(--green)";
          const alerta = pct >= 100 ? "⚠️ " : pct >= 70 ? "⏳ " : "";
          const nombre = moneda === "ARS" ? p.categoria : `${p.categoria} · ${moneda}`;
          return (
            <BarraPresupuesto
              key={p.id}
              nombre={nombre}
              texto={`${alerta}${fmtMon(gastado, moneda)} / ${fmtMon(p.monto, moneda)}`}
              color={color}
              pct={pct}
              delay={i * 60}
            />
          );
        })
      )}
    </div>
  );
}

function BarraPresupuesto({
  nombre,
  texto,
  color,
  pct,
  delay,
}: {
  nombre: string;
  texto: string;
  color: string;
  pct: number;
  delay: number;
}) {
  const ref = useRef<HTMLDivElement | null>(null);

  // La barra arranca en 0% y recién en el próximo frame toma el ancho real,
  // así la transición de .presupBarFill (ya definida en CSS) hace que se
  // "llene" en vez de aparecer directo al porcentaje.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const raf = requestAnimationFrame(() => {
      el.style.width = `${pct}%`;
    });
    return () => cancelAnimationFrame(raf);
  }, [pct]);

  return (
    <div className={`${css.presupBarRow} ${css.staggerIn}`} style={{ animationDelay: `${delay}ms` }}>
      <div className={css.presupBarLabels}>
        <span className={css.presupBarName}>{nombre}</span>
        <span className={css.presupBarAmt} style={{ color }}>
          {texto}
        </span>
      </div>
      <div className={css.presupBarTrack}>
        <div ref={ref} className={css.presupBarFill} style={{ width: 0, background: color }} />
      </div>
    </div>
  );
}
