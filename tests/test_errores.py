"""
Manejo de fallas: una ruta que no existe, o una excepción no atrapada, no
tienen que tirarle al visitante la página de error cruda de Flask - ver
_error_404/_error_500 en montor_server.py.
"""
import montor_server as app_module


def test_404_en_api_devuelve_json(client):
    r = client.get("/api/montor/ruta-que-no-existe")

    assert r.status_code == 404
    assert r.get_json() == {"ok": False, "error": "not_found"}


def test_404_en_pagina_devuelve_html(client):
    r = client.get("/ruta-que-no-existe")

    assert r.status_code == 404
    assert "Página no encontrada" in r.get_data(as_text=True)


def test_500_en_api_devuelve_json():
    with app_module.app.test_request_context("/api/montor/algo"):
        resp, status = app_module._error_500(Exception("boom"))
        assert status == 500
        assert resp.get_json() == {"ok": False, "error": "server_error"}


def test_500_en_pagina_devuelve_html():
    with app_module.app.test_request_context("/montor/algo"):
        html, status = app_module._error_500(Exception("boom"))
        assert status == 500
        assert "Algo salió mal" in html
