import { useId } from "react";

/**
 * La marca de Montor. Un solo dibujo, en un solo lugar.
 *
 * Antes el SVG estaba copiado a mano en seis componentes, así que cambiar la
 * marca implicaba tocar seis archivos y acordarse de todos.
 *
 * Es una M, pero con las patas de distinta altura y las puntas redondeadas:
 * el trazo del medio funciona como el valle de un gráfico y la pata derecha
 * como el pico, con el punto marcando el máximo. Así se lee "M" y se lee
 * "esto sube" — "Montor" viene de monitorear. Esa asimetría es también lo
 * que la separa de las M simétricas y puntiagudas de otras marcas.
 *
 * `placa` NO es otro logo: es el mismo trazo sobre el cuadrado violeta, para
 * cuando va solo y necesita fondo propio (ícono de la pantalla de inicio,
 * favicon). Ahí el trazo va blanco porque el violeta del degradado sobre el
 * violeta de la placa no se vería. El PNG de esos íconos se genera con
 * generar_iconos.py, desde este mismo dibujo.
 */

type Props = {
  /** `marca` (por defecto): sobre fondo transparente, para acompañar al
   *  texto "Montor". `placa`: sobre el cuadrado violeta. */
  variante?: "marca" | "placa";
  className?: string;
  /** Tamaño en px. Si se omite, lo define el CSS de quien lo usa. */
  size?: number;
};

export function LogoMontor({ variante = "marca", className, size }: Props) {
  // Un id distinto POR INSTANCIA, no por variante. Los id de un SVG son
  // globales al documento: si dos logos comparten uno, todos resuelven
  // contra el primero que aparece en el DOM. Eso rompía el logo de la barra
  // lateral, porque el header del panel también renderiza uno y el suyo va
  // antes, adentro de un contenedor con display:none — un degradado que no
  // se renderiza no pinta nada, así que quedaba invisible.
  const id = useId();
  const grad = `montor-grad-${id}`;

  const conPlaca = variante === "placa";

  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Montor"
    >
      <defs>
        {conPlaca ? (
          <linearGradient id={grad} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#8f74ff" />
            <stop offset="1" stopColor="#5a3ce0" />
          </linearGradient>
        ) : (
          /* Colores fijos y no var(--blue): la landing y la app definen
             azules distintos, así que tomarlos del tema hacía que la marca
             saliera azul en una y violeta en la otra. */
          <linearGradient id={grad} x1="0" y1="1" x2="1" y2="0">
            <stop offset="0" stopColor="#7c5cff" />
            <stop offset="1" stopColor="#00e0a4" />
          </linearGradient>
        )}
      </defs>

      {conPlaca && <rect x="0" y="0" width="100" height="100" rx="22" fill={`url(#${grad})`} />}

      <path
        d={conPlaca ? "M31 72 L31 42 L50 60 L69 31 L69 72" : "M24 76 L24 38 L50 62 L76 26 L76 76"}
        fill="none"
        stroke={conPlaca ? "#fff" : `url(#${grad})`}
        strokeWidth={conPlaca ? 10 : 12}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        cx={conPlaca ? 69 : 76}
        cy={conPlaca ? 31 : 26}
        r={conPlaca ? 7 : 8}
        fill="#00e0a4"
        stroke={conPlaca ? "#5a3ce0" : "none"}
        strokeWidth={conPlaca ? 2.5 : 0}
      />
    </svg>
  );
}
