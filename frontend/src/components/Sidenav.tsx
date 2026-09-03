import { usePreferencias } from "@/hooks/usePreferencias";
import type { MsgKey } from "@/i18n/messages";
import css from "./Sidenav.module.css";

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
  /** Para que quien usa este componente pueda ubicarlo en su propio grid
   *  (p.ej. hacer que ocupe dos filas en el panel principal). Un className
   *  externo, no una clase con el mismo nombre en OTRO archivo: por cómo
   *  escopea CSS Modules, una regla `.sidenav { grid-row: ... }` escrita en
   *  el CSS de quien lo usa NUNCA matchea este `<aside>` — cada módulo
   *  genera su propio nombre de clase hasheado. */
  className?: string;
};

export function Sidenav({ activa, username, isPro, onNuevaTransaccion, onUpgrade, onPerfil, className = "" }: Props) {
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
        <svg className={css.logo} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" strokeWidth="7" />
          <rect x="28" y="48" width="9" height="22" rx="3" fill="currentColor" />
          <rect x="45" y="38" width="9" height="32" rx="3" fill="currentColor" />
          <rect x="62" y="28" width="9" height="42" rx="3" fill="currentColor" />
        </svg>
        <span className={css.brandName}>Montor</span>
      </div>

      <div className={css.label}>{t("menu")}</div>

      <nav className={css.nav}>
        {SECCIONES.map((s) => {
          if (s.id === activa) {
            // Clickeable aunque ya estés acá: en mobile es la forma de
            // "volver al panel" cuando hay un modal abierto encima (Nueva
            // transacción, Perfil) — al navegar de nuevo a esta misma
            // sección, la página se remonta entera y el modal se cierra
            // solo. En escritorio es una recarga redundante pero inofensiva.
            return (
              <a key={s.id} className={`${css.item} ${css.active}`} href={s.href ?? "#"}>
                <span className={css.ico}>{s.icono}</span>
                <span className={css.itemLabel}>{t(s.label)}</span>
              </a>
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
          // Enlaces normales, no del router: navegan con una recarga
          // completa en vez de una transición de React Router.
          return (
            <a key={s.id} className={css.item} href={s.href ?? "#"}>
              <span className={css.ico}>{s.icono}</span>
              <span className={css.itemLabel}>{t(s.label)}</span>
            </a>
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
          <a className={`${css.item} ${css.perfilTab}`} href="/montor?perfil=1">
            <span className={css.ico}>👤</span>
            <span className={css.itemLabel}>{t("perfil_tab")}</span>
          </a>
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
          <a className={`${css.user} ${css.userBtn}`} href="/montor?perfil=1">
            {contenidoUsuario}
          </a>
        )}
      </div>
    </aside>
  );
}
