import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import { NAV_LINKS } from "./content";
import css from "./Landing.module.css";

export function Nav() {
  const { modo, lang, toggleModo, toggleLang } = usePreferencias();

  return (
    <nav className={css.nav}>
      <div className={css.navLogo}>
        <svg
          width="26"
          height="26"
          viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
          style={{ color: "var(--blue)", flexShrink: 0 }}
        >
          <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" strokeWidth="7" />
          <rect x="28" y="48" width="9" height="22" rx="3" fill="currentColor" />
          <rect x="45" y="38" width="9" height="32" rx="3" fill="currentColor" />
          <rect x="62" y="28" width="9" height="42" rx="3" fill="currentColor" />
        </svg>
        <span>Montor</span>
      </div>

      <div className={css.navLinks}>
        {NAV_LINKS.map((l) => (
          <a key={l.href} href={l.href}>
            {l.label[lang]}
          </a>
        ))}
      </div>

      <div className={css.navRight}>
        <button
          className={css.langBtn}
          onClick={toggleLang}
          title="Switch language"
          aria-label="Switch language"
        >
          {lang === "en" ? "ES" : "EN"}
        </button>
        <button
          className={css.iconBtn}
          onClick={toggleModo}
          title="Cambiar modo"
          aria-label="Cambiar modo claro/oscuro"
        >
          {modo === "light" ? "☀️" : "🌙"}
        </button>
        {/* Dos rótulos: en celular "Empezar gratis →" no entra junto al logo y
            los dos botones, y el CTA terminaba cortado contra el borde. */}
        <Link to="/montor/login" className={css.navCta}>
          <span className={css.ctaLargo}>{lang === "en" ? "Start free →" : "Empezar gratis →"}</span>
          <span className={css.ctaCorto}>{lang === "en" ? "Start →" : "Empezar →"}</span>
        </Link>
      </div>
    </nav>
  );
}
