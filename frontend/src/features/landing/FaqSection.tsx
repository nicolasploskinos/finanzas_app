import { useState } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import { FAQ_ITEMS } from "./content";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

export function FaqSection({ contenedor }: { contenedor: HTMLElement | null }) {
  const { lang } = usePreferencias();
  // Cada pregunta se abre/cierra independiente; varias pueden estar
  // abiertas a la vez, igual que en la versión original (toggleFaq solo
  // tocaba el ítem clickeado).
  const [abiertas, setAbiertas] = useState<Set<number>>(new Set());

  function toggle(i: number) {
    setAbiertas((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  return (
    <section className={css.section} id="faq">
      <div className={css.sectionLabel}>
        <span className={css.num}>05</span> — FAQ
      </div>
      <h2 className={css.h2}>{lang === "en" ? "Frequently asked questions" : "Preguntas frecuentes"}</h2>
      <div className={css.faqList}>
        {FAQ_ITEMS.map((item, i) => {
          const open = abiertas.has(i);
          return (
            <Reveal key={item.q.es} contenedor={contenedor} index={i} className={css.faqItem}>
              <button
                className={`${css.faqQ} ${open ? css.open : ""}`}
                onClick={() => toggle(i)}
                aria-expanded={open}
              >
                <span>{item.q[lang]}</span>
                <span className={css.faqToggle}>+</span>
              </button>
              <div className={`${css.faqAWrap} ${open ? css.open : ""}`}>
                <div>
                  <div className={css.faqA}>{item.a[lang]}</div>
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
