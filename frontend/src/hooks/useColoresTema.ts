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
  const cs = getComputedStyle(document.body);
  return Object.fromEntries(
    TOKENS.map((t) => [t, cs.getPropertyValue(`--${t}`).trim()]),
  ) as Record<Token, string>;
}
