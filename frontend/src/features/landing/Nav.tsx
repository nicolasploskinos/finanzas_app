import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import { NAV_LINKS } from "./content";
import css from "./Landing.module.css";
import { LogoMontor } from "@/components/LogoMontor";

export function Nav() {
  const { modo, lang, toggleModo, toggleLang } = usePreferencias();

  return (
    <nav className={css.nav}>
      <div className={css.navLogo}>
        <LogoMontor size={26} />
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
        {/* Dos rótulos: en celular el texto largo no entra junto al logo y los
            dos botones, y el CTA terminaba cortado contra el borde. */}
        <Link to="/montor/login" className={css.navCta}>
          <span className={css.ctaLargo}>{lang === "en" ? "Create account →" : "Crear cuenta →"}</span>
          <span className={css.ctaCorto}>{lang === "en" ? "Sign up →" : "Crear cuenta →"}</span>
        </Link>
      </div>
    </nav>
  );
}
