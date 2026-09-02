import { useEffect, useState } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";

const TOKENS = ["muted", "border", "green", "red", "blue"] as const;
type Token = (typeof TOKENS)[number];

/**
 * Chart.js necesita colores concretos, no `var(--x)`, así que hay que leer los
 * tokens ya resueltos. Se releen al cambiar de tema para que los gráficos
 * acompañen el modo claro/oscuro.
 */
export function useColoresTema(): Record<Token, string> {
  const { modo } = usePreferencias();
  const [colores, setColores] = useState<Record<Token, string>>(() => leer());

  useEffect(() => {
    setColores(leer());
  }, [modo]);

  return colores;
}

function leer(): Record<Token, string> {
  // Las páginas con el tema "Nébula" (ver nebula.module.css) redefinen estos
  // tokens en un <div> interno, no en <body> — por eso se busca ese nodo
  // primero. Las páginas que todavía no lo adoptaron no tienen ese atributo,
  // así que caen a <body> como antes.
  const el = document.querySelector<HTMLElement>("[data-tema='nebula']") ?? document.body;
  const cs = getComputedStyle(el);
  return Object.fromEntries(
    TOKENS.map((t) => [t, cs.getPropertyValue(`--${t}`).trim()]),
  ) as Record<Token, string>;
}
