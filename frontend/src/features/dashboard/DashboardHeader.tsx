import { Link } from "react-router-dom";

import { usePreferencias } from "@/hooks/usePreferencias";
import { trd } from "./messages";
import css from "./Dashboard.module.css";
import { LogoMontor } from "@/components/LogoMontor";

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
            <LogoMontor className={css.headerLogoIcon} />
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
            <Link to="/montor/viajes" title="Viajes" aria-label="Viajes" className={css.headerMobileLink}>
              ✈️
            </Link>
            <Link to="/montor/analisis" title="Análisis" aria-label="Análisis" className={css.headerMobileLink}>
              📈
            </Link>
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
