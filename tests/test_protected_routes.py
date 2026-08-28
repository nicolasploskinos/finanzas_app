"""
Todo lo que cuelga de @login_required tiene que rebotar a alguien sin
sesión, pase lo que pase con la base de datos. El chequeo de sesión pasa
antes que cualquier consulta, así que estos tests no necesitan fake_db.
"""
import pytest

import montor_server as app_module

RUTAS_PROTEGIDAS = [
    "/montor",
    "/montor/viajes",
    "/api/montor",
    "/api/montor/viajes",
    "/api/montor/presupuestos",
    "/api/montor/recurrentes",
    "/api/montor/stats",
    "/api/montor/resumen-ia",
]


@pytest.mark.parametrize("ruta", RUTAS_PROTEGIDAS)
def test_sin_sesion_no_expone_datos(client, ruta):
    r = client.get(ruta)
    assert r.status_code in (302, 401, 403)
    if r.status_code == 302:
        assert "/montor/login" in r.headers["Location"]


def test_cotizaciones_es_publica_a_proposito(client, monkeypatch):
    # Esta sí no lleva @login_required: el conversor de la landing la necesita
    # sin que el usuario haya iniciado sesión. Mockeamos la cotización para
    # no depender de la API externa (bluelytics) en el test.
    monkeypatch.setattr(app_module, "_obtener_cotizaciones",
                         lambda: {"USD": 1500.0, "EUR": 1650.0})
    r = client.get("/api/montor/cotizaciones")
    assert r.status_code == 200
    assert r.get_json() == {"USD": 1500.0, "EUR": 1650.0}


def test_logout_borra_la_sesion(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "u1"
        sess["username"] = "nico"

    r = client.get("/montor/logout")

    assert r.status_code == 302
    with client.session_transaction() as sess:
        assert "user_id" not in sess
