import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useBorrarTx, useCategorias, useCotizaciones, usePresupuestos, useSesion, useTransacciones } from "@/api/queries";
import type { Moneda, Transaccion } from "@/api/types";
import { Sidenav } from "@/components/Sidenav";
import { useFullBleed } from "@/hooks/useFullBleed";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import nebula from "@/styles/nebula.module.css";
import { ConsolidadoCard } from "./ConsolidadoCard";
import css from "./Dashboard.module.css";
import { DashboardHeader } from "./DashboardHeader";
import { DiaResultado } from "./DiaResultado";
import { EjemplosBanner } from "./EjemplosBanner";
import { ExportMenu } from "./ExportMenu";
import { Filtros } from "./Filtros";
import { ImportFlow } from "./ImportFlow";
import { LimiteBanner } from "./LimiteBanner";
import { filtrarTransacciones, FILTROS_INICIALES, rangoParaFetch } from "./logic";
import { PresupuestoModal } from "./PresupuestoModal";
import { PresupuestosCard } from "./PresupuestosCard";
import { trd } from "./messages";
import { ProfileModal } from "./ProfileModal";
import { ProModal } from "./ProModal";
import { RecurrentesCard } from "./RecurrentesCard";
import { StatsAccordion } from "./StatsAccordion";
import { CotizacionesCard } from "./CotizacionesCard";
import { TransactionList } from "./TransactionList";
import { TransactionModal } from "./TransactionModal";
import { TrialBanner } from "./TrialBanner";
import { WhatsappCard } from "./WhatsappCard";
import { useConfirmar } from "@/components/Confirmacion";

function fechaHoyTexto(lang: "es" | "en"): string {
  const hoy = new Date();
  const meses = lang === "en"
    ? ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    : ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  return lang === "en"
    ? `${meses[hoy.getMonth()]} ${hoy.getDate()}, ${hoy.getFullYear()}`
    : `${hoy.getDate()} de ${meses[hoy.getMonth()]} de ${hoy.getFullYear()}`;
}

export function DashboardPage() {
  useFullBleed(nebula.fullBleed);

  const { lang } = usePreferencias();
  const toast = useToast();
  const confirmar = useConfirmar();
  const [params, setParams] = useSearchParams();

  const [filtros, setFiltros] = useState(FILTROS_INICIALES);

  const hoy = new Date();
  // Al servidor sólo se le pide el rango que se está mirando; el resto de
  // los filtros (texto, tipo, categoría) se siguen aplicando acá.
  const rango = useMemo(() => rangoParaFetch(filtros, hoy), [filtros.periodo, filtros.dia]);

  const sesion = useSesion();
  const transacciones = useTransacciones(rango);
  const cotizaciones = useCotizaciones();
  const categoriasQuery = useCategorias();
  const presupuestos = usePresupuestos();
  const borrarTx = useBorrarTx();
  const [monedaConsol, setMonedaConsol] = useState<Moneda>("ARS");

  const [txModalAbierto, setTxModalAbierto] = useState(false);
  const [editando, setEditando] = useState<Transaccion | null>(null);
  const [presupModalAbierto, setPresupModalAbierto] = useState(false);
  const [proModalAbierto, setProModalAbierto] = useState(false);
  const [perfilModalAbierto, setPerfilModalAbierto] = useState(false);

  // Los acordeones de la derecha (Resumen del mes, Recurrentes, WhatsApp)
  // arrancan siempre cerrados, en cualquier tamaño de pantalla — el usuario
  // los abre cuando los quiere ver.
  const [statsOpen, setStatsOpen] = useState(false);
  const [recurOpen, setRecurOpen] = useState(false);
  const [waOpen, setWaOpen] = useState(false);

  const datos = useMemo(() => transacciones.data ?? [], [transacciones.data]);
  const cotiz = cotizaciones.data ?? { USD: null, EUR: null };
  // Las categorías vienen del historial completo, no del rango visible: si
  // no, el autocompletado se achicaría al cambiar de período.
  const catCompletas = useMemo(() => categoriasQuery.data ?? [], [categoriasQuery.data]);
  const categorias = useMemo(
    () => [...catCompletas].map((c) => c.nombre).sort((a, b) => a.localeCompare(b)),
    [catCompletas],
  );
  const categoriasFrecuentes = useMemo(() => catCompletas.map((c) => c.nombre), [catCompletas]);
  const filtrados = useMemo(() => filtrarTransacciones(datos, filtros, hoy), [datos, filtros]);
  // Sobre `datos` y no sobre `filtrados`: el aviso tiene que seguir estando
  // aunque el filtro activo deje los ejemplos fuera de la vista.
  const hayEjemplos = useMemo(() => datos.some((t) => t.es_ejemplo), [datos]);

  const isPro = sesion.data?.is_pro ?? false;

  // El "+" y el tab de Perfil de la barra de navegación en otras páginas
  // (Viajes, Análisis) linkean acá con ?add=1 / ?perfil=1 para abrir el
  // modal correspondiente sin duplicar esa UI en cada página.
  useEffect(() => {
    if (params.get("add") === "1") {
      setEditando(null);
      setTxModalAbierto(true);
      setParams({}, { replace: true });
    } else if (params.get("perfil") === "1") {
      setPerfilModalAbierto(true);
      setParams({}, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Tocar "Inicio" estando ya en el panel es la forma de volver a la vista
   *  limpia: antes lo lograba la recarga completa, ahora se cierra a mano. */
  function cerrarModales() {
    setTxModalAbierto(false);
    setPresupModalAbierto(false);
    setProModalAbierto(false);
    setPerfilModalAbierto(false);
  }

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

  async function cerrarSesion() {
    const ok = await confirmar({
      titulo: trd("dlg_cerrar_sesion_t", lang),
      confirmar: trd("dlg_cerrar_sesion_b", lang),
      cancelar: trd("dlg_cancelar", lang),
    });
    if (ok) window.location.href = "/montor/logout";
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
      <div className={nebula.theme} data-tema="nebula">
        <div className={css.estado}>{lang === "en" ? "Loading…" : "Cargando…"}</div>
      </div>
    );
  }
  if (transacciones.isError || !sesion.data) {
    return (
      <div className={nebula.theme} data-tema="nebula">
        <div className={css.estado}>
          {lang === "en" ? "Could not load the data." : "No se pudieron cargar los datos."}
          <button onClick={() => transacciones.refetch()}>{lang === "en" ? "Retry" : "Reintentar"}</button>
        </div>
      </div>
    );
  }

  const { username, whatsapp_habilitado: whatsappHabilitado, is_trial: isTrial, trial_dias: trialDias } = sesion.data;

  return (
    <div className={nebula.theme} data-tema="nebula">
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
          onPerfil={() => setPerfilModalAbierto(true)}
          onSeccionActiva={cerrarModales}
          className={css.sidenavArea}
        />

        <div className={css.hero}>
          <ConsolidadoCard filtrados={filtrados} cotiz={cotiz} monedaConsol={monedaConsol} onCambiarMoneda={setMonedaConsol} />
        </div>

        <div className={css.der}>
          {hayEjemplos && <EjemplosBanner />}
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
      <ProfileModal
        abierto={perfilModalAbierto}
        onCerrar={() => setPerfilModalAbierto(false)}
        onVerPlanes={() => setProModalAbierto(true)}
      />
    </div>
  );
}
