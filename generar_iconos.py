"""
Genera los PNG del ícono de la app a partir de un SVG.

Por qué PNG y no el SVG que ya tenemos: iOS ignora por completo el manifest al
"Agregar a pantalla de inicio" — usa <link rel="apple-touch-icon">, que no
acepta SVG. Sin un PNG ahí, el iPhone pone una captura de la página como
ícono. En Android el manifest sí manda, pero el soporte de SVG en los
launchers es despareja, así que PNG es lo seguro en los dos lados.

Se generan dos familias:
  - normal:   el dibujo completo con sus esquinas redondeadas.
  - maskable: el mismo dibujo más chico y sobre un fondo a sangre, porque el
              sistema le aplica SU propia máscara (círculo, squircle, etc.) y
              recorta hasta un 20% de cada borde. Si se le pasa el ícono
              normal, le come las esquinas y parte del dibujo.

Uso: python generar_iconos.py
"""
import os

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(BASE, "static", "icons")

# La billetera: dos tarjetas asomando (las monedas) y la M de la marca al
# frente. Mismo trazo que components/LogoMontor.tsx.
def dibujo(escala=1.0, sangre=False):
    """`escala` < 1 encoge el dibujo para la versión maskable."""
    fondo = (
        "<rect width='100' height='100' fill='url(#g)'/>"
        if sangre
        else "<rect width='100' height='100' rx='22' fill='url(#g)'/>"
    )
    # El grupo se escala desde el centro para dejar margen a la máscara.
    d = 50 * (1 - escala)
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" style="width:100%;height:100%;display:block">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#8f74ff"/><stop offset="1" stop-color="#5a3ce0"/>
    </linearGradient>
    <linearGradient id="cuerpo" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".22"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity=".06"/>
    </linearGradient>
  </defs>
  {fondo}
  <g transform="translate({d},{d}) scale({escala})">
    <!-- Tarjetas asomando por arriba: son las otras dos monedas. Quedan
         detrás del cuerpo, apenas sobresaliendo, como en una billetera real. -->
    <rect x="31" y="19" width="40" height="22" rx="5" fill="#2fe6c7" transform="rotate(-7 51 30)"/>
    <rect x="33" y="24" width="40" height="22" rx="5" fill="#ffb93d" transform="rotate(-2 53 35)"/>
    <!-- Cuerpo: violeta MÁS OSCURO que la placa, no translúcido. Con blanco
         al 20% las tarjetas se transparentaban y el ícono quedaba sucio. -->
    <rect x="19" y="38" width="62" height="41" rx="11" fill="#4526b8"/>
    <rect x="19" y="38" width="62" height="12" rx="11" fill="#ffffff" fill-opacity=".12"/>
    <!-- La M. Sin el punto verde que sí lleva la marca suelta: acá la M es
         más angosta y el punto sobre la pata derecha la hacía leer "Mi". La
         pata más alta ya transmite sola la idea de que sube. -->
    <path d="M38 69 L38 55 L50 65 L62 50 L62 69" fill="none" stroke="#fff"
          stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>"""


# (archivo, lado en px, svg)
ICONOS = [
    # iOS: 180 es el tamaño que pide Safari. Va sin transparencia porque iOS
    # no respeta el alfa y pinta el fondo de negro.
    ("apple-touch-icon.png", 180, dibujo(1.0)),
    ("icon-192.png", 192, dibujo(1.0)),
    ("icon-512.png", 512, dibujo(1.0)),
    # Maskable: dibujo al 72% sobre fondo a sangre (deja el margen del 20%
    # que el sistema puede recortar, con aire de sobra).
    ("icon-maskable-512.png", 512, dibujo(0.72, sangre=True)),
]


def main():
    os.makedirs(SALIDA, exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        for nombre, lado, svg in ICONOS:
            page = navegador.new_page(viewport={"width": lado, "height": lado})
            # El SVG se estira al div: si lleva width/height propios, la
            # captura sale siempre del tamaño intrínseco y no del pedido.
            page.set_content(
                f"<body style='margin:0'>"
                f"<div style='width:{lado}px;height:{lado}px;line-height:0'>{svg}</div>"
                f"</body>"
            )
            page.wait_for_timeout(180)
            destino = os.path.join(SALIDA, nombre)
            page.locator("div").screenshot(path=destino, omit_background=False)
            page.close()
            print(f"OK {nombre} ({lado}x{lado}, {os.path.getsize(destino)} bytes)")
        navegador.close()


if __name__ == "__main__":
    main()
