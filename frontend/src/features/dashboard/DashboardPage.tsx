import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useBorrarTx, useCotizaciones, usePresupuestos, useSesion, useTransacciones } from "@/api/queries";
import type { Moneda, Transaccion } from "@/api/types";
import { Sidenav } from "@/components/Sidenav";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { ConsolidadoCard } from "./ConsolidadoCard";
import css from "./Dashboard.module.css";
import { DashboardHeader } from "./DashboardHeader";
import { DiaResultado } from "./DiaResultado";
import { ExportMenu } from "./ExportMenu";
import { Filtros } from "./Filtros";
import { ImportFlow } from "./ImportFlow";
import { LimiteBanner } from "./LimiteBanner";
import { categoriasDisponibles, categoriasPorFrecuencia, filtrarTransacciones, FILTROS_INICIALES } from "./logic";
import { MultiMonedaCard } from "./MultiMonedaCard";
import { PresupuestoModal } from "./PresupuestoModal";
import { PresupuestosCard } from "./PresupuestosCard";
import { trd } from "./messages";
import { ProModal } from "./ProModal";
import { RecurrentesCard } from "./RecurrentesCard";
import { StatsAccordion } from "./StatsAccordion";
import { CotizacionesCard } from "./CotizacionesCard";
import { TransactionList } from "./TransactionList";
import { TransactionModal } from "./TransactionModal";
import { TrialBanner } from "./TrialBanner";
import { WhatsappCard } from "./WhatsappCard";

function fechaHoyTexto(lang: "es" | "en"): string {
  const hoy = new Date();
  const meses = lang === "en"
    ? ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    : ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  return lang === "en"
    ? `${meses[hoy.getMonth()]} ${hoy.getDate()}, ${hoy.getFullYear()}`
    : `${hoy.getDate()} de ${meses[hoy.getMonth()]} de ${hoy.getFullYear()}`;
}

const esEscritorio = () => window.matchMedia("(min-width: 900px)").matches;

