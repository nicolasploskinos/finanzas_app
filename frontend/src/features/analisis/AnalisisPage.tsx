import { Link } from "react-router-dom";
import { useMemo, useState } from "react";

import { useCategorias, useCotizaciones, useSesion, useTransacciones } from "@/api/queries";
import { AppHeader } from "@/components/AppHeader";
import { Sidenav } from "@/components/Sidenav";
import { useFullBleed } from "@/hooks/useFullBleed";
import { usePreferencias } from "@/hooks/usePreferencias";
import type { MsgKey } from "@/i18n/messages";
import nebula from "@/styles/nebula.module.css";
import css from "./Analisis.module.css";
import { CategoryRank } from "./CategoryRank";
import { MonthlyChart, TrendChart } from "./Charts";
import { KpiGrid } from "./KpiGrid";
import { calcularAnalisis, FILTROS_INICIALES, MONEDAS, rangoPeriodo } from "./analytics";
import { aISO } from "@/lib/formato";
import type { Filtros, Periodo } from "./analytics";
import type { Moneda } from "@/api/types";

const PILLS: Array<{ id: Periodo; label: MsgKey }> = [
  { id: "1m", label: "este_mes" },
  { id: "mes_pasado", label: "mes_pasado" },
  { id: "3m", label: "tres_meses" },
  { id: "6m", label: "seis_meses" },
  { id: "1a", label: "este_anio" },
  { id: "todo", label: "todo" },
];

