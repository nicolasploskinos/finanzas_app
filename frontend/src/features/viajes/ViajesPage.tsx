import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useSesion, useViaje, useViajes } from "@/api/queries";
import type { Viaje } from "@/api/types";
import { AppHeader } from "@/components/AppHeader";
import { Sidenav } from "@/components/Sidenav";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon, formatFecha } from "@/lib/formato";
import { ViajeDetalle } from "./ViajeDetalle";
import { ViajeModal } from "./ViajeModal";
import css from "./Viajes.module.css";

function ListaViajes({
  viajes,
  onAbrir,
}: {
  viajes: Viaje[];
  onAbrir: (id: number) => void;
}) {
  const { t, lang } = usePreferencias();

  if (!viajes.length) return <div className={css.vacio}>{t("sin_viajes")}</div>;

  return (
    <div className={css.lista}>
      {viajes.map((v, i) => {
        const gastado = v.gastado?.USD ?? 0;
        return (
          <button
            key={v.id}
            className={`${css.card} stagger-in`}
            style={{ animationDelay: `${Math.min(i, 10) * 50}ms` }}
            onClick={() => onAbrir(v.id)}
          >
            <div className={css.cardNombre}>{v.nombre}</div>
            <div className={css.cardFechas}>
              {formatFecha(v.fecha_inicio, lang)} — {formatFecha(v.fecha_fin, lang)}
            </div>
            {gastado ? (
              <div className={css.cardGastoLabels}>
                <span className={css.cardGastoName}>{t("gastado")}</span>
                <span className={css.cardGastoAmt}>{fmtMon(gastado, "USD")}</span>
              </div>
            ) : (
              <div className={css.cardSinGasto}>{t("sin_gastos_reg_todavia")}</div>
            )}
          </button>
        );
      })}
    </div>
  );
}

export function ViajesPage() {
  const { t } = usePreferencias();
  const sesion = useSesion();

  // El detalle se direcciona con ?id=N, igual que antes: así los enlaces y
  // favoritos que ya existían siguen funcionando. El router se encarga del
  // historial, no hace falta pushState a mano.
  const [params, setParams] = useSearchParams();
  const idParam = params.get("id");
  const viajeId = idParam && /^\d+$/.test(idParam) ? Number(idParam) : null;

  const viajes = useViajes();
  const detalle = useViaje(viajeId);
  const [editando, setEditando] = useState<Viaje | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);

  // Desde el detalle la flecha vuelve a la lista, no al panel.
  const header = (
    <AppHeader
      icono="✈️"
      titulo={t("viajes")}
      onVolver={viajeId !== null ? () => setParams({}) : undefined}
    />
  );

  if (sesion.isPending) {
    return (
      <>
        {header}
        <div className={css.estado}>{t("cargando")}</div>
      </>
    );
  }

  const { username = "", is_pro: isPro = false } = sesion.data ?? {};

  if (!isPro) {
    return (
      <>
        {header}
        <div className={css.estado}>
          <h2>{t("viajes_solo_pro")}</h2>
          <p>{t("viajes_solo_pro_detalle")}</p>
          <a href="/montor">{t("volver_a_montor")}</a>
        </div>
      </>
    );
  }

  const irALista = () => setParams({});
  const abrirDetalle = (id: number) => setParams({ id: String(id) });

  const abrirModal = (viaje: Viaje | null) => {
    setEditando(viaje);
    setModalAbierto(true);
  };

  return (
    <>
      {header}
      <div className={css.shell}>
        <Sidenav activa="viajes" username={username} isPro={isPro} />

        <div className={css.content}>
          {viajeId !== null ? (
            <ViajeDetalle
              id={viajeId}
              onVolver={irALista}
              onEditar={() => abrirModal(detalle.data?.viaje ?? null)}
            />
          ) : viajes.isPending ? (
            <div className={css.estado}>{t("cargando")}</div>
          ) : (
            <ListaViajes viajes={viajes.data ?? []} onAbrir={abrirDetalle} />
          )}
        </div>
      </div>

      {viajeId === null && (
        <button className={css.fab} onClick={() => abrirModal(null)} aria-label={t("nuevo_viaje")}>
          +
        </button>
      )}

      <ViajeModal
        abierto={modalAbierto}
        viaje={editando}
        onCerrar={() => setModalAbierto(false)}
        // Al crear uno nuevo se entra directo a su detalle; al editar ya
        // estabas ahí y alcanza con que el modal se cierre.
        onGuardado={(v) => {
          if (!editando) abrirDetalle(v.id);
        }}
      />
    </>
  );
}