export function DashboardPage() {
  const { lang } = usePreferencias();
  const toast = useToast();
  const [params, setParams] = useSearchParams();

  const sesion = useSesion();
  const transacciones = useTransacciones();
  const cotizaciones = useCotizaciones();
  const presupuestos = usePresupuestos();
  const borrarTx = useBorrarTx();

  const [filtros, setFiltros] = useState(FILTROS_INICIALES);
  const [monedaConsol, setMonedaConsol] = useState<Moneda>("ARS");

  const [txModalAbierto, setTxModalAbierto] = useState(false);
  const [editando, setEditando] = useState<Transaccion | null>(null);
  const [presupModalAbierto, setPresupModalAbierto] = useState(false);
  const [proModalAbierto, setProModalAbierto] = useState(false);

  // En escritorio hay lugar de sobra: los acordeones vienen abiertos de
  // entrada en vez de forzar un click extra. En mobile, cerrados.
  const [statsOpen, setStatsOpen] = useState(esEscritorio);
  const [recurOpen, setRecurOpen] = useState(esEscritorio);
  const [waOpen, setWaOpen] = useState(esEscritorio);

  const datos = useMemo(() => transacciones.data ?? [], [transacciones.data]);
  const cotiz = cotizaciones.data ?? { USD: null, EUR: null };
  const categorias = useMemo(() => categoriasDisponibles(datos), [datos]);
  const categoriasFrecuentes = useMemo(() => categoriasPorFrecuencia(datos), [datos]);
  const hoy = new Date();
  const filtrados = useMemo(() => filtrarTransacciones(datos, filtros, hoy), [datos, filtros]);

  const isPro = sesion.data?.is_pro ?? false;

  // El "+" de la barra de iconos en otras páginas (Viajes, Análisis) linkea
  // acá con ?add=1 para abrir el modal de carga sin duplicar su UI.
  useEffect(() => {
    if (params.get("add") === "1") {
      setEditando(null);
      setTxModalAbierto(true);
      setParams({}, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function abrirNuevo() {
    setEditando(null);
    setTxModalAbierto(true);
  }
  function abrirEditar(id: number) {
    const t = datos.find((x) => x.id === id);
    if (!t) return;
    setEditando(t);
    setTxModalAbierto(true);
  }
  async function alBorrarSwipe(id: number): Promise<boolean> {
    try {
      await borrarTx.mutateAsync(id);
      toast(trd("tx_eliminada", lang));
      return true;
    } catch {
      toast(trd("error_guardar", lang));
      return false;
    }
  }

  function cerrarSesion() {
    if (confirm(trd("confirm_cerrar_sesion", lang))) {
      window.location.href = "/montor/logout";
    }
  }

  // El progreso de los presupuestos siempre mide el mes calendario en curso,
  // no el filtro activo de la lista — por eso usa `datos` (todo lo cargado)
  // y no `filtrados`.
  const contarMesActual = () => {
    const inicio = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    return datos.filter((t) => new Date(t.fecha + "T00:00:00") >= inicio).length;
  };

  if (sesion.isPending || transacciones.isPending) {
    return (
      <div className={css.theme}>
        <div className={css.estado}>{lang === "en" ? "Loading…" : "Cargando…"}</div>
      </div>
    );
  }
  if (transacciones.isError || !sesion.data) {
    return (
      <div className={css.theme}>
        <div className={css.estado}>
          {lang === "en" ? "Could not load the data." : "No se pudieron cargar los datos."}
          <button onClick={() => transacciones.refetch()}>{lang === "en" ? "Retry" : "Reintentar"}</button>
        </div>
      </div>
    );
  }

  const { username, whatsapp_habilitado: whatsappHabilitado, is_trial: isTrial, trial_dias: trialDias } = sesion.data;

  return (
    <div className={css.theme}>
      <DashboardHeader
        username={username}
        isPro={isPro}
        fechaHoy={fechaHoyTexto(lang)}
        onAbrirPro={() => setProModalAbierto(true)}
        onCerrarSesion={cerrarSesion}
      />

      {isTrial && <TrialBanner dias={trialDias} onSuscribirme={() => setProModalAbierto(true)} />}

      <div className={css.shell}>
        <Sidenav
          activa="inicio"
          username={username}
          isPro={isPro}
          onNuevaTransaccion={abrirNuevo}
          onUpgrade={() => setProModalAbierto(true)}
          className={css.sidenavArea}
        />

        <div className={css.hero}>
          <ConsolidadoCard filtrados={filtrados} cotiz={cotiz} monedaConsol={monedaConsol} onCambiarMoneda={setMonedaConsol} />
        </div>

        <div className={css.der}>
          {!isPro && <LimiteBanner count={contarMesActual()} onUpgrade={() => setProModalAbierto(true)} />}
          {!isPro && (
            <div className={css.avisoTresMeses}>
              <span>{trd("mostrando_ultimos_3_meses", lang)}</span>
              <button onClick={() => setProModalAbierto(true)}>{trd("ver_todo", lang)}</button>
            </div>
          )}

          <Filtros filtros={filtros} onChange={setFiltros} categorias={categorias} />
          <DiaResultado filtrados={filtrados} filtros={filtros} />

          <div className={css.importExportRow}>
            <ImportFlow isPro={isPro} onNecesitaPro={() => setProModalAbierto(true)} />
            <ExportMenu isPro={isPro} onNecesitaPro={() => setProModalAbierto(true)} />
          </div>

          <TransactionList lista={filtrados} onEditar={abrirEditar} onBorrar={alBorrarSwipe} />
        </div>

        <div className={css.drcha}>
          <PresupuestosCard presupuestos={presupuestos.data ?? []} datos={datos} onAgregar={() => setPresupModalAbierto(true)} />
          {isPro ? (
            <StatsAccordion abierto={statsOpen} onToggle={() => setStatsOpen((v) => !v)} />
          ) : (
            <div className={`${css.cotWrap} ${css.cotWrapStats}`}>
              <div className={css.cotHeader} onClick={() => setProModalAbierto(true)}>
                <span>{trd("resumen_del_mes", lang)}</span>
                <span className={css.chev}>▼</span>
              </div>
            </div>
          )}
          <MultiMonedaCard filtrados={filtrados} />
          <RecurrentesCard abierto={recurOpen} onToggle={() => setRecurOpen((v) => !v)} />
          {whatsappHabilitado && <WhatsappCard abierto={waOpen} onToggle={() => setWaOpen((v) => !v)} />}
          <CotizacionesCard cotiz={cotiz} cargando={cotizaciones.isPending} />
        </div>
      </div>

      <button className={css.fab} onClick={abrirNuevo} aria-label={trd("nueva_transaccion", lang)}>
        +
      </button>

      <TransactionModal
        abierto={txModalAbierto}
        editando={editando}
        isPro={isPro}
        categoriasSugeridas={categoriasFrecuentes}
        onCerrar={() => setTxModalAbierto(false)}
        onNecesitaPro={() => setProModalAbierto(true)}
      />
      <PresupuestoModal
        abierto={presupModalAbierto}
        presupuestos={presupuestos.data ?? []}
        categorias={categoriasFrecuentes}
        onCerrar={() => setPresupModalAbierto(false)}
      />
      <ProModal abierto={proModalAbierto} onCerrar={() => setProModalAbierto(false)} />
    </div>
  );
}
