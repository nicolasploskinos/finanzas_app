import { useId } from "react";

/**
 * La marca de Montor, en un solo lugar.
 *
 * Antes el SVG estaba copiado a mano en seis componentes (barra, header,
 * login, nav y pie de la landing, y la ventanita de la demo), así que
 * cambiar la marca implicaba tocar seis archivos y acordarse de todos.
 *
 * La M no es un monograma cualquiera: las dos patas tienen distinta altura y
 * el punto marca el máximo, así que además de leerse "M" se lee como un
 * gráfico que sube — que es lo que hace la app. Las puntas redondeadas y esa
 * asimetría son también lo que la separa de la M simétrica y puntiaguda que
 * usan otras marcas.
 */

/** El trazo de la M. Compartido por las dos variantes para que no se puedan
 *  desincronizar. */
const TRAZO_M = "M24 76 L24 38 L50 62 L76 26 L76 76";

type Props = {
  /** `marca` (por defecto): el trazo suelto con degradado, para acompañar al
   *  texto "Montor". `placa`: sobre el cuadrado violeta, para cuando el logo
   *  va solo y necesita presencia propia (ícono de app, favicon). */
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
  // se renderiza no pinta nada, así que la M quedaba invisible.
  const idGrad = `montor-grad-${useId()}`;

  if (variante === "placa") {
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
          <linearGradient id={idGrad} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#8f74ff" />
            <stop offset="1" stopColor="#5a3ce0" />
          </linearGradient>
        </defs>
        <rect x="6" y="6" width="88" height="88" rx="22" fill={`url(#${idGrad})`} />
        <path
          d="M31 72 L31 42 L50 60 L69 31 L69 72"
          fill="none"
          stroke="#fff"
          strokeWidth="10"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="69" cy="31" r="7" fill="#00e0a4" stroke="#5a3ce0" strokeWidth="2.5" />
      </svg>
    );
  }

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
      {/* Colores fijos, no var(--blue): la landing y la app definen azules
          distintos, así que tomarlos del tema hacía que la marca apareciera
          azul en una y violeta en la otra. Un logo es el mismo en todos
          lados; por eso también van acá los valores y no los tokens. */}
      <defs>
        <linearGradient id={idGrad} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#7c5cff" />
          <stop offset="1" stopColor="#00e0a4" />
        </linearGradient>
      </defs>
      <path
        d={TRAZO_M}
        fill="none"
        stroke={`url(#${idGrad})`}
        strokeWidth="12"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="76" cy="26" r="8" fill="#00e0a4" />
    </svg>
  );
}
