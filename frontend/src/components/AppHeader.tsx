import { usePreferencias } from "@/hooks/usePreferencias";
import css from "./AppHeader.module.css";

type Props = {
  icono: string;
  titulo: string;
  /** A dónde vuelve la flecha. Sigue siendo una página Jinja. */
  volverA?: string;
};

export function AppHeader({ icono, titulo, volverA = "/montor" }: Props) {
  const { modo, lang, toggleModo, toggleLang } = usePreferencias();

  return (
    <header className={css.header}>
      <h1 className={css.title}>
        <a className={css.back} href={volverA} aria-label="Volver">
          ←
        </a>
        <span>
          {icono} {titulo}
        </span>
      </h1>
      <div className={css.actions}>
        <button onClick={toggleLang} aria-label="Switch language" title="Switch language">
          {lang === "en" ? "ES" : "EN"}
        </button>
        <button onClick={toggleModo} aria-label="Cambiar modo claro/oscuro" title="Cambiar modo">
          {modo === "light" ? "☀️" : "🌙"}
        </button>
      </div>
    </header>
  );
}
