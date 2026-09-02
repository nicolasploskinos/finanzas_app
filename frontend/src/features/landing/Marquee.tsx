import { Fragment } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import { MARQUEE_ITEMS } from "./content";
import css from "./Landing.module.css";

export function Marquee() {
  const { lang } = usePreferencias();
  // Duplicado para el loop continuo (la animación desplaza -50%, así que la
  // segunda mitad idéntica hace que el corte sea invisible).
  const items = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS];

  return (
    <div className={css.marquee} aria-hidden="true">
      <div className={css.marqueeTrack}>
        {items.map((item, i) => (
          <Fragment key={i}>
            <span>{item[lang]}</span>
            <span className={css.dot}>•</span>
          </Fragment>
        ))}
      </div>
    </div>
  );
}
