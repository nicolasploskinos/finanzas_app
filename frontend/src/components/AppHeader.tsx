import { Link } from "react-router-dom";

import { usePreferencias } from "@/hooks/usePreferencias";
import css from "./AppHeader.module.css";

type Props = {
  icono: string;
  titulo: string;
  /** A dónde vuelve la flecha; por defecto, al panel. */
  volverA?: string;
  /** Si se pasa, la flecha ejecuta esto en vez de navegar (p. ej. volver del
   *  detalle de un viaje a la lista sin salir de la página). */
  onVolver?: () => void;
};

export function AppHeader({ icono, titulo, volverA = "/montor", onVolver }: Props) {
  const { modo, lang, toggleModo, toggleLang } = usePreferencias();

  return (
    <header className={css.header}>
      <h1 className={css.title}>
        {onVolver ? (
          <button className={css.back} onClick={onVolver} aria-label="Volver">
            ←
          </button>
        ) : (
          <Link className={css.back} to={volverA} aria-label="Volver">
            ←
          </Link>
        )}
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
