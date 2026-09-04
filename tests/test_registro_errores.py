"""
Registro de errores (routes_errores).

Lo que se cuida: que anotar un error nunca sea la causa de otro, que el texto
que manda el navegador se trate como dato no confiable (se recorta, no se
confía el user_id), y que un frontend en loop no llene la tabla.
"""
import pytest

import montor_server as app_module
import routes_errores


def _insertados(fake_db):
    """Payloads que se intentaron guardar en la tabla `errores`."""
    return [q._written for (nombre, q) in fake_db.queries if nombre == "errores" and q._written]


@pytest.fixture(autouse=True)
def _reset_tope():
    # El tope por IP vive a nivel de módulo (así persiste entre requests
    # reales), igual que _login_intentos: sin esto un test que lo agota deja
    # a los siguientes sin poder reportar.
    routes_errores._reportes.clear()
    yield
    routes_errores._reportes.clear()


def test_reportar_guarda_lo_que_manda_el_frontend(client, fake_db):
    r = client.post("/api/montor/errores", json={
        "mensaje": "TypeError: x is not a function",
        "stack": "en Dashboard.tsx:42",
        "ruta": "/montor/analisis",
    })

    assert r.status_code == 202
    assert r.get_json()["guardado"] is True
    fila = _insertados(fake_db)[-1]
    assert fila["origen"] == "frontend"
    assert fila["mensaje"] == "TypeError: x is not a function"
    assert fila["ruta"] == "/montor/analisis"


def test_no_se_le_puede_atribuir_el_error_a_otra_cuenta(client, fake_db):
    """El user_id sale de la sesión, nunca del cuerpo del pedido."""
    client.post("/api/montor/errores", json={
        "mensaje": "algo se rompió",
        "user_id": "00000000-0000-0000-0000-000000000001",
    })

    assert _insertados(fake_db)[-1]["user_id"] is None


def test_los_textos_largos_se_recortan(client, fake_db):
    client.post("/api/montor/errores", json={
        "mensaje": "x" * 50_000,
        "stack": "y" * 90_000,
    })

    fila = _insertados(fake_db)[-1]
    assert len(fila["mensaje"]) == routes_errores._MAX_MENSAJE
    assert len(fila["stack"]) == routes_errores._MAX_STACK


def test_un_mensaje_vacio_no_genera_fila(client, fake_db):
    r = client.post("/api/montor/errores", json={"mensaje": "   "})

    assert r.status_code == 202
    assert r.get_json()["guardado"] is False
    assert _insertados(fake_db) == []


def test_una_pantalla_en_loop_no_llena_la_tabla(client, fake_db):
    for i in range(routes_errores._MAX_REPORTES + 15):
        client.post("/api/montor/errores", json={"mensaje": f"loop {i}"})

    assert len(_insertados(fake_db)) == routes_errores._MAX_REPORTES


def test_si_la_base_falla_el_registro_no_explota(fake_db, monkeypatch):
    """La regla más importante: esto se llama desde un except, así que
    propagar convertiría un error en dos."""
    def explota(*a, **kw):
        raise RuntimeError("Supabase caído")

    monkeypatch.setattr(fake_db, "table", explota)

    assert routes_errores.registrar("backend", "algo") is False  # no relanza


def test_una_excepcion_no_atrapada_del_backend_queda_registrada(fake_db):
    """El 500 le promete al usuario "ya estamos al tanto" — que sea cierto.

    Se invoca el handler directo porque con TESTING=True Flask propaga la
    excepción en vez de pasar por él.
    """
    with app_module.app.test_request_context("/api/montor/algo", method="POST"):
        _, codigo = app_module._error_500(ValueError("boom de prueba"))

    assert codigo == 500
    fila = _insertados(fake_db)[-1]
    assert fila["origen"] == "backend"
    assert "boom de prueba" in fila["mensaje"]
    assert fila["ruta"] == "POST /api/montor/algo"


def test_el_handler_500_responde_aunque_no_se_pueda_registrar(fake_db, monkeypatch):
    """Si la base está caída, el usuario igual tiene que recibir su 500 y no
    una excepción dentro del manejador de excepciones."""
    monkeypatch.setattr(fake_db, "table", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("caído")))

    with app_module.app.test_request_context("/api/montor/algo"):
        cuerpo, codigo = app_module._error_500(ValueError("boom"))

    assert codigo == 500
    assert cuerpo.get_json() == {"ok": False, "error": "server_error"}
