"""
Íconos para "Agregar a pantalla de inicio".

Esto se rompe en silencio: nadie lo nota hasta que alguien agrega la app al
inicio del celular y le aparece una captura de la página en vez del logo.
Por eso se testea, aunque sean sólo archivos estáticos.

Lo que se cuida:
- que exista el apple-touch-icon en el HTML (iOS ignora el manifest y usa
  SOLO esto para el ícono de inicio),
- que sea PNG (iOS no soporta SVG ahí),
- que el manifest ofrezca PNG y tenga un maskable aparte del normal.
"""
import json
import os
import struct

import routes_paginas

ICONOS = os.path.join(os.path.dirname(routes_paginas._OG_IMAGEN), "icons")


def _dimensiones(nombre):
    """Ancho y alto leídos del encabezado IHDR del PNG."""
    with open(os.path.join(ICONOS, nombre), "rb") as f:
        f.read(16)
        return struct.unpack(">II", f.read(8))


def test_el_html_declara_el_apple_touch_icon(client):
    """Sin esto, un iPhone pone una captura de la página como ícono."""
    html = client.get("/montor/login").get_data(as_text=True)

    assert 'rel="apple-touch-icon"' in html
    assert "/static/icons/apple-touch-icon.png" in html


def test_el_apple_touch_icon_es_png_de_180(client):
    """iOS no acepta SVG en apple-touch-icon, y 180x180 es lo que pide."""
    assert _dimensiones("apple-touch-icon.png") == (180, 180)

    r = client.get("/static/icons/apple-touch-icon.png")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "image/png"


def test_el_manifest_ofrece_png_y_un_maskable(client):
    """El maskable va aparte: el sistema le aplica su propia máscara y le
    recorta hasta un 20% de cada borde, así que no puede ser el mismo
    archivo que el normal."""
    manifest = json.loads(client.get("/montor/manifest.json").get_data(as_text=True))
    iconos = manifest["icons"]

    assert all(i["type"] == "image/png" for i in iconos)
    propositos = {i["purpose"] for i in iconos}
    assert "any" in propositos and "maskable" in propositos
    # No pueden ser el mismo archivo (ver el motivo arriba).
    normal = next(i["src"] for i in iconos if i["purpose"] == "any" and i["sizes"] == "512x512")
    maskable = next(i["src"] for i in iconos if i["purpose"] == "maskable")
    assert normal != maskable


def test_los_iconos_del_manifest_existen_y_miden_lo_que_dicen(client):
    manifest = json.loads(client.get("/montor/manifest.json").get_data(as_text=True))

    for icono in manifest["icons"]:
        r = client.get(icono["src"])
        assert r.status_code == 200, icono["src"]
        ancho, alto = (int(n) for n in icono["sizes"].split("x"))
        assert _dimensiones(os.path.basename(icono["src"])) == (ancho, alto), icono["src"]
