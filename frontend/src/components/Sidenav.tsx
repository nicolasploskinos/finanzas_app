import { Link } from "react-router-dom";

import { usePreferencias } from "@/hooks/usePreferencias";
import type { MsgKey } from "@/i18n/messages";
import css from "./Sidenav.module.css";
import { LogoMontor } from "@/components/LogoMontor";

/** Secciones de la app. `href` null = la sección en la que ya estás. */
type Seccion = { id: string; icono: string; label: MsgKey; href: string | null };

const SECCIONES: Seccion[] = [
  { id: "inicio", icono: "🏠", label: "inicio", href: "/montor" },
  { id: "nueva", icono: "➕", label: "nueva_transaccion", href: "/montor?add=1" },
  { id: "analisis", icono: "📈", label: "analisis", href: "/montor/analisis" },
  { id: "viajes", icono: "✈️", label: "viajes", href: "/montor/viajes" },
];

type Props = {
  /** id de la sección activa (ver SECCIONES). */
  activa: string;
  username: string;
  isPro: boolean;
  /** Solo en el panel: "Nueva transacción" abre el modal ahí mismo en vez
   *  de navegar a `/montor?add=1` (esa URL existe para volver desde otra
   *  página, no hace falta cuando ya estás en el panel). */
  onNuevaTransaccion?: () => void;
  /** Solo en el panel: agrega el botón "Pasar a Pro" abajo del todo. */
  onUpgrade?: () => void;
  /** Solo en el panel: hace clickeable el bloque de usuario/plan de abajo,
   *  para abrir el perfil (cambiar nombre, contraseña, suscripción). */
  onPerfil?: () => void;
  /** Tocar la sección en la que ya estás sirve para "volver": antes eso
   *  recargaba la página y cerraba de paso cualquier modal abierto encima.
   *  Ahora que se navega del lado del cliente no hay remonte, así que la
   *  página avisa por acá para cerrar lo que tenga abierto. */
  onSeccionActiva?: () => void;
  /** Para que quien usa este componente pueda ubicarlo en su propio grid
   *  (p.ej. hacer que ocupe dos filas en el panel principal). Un className
   *  externo, no una clase con el mismo nombre en OTRO archivo: por cómo
   *  escopea CSS Modules, una regla `.sidenav { grid-row: ... }` escrita en
   *  el CSS de quien lo usa NUNCA matchea este `<aside>` — cada módulo
   *  genera su propio nombre de clase hasheado. */
  className?: string;
};

export function Sidenav({
  activa,
  username,
  isPro,
  onNuevaTransaccion,
  onUpgrade,
  onPerfil,
  onSeccionActiva,
  className = "",
}: Props) {
  const { t } = usePreferencias();

  const contenidoUsuario = (
    <>
      <span className={css.avatar}>{(username || "?").slice(0, 1).toUpperCase()}</span>
      <div className={css.userTxt}>
        <div className={css.userName}>{username}</div>
        <div className={css.userPlan}>{isPro ? t("plan_pro") : t("plan_gratis")}</div>
      </div>
      <span className={css.userChevron}>›</span>
    </>
  );

  return (
    <aside className={`${css.rail} ${className}`}>
      <div className={css.brand}>
        <LogoMontor className={css.logo} />
        <span className={css.brandName}>Montor</span>
      </div>

      <div className={css.label}>{t("menu")}</div>

      <nav className={css.nav}>
        {SECCIONES.map((s) => {
          if (s.id === activa) {
            // Sigue siendo clickeable aunque ya estés acá: en mobile es la
            // forma de "volver" cuando hay un modal abierto encima (Nueva
            // transacción, Perfil).
            return (
              <Link
                key={s.id}
                className={`${css.item} ${css.active}`}
                to={s.href ?? "#"}
                onClick={onSeccionActiva}
              >
                <span className={css.ico}>{s.icono}</span>
                <span className={css.itemLabel}>{t(s.label)}</span>
              </Link>
            );
          }
          if (s.id === "nueva" && onNuevaTransaccion) {
            return (
              <button key={s.id} className={css.item} onClick={onNuevaTransaccion}>
                <span className={css.ico}>{s.icono}</span>
                <span className={css.itemLabel}>{t(s.label)}</span>
              </button>
            );
          }
          return (
            <Link key={s.id} className={css.item} to={s.href ?? "#"}>
              <span className={css.ico}>{s.icono}</span>
              <span className={css.itemLabel}>{t(s.label)}</span>
            </Link>
          );
        })}
        {/* Solo en mobile (ver Sidenav.module.css): la barra de abajo suma un
         *  acceso directo al perfil, que en escritorio ya está en .foot. Si
         *  no estamos en el panel (no hay onPerfil) navega para abrirlo ahí,
         *  igual que "Nueva transacción" con ?add=1. */}
        {onPerfil ? (
          <button className={`${css.item} ${css.perfilTab}`} onClick={onPerfil}>
            <span className={css.ico}>👤</span>
            <span className={css.itemLabel}>{t("perfil_tab")}</span>
          </button>
        ) : (
          <Link className={`${css.item} ${css.perfilTab}`} to="/montor?perfil=1">
            <span className={css.ico}>👤</span>
            <span className={css.itemLabel}>{t("perfil_tab")}</span>
          </Link>
        )}
      </nav>

      <div className={css.foot}>
        {!isPro && onUpgrade && (
          <button className={css.pro} onClick={onUpgrade}>
            {t("pasar_a_pro")}
          </button>
        )}
        {/* El bloque de usuario/plan abre el perfil desde cualquier página:
         *  en el panel llama al modal directo, y en el resto navega al panel
         *  con ?perfil=1 para que lo abra ahí (mismo patrón que el tab de
         *  Perfil de la barra de abajo en mobile). */}
        {onPerfil ? (
          <button className={`${css.user} ${css.userBtn}`} onClick={onPerfil}>
            {contenidoUsuario}
          </button>
        ) : (
          <Link className={`${css.user} ${css.userBtn}`} to="/montor?perfil=1">
            {contenidoUsuario}
          </Link>
        )}
      </div>
    </aside>
  );
}
