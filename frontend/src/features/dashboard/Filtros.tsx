import { useEffect, useState } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import type { Filtros as FiltrosType, Periodo } from "./logic";
import { normalizarRangoDia } from "./logic";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

type Props = {
  filtros: FiltrosType;
  onChange: (f: FiltrosType) => void;
  categorias: string[];
};

const PERIODOS: Array<{ id: Periodo; key: "este_mes" | "tres_meses" | "seis_meses" | "este_anio" | "todo" }> = [
  { id: "1m", key: "este_mes" },
  { id: "3m", key: "tres_meses" },
  { id: "6m", key: "seis_meses" },
  { id: "1a", key: "este_anio" },
  { id: "todo", key: "todo" },
];

export function Filtros({ filtros, onChange, categorias }: Props) {
  const { lang } = usePreferencias();
  const set = (parcial: Partial<FiltrosType>) => onChange({ ...filtros, ...parcial });

  // Los dos inputs de fecha se llevan por separado de `filtros.dia`: ese
  // valor ya viene normalizado (desde <= hasta, y con el vacío completado
  // con el otro extremo para filtrar "un solo día"), pero el input que el
  // usuario no tocó todavía tiene que seguir viéndose vacío en pantalla en
  // vez de mostrar la fecha que se le copió por detrás.
  const [rawDesde, setRawDesde] = useState(filtros.dia?.desde ?? "");
  const [rawHasta, setRawHasta] = useState(filtros.dia?.hasta ?? "");

  useEffect(() => {
    if (!filtros.dia) {
      setRawDesde("");
      setRawHasta("");
    }
  }, [filtros.dia]);

  function alCambiarDesde(v: string) {
    setRawDesde(v);
    set({ dia: normalizarRangoDia(v, rawHasta) });
  }
  function alCambiarHasta(v: string) {
    setRawHasta(v);
    set({ dia: normalizarRangoDia(rawDesde, v) });
  }
  function limpiarDia() {
    setRawDesde("");
    setRawHasta("");
    set({ dia: null });
  }

  return (
    <>
      <div className={css.busquedaWrap}>
        <input
          type="text"
          className={css.busqueda}
          placeholder={trd("buscar", lang)}
          autoComplete="off"
          value={filtros.busqueda}
          onChange={(e) => set({ busqueda: e.target.value })}
        />
        {filtros.busqueda && (
          <button className={`${css.btnClearBusq} ${css.visible}`} onClick={() => set({ busqueda: "" })}>
            ×
          </button>
        )}
      </div>

      <div className={css.periodoPills}>
        {PERIODOS.map((p) => (
          <button
            key={p.id}
            className={`${css.periodoBtn} ${!filtros.dia && filtros.periodo === p.id ? css.active : ""}`}
            onClick={() => {
              setRawDesde("");
              setRawHasta("");
              set({ periodo: p.id, dia: null });
            }}
          >
            {trd(p.key, lang)}
          </button>
        ))}
      </div>

      <div className={css.filtros}>
        <select value={filtros.tipo} onChange={(e) => set({ tipo: e.target.value as FiltrosType["tipo"] })}>
          <option value="">{trd("todo", lang)}</option>
          <option value="Gasto">{trd("gasto", lang)}</option>
          <option value="Ingreso">{trd("ingreso", lang)}</option>
        </select>
        <select value={filtros.moneda} onChange={(e) => set({ moneda: e.target.value as FiltrosType["moneda"] })}>
          <option value="">{trd("todas", lang)}</option>
          <option value="ARS">ARS</option>
          <option value="USD">USD</option>
          <option value="EUR">EUR</option>
        </select>
        <select value={filtros.categoria} onChange={(e) => set({ categoria: e.target.value })}>
          <option value="">{trd("all_categories", lang)}</option>
          {categorias.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className={css.diaRangeWrap}>
        <span className={css.diaLabel} style={{ cursor: "default" }}>
          {trd("ver_dias_puntuales", lang)}
        </span>
        <input
          type="date"
          className={css.diaInput}
          title="Desde qué día"
          value={rawDesde}
          onChange={(e) => alCambiarDesde(e.target.value)}
        />
        <span className={css.diaLabel} style={{ cursor: "default" }}>
          {trd("a", lang)}
        </span>
        <input
          type="date"
          className={css.diaInput}
          title="Hasta qué día (opcional, para ver un rango)"
          value={rawHasta}
          onChange={(e) => alCambiarHasta(e.target.value)}
        />
        {filtros.dia && (
          <button className={css.diaLabel} onClick={limpiarDia}>
            {trd("limpiar", lang)}
          </button>
        )}
      </div>
    </>
  );
}
