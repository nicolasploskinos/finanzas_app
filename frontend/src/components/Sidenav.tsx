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
};

export function Sidenav({ activa, username, isPro }: Props) {
  const { t } = usePreferencias();

  return (
    <aside className={css.rail}>
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
        {SECCIONES.map((s) =>
          s.id === activa ? (
            <span key={s.id} className={`${css.item} ${css.active}`}>
              <span className={css.ico}>{s.icono}</span>
              <span>{t(s.label)}</span>
            </span>
          ) : (
            // Enlaces normales, no del router: el resto de la app todavía se
            // sirve desde Flask con Jinja. Se cambian a <Link> cuando esas
            // páginas también estén migradas.
            <a key={s.id} className={css.item} href={s.href ?? "#"}>
              <span className={css.ico}>{s.icono}</span>
              <span>{t(s.label)}</span>
            </a>
          ),
        )}
      </nav>

      <div className={css.foot}>
        <div className={css.user}>
          <span className={css.avatar}>{(username || "?").slice(0, 1).toUpperCase()}</span>
          <div className={css.userTxt}>
            <div className={css.userName}>{username}</div>
            <div className={css.userPlan}>{isPro ? t("plan_pro") : t("plan_gratis")}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
