import type { HTMLAttributes, ReactNode, Ref } from "react";

import css from "./Landing.module.css";
import { useReveal } from "./useReveal";

type Props = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  /** Contenedor que scrollea (el div fixed de la página). */
  contenedor: HTMLElement | null;
  /** Índice dentro de su grupo, para el escalonado de 70ms × (i % 4). */
  index?: number;
  /** Clase semántica del propio elemento (featCard, heroTile, etc.) — se
   *  aplica en el MISMO div que reveal/in, no en un wrapper aparte, para no
   *  alterar el layout de grid/columnas del que ese div es hijo directo. */
  className?: string;
  /** Para cuando el que llama también necesita el nodo real (p.ej. el tilt
   *  3D de HeroTile, que lee/escribe custom properties CSS en él). */
  elRef?: Ref<HTMLDivElement>;
};

export function Reveal({ children, contenedor, index = 0, className = "", elRef, style, ...rest }: Props) {
  const { ref, revelado } = useReveal<HTMLDivElement>(contenedor);

  return (
    <div
      ref={(node) => {
        ref.current = node;
        if (typeof elRef === "function") elRef(node);
        else if (elRef) (elRef as { current: HTMLDivElement | null }).current = node;
      }}
      className={`${className} ${css.reveal} ${revelado ? css.in : ""}`}
      style={{ transitionDelay: `${(index % 4) * 70}ms`, ...style }}
      {...rest}
    >
      {children}
    </div>
  );
}
