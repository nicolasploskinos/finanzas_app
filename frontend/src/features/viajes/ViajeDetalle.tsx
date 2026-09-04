import { useMemo, useState } from "react";

import { useBorrarViaje, useQuitarDelViaje, useViaje } from "@/api/queries";
import type { TransaccionViaje } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { fmtMon, formatFecha } from "@/lib/formato";
import { CategoriaDonut } from "./CategoriaDonut";
import css from "./Viajes.module.css";
import { useConfirmar } from "@/components/Confirmacion";

type Props = {
  id: number;
  onVolver: () => void;
  onEditar: () => void;
};

/** Rango de días normalizado (desde <= hasta), o null si no hay filtro. */
function normalizarRango(desde: string, hasta: string): { desde: string; hasta: string } | null {
  if (!desde && !hasta) return null;
  const d = desde || hasta;
  const h = hasta || desde;
  return d > h ? { desde: h, hasta: d } : { desde: d, hasta: h };
}

export function ViajeDetalle({ id, onVolver, onEditar }: Props) {
  const { t, lang } = usePreferencias();
  const confirmar = useConfirmar();
  const toast = useToast();
  const detalle = useViaje(id);
  const borrar = useBorrarViaje();
  const quitar = useQuitarDelViaje(id);

  const [categoria, setCategoria] = useState("");
  const [dias, setDias] = useState({ desde: "", hasta: "" });
  // El gráfico arranca cerrado: en mobile ocupa media pantalla y no siempre
  // es lo que venís a mirar.
  const [chartAbierto, setChartAbierto] = useState(false);

  const transacciones = useMemo(() => detalle.data?.transacciones ?? [], [detalle.data]);

  const categorias = useMemo(() => {
    const vistas = new Set<string>();
    for (const tx of transacciones) if (tx.categoria) vistas.add(tx.categoria);
    return [...vistas].sort((a, b) => a.localeCompare(b));
  }, [transacciones]);

  const rango = normalizarRango(dias.desde, dias.hasta);
  const visibles = transacciones.filter((tx) => {
    if (categoria && tx.categoria !== categoria) return false;
    if (rango && (tx.fecha < rango.desde || tx.fecha > rango.hasta)) return false;
    return true;
  });

  if (detalle.isPending) return <div className={css.estado}>{t("cargando")}</div>;
  if (detalle.isError || !detalle.data)
    return (
      <div className={css.estado}>
        {t("no_pudo_cargar_viaje")}
        <button onClick={onVolver}>{t("volver_a_montor")}</button>
      </div>
    );

  const { viaje, totales, por_categoria } = detalle.data;
  const totalUSD = totales.USD || 0;
  // Los viajes se muestran siempre en dólares: los gastos en otras monedas ya
  // vienen convertidos desde el backend al cambio oficial.
  const catsUSD = por_categoria.USD ?? [];

  async function alBorrar() {
    const ok = await confirmar({
      titulo: t("confirm_borrar_viaje"),
      confirmar: t("eliminar"),
      cancelar: t("cancelar"),
      peligro: true,
    });
    if (!ok) return;
    try {
      await borrar.mutateAsync(id);
      onVolver();
    } catch {
      toast(t("error_guardar_viaje"));
    }
  }

  async function alQuitar(tx: TransaccionViaje) {
    try {
      await quitar.mutateAsync(tx);
      toast(t("quitado_del_viaje"));
    } catch {
      toast(t("error_guardar_viaje"));
    }
  }

  return (
    <div className={css.detalle}>
      <div className={css.detalleLayout}>
        <div className={css.detalleIzq}>
          <div className={css.detalleHeader}>
            <div className={css.detalleNombre}>{viaje.nombre}</div>
            <div className={css.detalleFechas}>
              {formatFecha(viaje.fecha_inicio, lang)} — {formatFecha(viaje.fecha_fin, lang)}
            </div>
            <div className={css.detalleAcciones}>
              <button onClick={onEditar}>{t("editar")}</button>
              <button className={css.borrar} onClick={alBorrar} disabled={borrar.isPending}>
                {t("eliminar")}
              </button>
            </div>
          </div>

          <div className={css.totales}>
            {totalUSD ? (
              <div className={css.totalCard}>
                <div className={css.totalLabel}>{t("total_gastado")}</div>
                <div className={css.totalValue}>{fmtMon(totalUSD, "USD")}</div>
              </div>
            ) : (
              <div className={css.totalVacio}>{t("todavia_no_cargaste")}</div>
            )}
          </div>

          <div className={css.chartWrap}>
            <button className={css.chartTitle} onClick={() => setChartAbierto((v) => !v)}>
              <span>{t("gasto_por_categoria_usd")}</span>
              <span>{chartAbierto ? "▲" : "▼"}</span>
            </button>
            {chartAbierto && (
              <div className={css.chartBody}>
                {catsUSD.length ? (
                  <CategoriaDonut categorias={catsUSD} />
                ) : (
                  <div className={css.chartVacio}>{t("sin_gastos_registrados")}</div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className={css.detalleDer}>
          <div className={css.filtros}>
            <select value={categoria} onChange={(e) => setCategoria(e.target.value)}>
              <option value="">{t("todas_categorias")}</option>
              {categorias.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className={css.filtroDias}>
            <span className={css.filtroDiasLabel}>{t("ver_dias_puntuales")}</span>
            <input
              type="date"
              value={dias.desde}
              onChange={(e) => setDias((d) => ({ ...d, desde: e.target.value }))}
            />
            <span className={css.filtroDiasLabel}>{t("a")}</span>
            <input
              type="date"
              value={dias.hasta}
              onChange={(e) => setDias((d) => ({ ...d, hasta: e.target.value }))}
            />
            {rango && (
              <button onClick={() => setDias({ desde: "", hasta: "" })}>{t("limpiar")}</button>
            )}
          </div>

          {visibles.length ? (
            visibles.map((tx, i) => {
              const clase = tx.tipo === "Ingreso" ? css.ingreso : css.gasto;
              const enUSD = tx.monto_usd ?? tx.monto;
              return (
                <div
                  key={tx.id}
                  className={`${css.txWrap} stagger-in`}
                  style={{ animationDelay: `${Math.min(i, 12) * 30}ms` }}
                >
                  <div className={css.tx}>
                    <div className={`${css.txIcon} ${clase}`}>
                      {tx.tipo === "Ingreso" ? "↑" : "↓"}
                    </div>
                    <div className={css.txInfo}>
                      <div className={css.txCat}>{tx.categoria || t("sin_categoria")}</div>
                      <div className={css.txFecha}>
                        {formatFecha(tx.fecha, lang)}
                        {(tx.moneda ?? "ARS") !== "USD" && ` · ${fmtMon(tx.monto, tx.moneda)}`}
                      </div>
                    </div>
                    <div className={css.txRight}>
                      <div className={`${css.txMonto} ${clase}`}>
                        {tx.tipo === "Ingreso" ? "+" : "-"}
                        {fmtMon(enUSD, "USD")}
                      </div>
                      <button
                        className={css.txQuitar}
                        title={t("quitar_del_viaje")}
                        aria-label={t("quitar_del_viaje")}
                        onClick={() => alQuitar(tx)}
                        disabled={quitar.isPending}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className={css.vacio}>
              {transacciones.length ? t("sin_gastos_filtro") : t("sin_tx_viaje")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
