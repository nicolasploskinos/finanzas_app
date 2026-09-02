import { useRef } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import type { HERO_TILES } from "./content";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

const TILE_CLASS = { blue: css.tileBlue, purple: css.tilePurple, green: css.tileGreen };

type Props = {
  tile: (typeof HERO_TILES)[number];
  index: number;
  contenedor: HTMLElement | null;
};

export function HeroTile({ tile, index, contenedor }: Props) {
  const { lang } = usePreferencias();
  const ref = useRef<HTMLDivElement | null>(null);

  // Tilt 3D siguiendo el cursor: va directo a las custom properties CSS
  // (--tiltX/--tiltY, que .heroTile:hover ya usa en su transform) del MISMO
  // div que tiene la clase heroTile — no a un estado de React, esto dispara
  // en cada mousemove y es puramente decorativo.
  function alMover(e: React.MouseEvent<HTMLDivElement>) {
    if (!window.matchMedia("(pointer: fine)").matches) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    el.style.setProperty("--tiltX", `${y * -10}deg`);
    el.style.setProperty("--tiltY", `${x * 10}deg`);
  }
  function alSalir() {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--tiltX", "0deg");
    el.style.setProperty("--tiltY", "0deg");
  }

  return (
    <Reveal
      contenedor={contenedor}
      index={index}
      className={`${css.heroTile} ${TILE_CLASS[tile.tile]}`}
      elRef={ref}
      onMouseMove={alMover}
      onMouseLeave={alSalir}
    >
      <div className={css.heroTileIcon}>{tile.icon}</div>
      <h3>{tile.title[lang]}</h3>
      <p>{tile.body[lang]}</p>
    </Reveal>
  );
}
