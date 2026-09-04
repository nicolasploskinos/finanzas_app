"""
La imagen de preview al compartir el link (Open Graph).

Lo que se cuida acá es que la URL salga absoluta y en https: los crawlers de
WhatsApp/Twitter no resuelven rutas relativas, y detrás del proxy de
PythonAnywhere `request.host_url` llega como http:// aunque el sitio se sirva
por https. Si eso se rompe, el link compartido vuelve a ser un renglón de
texto sin imagen — y no falla ningún otro test, por eso este.
"""
import os

import routes_paginas


def test_og_image_fuerza_https_en_produccion(client, monkeypatch):
    monkeypatch.delenv("BASE_URL", raising=False)
    html = client.get("/", base_url="http://nicolasploskinos.pythonanywhere.com").get_data(as_text=True)
    assert 'property="og:image"' in html
    assert "https://nicolasploskinos.pythonanywhere.com/static/og-montor.png" in html
    assert "http://nicolasploskinos.pythonanywhere.com/static/og-montor.png" not in html


def test_og_image_respeta_localhost_en_desarrollo(client, monkeypatch):
    """En local no hay TLS: forzar https dejaría la imagen inalcanzable."""
    monkeypatch.delenv("BASE_URL", raising=False)
    html = client.get("/", base_url="http://127.0.0.1:5001").get_data(as_text=True)
    assert "http://127.0.0.1:5001/static/og-montor.png" in html


def test_og_image_lleva_cache_busting(client, monkeypatch):
    """WhatsApp cachea el preview casi para siempre: sin el ?v= no habría
    forma de que vea una imagen nueva."""
    monkeypatch.delenv("BASE_URL", raising=False)
    html = client.get("/", base_url="https://nicolasploskinos.pythonanywhere.com").get_data(as_text=True)
    assert "og-montor.png?v=" in html


def test_og_image_declara_medidas_y_twitter_card(client):
    html = client.get("/").get_data(as_text=True)
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="630">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html


def test_la_imagen_existe_y_pesa_poco(client):
    """WhatsApp descarta previews pesados; y si el archivo no está, la página
    quedaría anunciando una imagen rota."""
    assert os.path.exists(routes_paginas._OG_IMAGEN)
    assert os.path.getsize(routes_paginas._OG_IMAGEN) < 400_000
    assert client.get("/static/og-montor.png").status_code == 200


def test_paginas_privadas_no_publican_og(client):
    """Solo la landing es compartible; el panel exige login y no tiene por qué
    anunciar preview."""
    html = client.get("/terminos").get_data(as_text=True)
    assert 'property="og:image"' not in html