export function AnalisisPage() {
  useFullBleed(nebula.fullBleed);
  const { t, lang } = usePreferencias();
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES);

  // Al servidor sólo se le pide el período elegido, no todo el historial.
  const rango = useMemo(() => {
    const { desde, hasta } = rangoPeriodo(filtros.periodo, new Date());
    return { desde: desde ? aISO(desde) : null, hasta: hasta ? aISO(hasta) : null };
  }, [filtros.periodo]);

  const sesion = useSesion();
  const transacciones = useTransacciones(rango);
  // Respaldo para las filas viejas que no guardaron la cotización del día.
  const cotizaciones = useCotizaciones();
  const categoriasQuery = useCategorias();

  /** Prende/apaga una moneda en el lado que corresponda (ingresos o gastos). */
  function toggleMoneda(lado: "monedasIng" | "monedasGas", m: Moneda) {
    setFiltros((f) => {
      const actuales = f[lado];
      const nuevas = actuales.includes(m)
        ? actuales.filter((x) => x !== m)
        : [...MONEDAS].filter((x) => actuales.includes(x) || x === m); // mantiene el orden ARS/USD/EUR
      return { ...f, [lado]: nuevas };
    });
  }

  const datos = useMemo(() => transacciones.data ?? [], [transacciones.data]);
  const cotiz = cotizaciones.data ?? { USD: null, EUR: null };
  // Del historial completo, no del rango visible (ver useCategorias).
  const categorias = useMemo(
    () => (categoriasQuery.data ?? []).map((c) => c.nombre).sort((a, b) => a.localeCompare(b)),
    [categoriasQuery.data],
  );
  const analisis = useMemo(
    () => calcularAnalisis(datos, filtros, lang, cotiz),
    [datos, filtros, lang, cotiz.USD, cotiz.EUR],
  );

  // Si el filtro de tipo ya deja un solo lado, el selector de monedas del
  // otro lado no tendría efecto: se esconde en vez de quedar muerto.
  const ingVisible = filtros.tipo !== "Gasto";
  const gasVisible = filtros.tipo !== "Ingreso";
  const sinMonedas =
    (!ingVisible || filtros.monedasIng.length === 0) &&
    (!gasVisible || filtros.monedasGas.length === 0);

  const header = <AppHeader icono="📈" titulo={t("analisis")} />;

  if (sesion.isPending || transacciones.isPending) {
    return (
      <div className={nebula.theme} data-tema="nebula">
        {header}
        <div className={css.estado}>{t("cargando")}</div>
      </div>
    );
  }

  if (transacciones.isError) {
    return (
      <div className={nebula.theme} data-tema="nebula">
        {header}
        <div className={css.estado}>
          {t("error_carga")}
          <button onClick={() => transacciones.refetch()}>{t("reintentar")}</button>
        </div>
      </div>
    );
  }

  const { username = "", is_pro: isPro = false } = sesion.data ?? {};

  if (!isPro) {
    return (
      <div className={nebula.theme} data-tema="nebula">
        {header}
        <div className={css.locked}>
          <h2>🔒 {t("solo_pro")}</h2>
          <p>{t("solo_pro_detalle")}</p>
          <Link to="/montor">{t("ver_planes")}</Link>
        </div>
      </div>
    );
  }

  return (
    <div className={nebula.theme} data-tema="nebula">
      {header}
      <div className={css.shell}>
        <Sidenav activa="analisis" username={username} isPro={isPro} />

        <div className={css.content}>
          <div className={css.pills}>
            {PILLS.map((p) => (
              <button
                key={p.id}
                className={`${css.pill} ${filtros.periodo === p.id ? css.active : ""}`}
                onClick={() => setFiltros((f) => ({ ...f, periodo: p.id }))}
              >
                {t(p.label)}
              </button>
            ))}
          </div>

          <div className={css.filtros}>
            <select
              value={filtros.tipo}
              onChange={(e) =>
                setFiltros((f) => ({ ...f, tipo: e.target.value as Filtros["tipo"] }))
              }
            >
              <option value="">{t("todo")}</option>
              <option value="Gasto">{t("gasto")}</option>
              <option value="Ingreso">{t("ingreso")}</option>
            </select>

            <select
              value={filtros.categoria}
              onChange={(e) => setFiltros((f) => ({ ...f, categoria: e.target.value }))}
            >
              <option value="">{t("todas_categorias")}</option>
              {categorias.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Monedas por lado: se puede mirar, por ejemplo, ingresos sólo en
              dólares contra gastos en las tres. */}
          <div className={css.monedasFiltro}>
            {ingVisible && (
              <div className={css.monedaGrupo}>
                <span className={css.monedaGrupoLabel}>{t("ingresos")}</span>
                {MONEDAS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    aria-pressed={filtros.monedasIng.includes(m)}
                    className={`${css.monedaChip} ${filtros.monedasIng.includes(m) ? css.chipIng : ""}`}
                    onClick={() => toggleMoneda("monedasIng", m)}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}

            {gasVisible && (
              <div className={css.monedaGrupo}>
                <span className={css.monedaGrupoLabel}>{t("gastos")}</span>
                {MONEDAS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    aria-pressed={filtros.monedasGas.includes(m)}
                    className={`${css.monedaChip} ${filtros.monedasGas.includes(m) ? css.chipGas : ""}`}
                    onClick={() => toggleMoneda("monedasGas", m)}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>

          <p className={`${css.notaConversion} ${sinMonedas ? css.notaAviso : ""}`}>
            {sinMonedas ? `⚠️ ${t("sin_monedas")}` : `💱 ${t("nota_conversion")}`}
          </p>

          <KpiGrid analisis={analisis} />

          <div className={css.anGrid}>
            <div className={css.card}>
              <div className={css.cardTitle}>{t("ing_vs_gas")}</div>
              {analisis.hayDatosMensuales ? (
                <MonthlyChart meses={analisis.meses} />
              ) : (
                <div className={css.empty}>{t("sin_datos")}</div>
              )}
            </div>

            <div className={css.card}>
              <div className={css.cardTitle}>{t("cat_principales")}</div>
              <CategoryRank categorias={analisis.categorias} />
            </div>

            <div className={`${css.card} ${css.full}`}>
              <div className={css.cardTitle}>{t("tendencia_saldo")}</div>
              {analisis.hayDatosMensuales ? (
                <TrendChart meses={analisis.meses} />
              ) : (
                <div className={css.empty}>{t("sin_datos")}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
