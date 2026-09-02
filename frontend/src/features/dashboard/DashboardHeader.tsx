import { usePreferencias } from "@/hooks/usePreferencias";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

type Props = {
  username: string;
  isPro: boolean;
  fechaHoy: string;
  onAbrirPro: () => void;
  onCerrarSesion: () => void;
};

export function DashboardHeader({ username, isPro, fechaHoy, onAbrirPro, onCerrarSesion }: Props) {
  const { modo, lang, toggleModo, toggleLang } = usePreferencias();

  return (
    <header className={css.header}>
      <div className={css.headerInner}>
        <div className={css.headerLeft}>
          <div className={css.headerBrand}>
            <svg className={css.headerLogoIcon} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" strokeWidth="7" />
              <rect x="28" y="48" width="9" height="22" rx="3" fill="currentColor" />
              <rect x="45" y="38" width="9" height="32" rx="3" fill="currentColor" />
              <rect x="62" y="28" width="9" height="42" rx="3" fill="currentColor" />
            </svg>
            <h1>Montor</h1>
          </div>
          <p className={css.headerFecha}>{fechaHoy}</p>
        </div>

        <div className={css.headerRight}>
          <div className={css.headerId}>
            <span className={css.headerAvatar}>{(username || "?").slice(0, 1).toUpperCase()}</span>
            <div className={css.headerUsername}>{trd("hola", lang, { n: username })}</div>
          </div>
          <div className={css.headerActions}>
            {isPro ? (
              <span className={`${css.hdrProBadge} ${css.pro}`}>✓ Pro</span>
            ) : (
              <button onClick={onAbrirPro} className={`${css.hdrProBadge} ${css.free}`}>
                ⭐ Pro
              </button>
            )}
            <a href="/montor/viajes" title="Viajes" aria-label="Viajes" className={css.headerMobileLink}>
              ✈️
            </a>
            <a href="/montor/analisis" title="Análisis" aria-label="Análisis" className={css.headerMobileLink}>
              📈
            </a>
            <button onClick={toggleLang} className={css.hdrLangBtn} aria-label="Switch language" title="Switch language">
              {lang === "en" ? "ES" : "EN"}
            </button>
            <button onClick={toggleModo} className={css.hdrIconBtn} aria-label="Cambiar modo claro/oscuro" title="Cambiar modo">
              {modo === "light" ? "☀️" : "🌙"}
            </button>
            <button onClick={onCerrarSesion} className={css.hdrLogout}>
              {trd("salir", lang)}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
