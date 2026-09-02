import { useMemo, useState } from "react";

import { useInflacion, useResumenIA, useStats } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import { AccBody } from "./AccBody";
import { CategoriaChart } from "./CategoriaChart";
import { MESES_ES, MESES_EN, mesTraducido } from "./meses";
import { trd } from "./messages";
import type { DashMsgKey } from "./messages";
import css from "./Dashboard.module.css";

type Props = {
  abierto: boolean;
  onToggle: () => void;
};

const MSG_KEYS_IA = { ia_no_disponible: 1, sin_datos: 1, ia_no_configurada: 1 } as const;

function Diff({ actual, anterior, buenoCuandoBaja, mesAnteriorLabel }: { actual: number; anterior: number; buenoCuandoBaja: boolean; mesAnteriorLabel: string }) {
  if (!anterior) return null;
  const pct = Math.round(((actual - anterior) / anterior) * 100);
  const sube = actual > anterior;
  const bueno = buenoCuandoBaja ? !sube : sube;
  return (
    <div className={css.statsDiff} style={{ color: bueno ? "var(--green)" : "var(--red)" }}>
      {sube ? "▲" : "▼"} {Math.abs(pct)}% vs {mesAnteriorLabel}
    </div>
  );
}

export function StatsAccordion({ abierto, onToggle }: Props) {
  const { lang } = usePreferencias();
  const hoy = new Date();
  const [mes, setMes] = useState(hoy.getMonth() + 1);
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [iaTexto, setIaTexto] = useState<string | null>(null);

  const stats = useStats(mes, anio, abierto);
  const inflacion = useInflacion(abierto);
  const resumenIA = useResumenIA();

  // El banner de límite de transacciones (plan free) nunca depende de esto:
  // toggleStats() ni siquiera deja abrir este acordeón sin ser Pro, y el
  // banner solo se muestra a usuarios free — el conteo para el banner sale
  // directo de la lista de transacciones ya cargada (ver DashboardPage).

  const anios: number[] = [];
  for (let y = hoy.getFullYear(); y >= Math.max(2020, hoy.getFullYear() - 4); y--) anios.push(y);
  const meses = lang === "en" ? MESES_EN : MESES_ES;

  const r = stats.data?.resumen;
  const cats = stats.data?.categorias ?? [];

  const inflStrip = useMemo(() => {
    if (!r || !inflacion.data) return null;
    const pad = (n: number) => String(n).padStart(2, "0");
    const mesStr = `${anio}-${pad(mes)}`;
    const mesPrevStr = mes > 1 ? `${anio}-${pad(mes - 1)}` : `${anio - 1}-12`;
    const ipcAct = inflacion.data.find((x) => x.mes === mesStr)?.ipc;
    const ipcAnt = inflacion.data.find((x) => x.mes === mesPrevStr)?.ipc;
    if (!ipcAct || !ipcAnt) return null;
    const inflPct = (ipcAct / ipcAnt - 1) * 100;
    let real = null as null | { pct: number; color: string };
    if (r.gastos_anterior > 0) {
      const nomPct = ((r.gastos_actual - r.gastos_anterior) / r.gastos_anterior) * 100;
      const realPct = ((1 + nomPct / 100) / (1 + inflPct / 100) - 1) * 100;
      real = { pct: realPct, color: realPct > 0 ? "var(--red)" : "var(--green)" };
    }
    return { inflPct, real, mesLabel: mesTraducido(r.mes_actual, lang) };
  }, [r, inflacion.data, anio, mes, lang]);

  function esCodigoConocido(codigo: string): codigo is DashMsgKey {
    return codigo in MSG_KEYS_IA;
  }

  async function generarResumen() {
    setIaTexto(trd("ia_generando", lang));
    try {
      const d = await resumenIA.mutateAsync({ mes, anio, lang });
      if (d.ok && d.resumen) { setIaTexto(d.resumen); return; }
      const codigo = d.error ?? "ia_no_disponible";
      setIaTexto(esCodigoConocido(codigo) ? trd(codigo, lang) : codigo);
    } catch {
      setIaTexto(trd("ia_no_disponible", lang));
    }
  }

  return (
    <div className={`${css.cotWrap} ${css.cotWrapStats}`}>
      <div className={css.cotHeader} onClick={onToggle}>
        <span>{trd("resumen_del_mes", lang)}</span>
        <span className={css.chev}>{abierto ? "▲" : "▼"}</span>
      </div>
      <AccBody open={abierto}>
        <div className={css.statsSelects}>
          <select value={mes} onChange={(e) => setMes(Number(e.target.value))}>
            {meses.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
          <select value={anio} onChange={(e) => setAnio(Number(e.target.value))}>
            {anios.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>

        {r && (
          <div className={css.statsGrid}>
            <div className={css.statsCard}>
              <div className={css.statsCardLabel}>
                {trd("lbl_gastos", lang)} {mesTraducido(r.mes_actual, lang)}
              </div>
              <div className={`${css.statsCardValue} ${css.red}`}>${Math.round(r.gastos_actual).toLocaleString("es-AR")}</div>
              <Diff actual={r.gastos_actual} anterior={r.gastos_anterior} buenoCuandoBaja mesAnteriorLabel={mesTraducido(r.mes_anterior, lang)} />
            </div>
            <div className={css.statsCard}>
              <div className={css.statsCardLabel}>
                {trd("lbl_ingresos", lang)} {mesTraducido(r.mes_actual, lang)}
              </div>
              <div className={`${css.statsCardValue} ${css.green}`}>${Math.round(r.ingresos_actual).toLocaleString("es-AR")}</div>
              <Diff actual={r.ingresos_actual} anterior={r.ingresos_anterior} buenoCuandoBaja={false} mesAnteriorLabel={mesTraducido(r.mes_anterior, lang)} />
            </div>
          </div>
        )}

        {inflStrip && (
          <div className={css.inflStrip}>
            📊 {trd("inflacion_indec", lang)} {inflStrip.mesLabel}:{" "}
            <strong style={{ color: "var(--yellow)" }}>+{inflStrip.inflPct.toFixed(1)}%</strong>
            {inflStrip.real && (
              <>
                {" "}
                &nbsp;·&nbsp; {trd("gastos_reales", lang)}:{" "}
                <strong style={{ color: inflStrip.real.color }}>
                  {inflStrip.real.pct > 0 ? "▲" : "▼"} {Math.abs(inflStrip.real.pct).toFixed(1)}%
                </strong>
              </>
            )}
          </div>
        )}

        <div className={css.catLabel}>{trd("gastos_por_categoria_ars", lang)}</div>
        {cats.length ? <CategoriaChart categorias={cats} /> : <div className={css.catVacio}>{trd("sin_gastos_este_mes", lang)}</div>}

        <div className={css.iaWrap}>
          <button className={css.iaBtn} onClick={generarResumen} disabled={resumenIA.isPending}>
            {trd("generar_resumen_ia", lang)}
          </button>
          {iaTexto && <div className={css.iaBox}>{iaTexto}</div>}
        </div>
      </AccBody>
    </div>
  );
}
