import { useMemo, useState } from "react";

import { useSesion, useTransacciones } from "@/api/queries";
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
import { calcularAnalisis, categoriasDisponibles } from "./analytics";
import type { Filtros, Periodo } from "./analytics";

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
  const sesion = useSesion();
  const transacciones = useTransacciones();

  const [filtros, setFiltros] = useState<Filtros>({
    periodo: "1m",
    tipo: "",
    moneda: "",
    categoria: "",
  });

  const datos = useMemo(() => transacciones.data ?? [], [transacciones.data]);
  const categorias = useMemo(() => categoriasDisponibles(datos), [datos]);
  const analisis = useMemo(
    () => calcularAnalisis(datos, filtros, lang),
    [datos, filtros, lang],
  );

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
          <a href="/montor">{t("ver_planes")}</a>
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
              value={filtros.moneda}
              onChange={(e) =>
                setFiltros((f) => ({ ...f, moneda: e.target.value as Filtros["moneda"] }))
              }
            >
              <option value="">{t("todas")}</option>
              <option value="ARS">ARS</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
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
