"""Resumen mensual generado con la API de Gemini. Los tests nunca llaman a la
API real: se reemplaza genai.Client por un fake que devuelve texto fijo."""
from types import SimpleNamespace

import finanzas_server as app_module


def _fake_client_factory(texto="Este mes gastaste más que el anterior.", calls=None):
    calls = calls if calls is not None else []

    class FakeModels:
        def generate_content(self, model, contents):
            calls.append((model, contents))
            return SimpleNamespace(text=texto)

    class FakeClient:
        def __init__(self, api_key=None):
            self.models = FakeModels()

    return FakeClient


def _loguear(client, fake_db, user_id="u1", pro=True):
    fake_db.tables["usuarios"] = [{
        "id": user_id, "plan": "pro" if pro else "free", "trial_expira": None,
    }]
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "nico"


def _con_transacciones(fake_db):
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 1000, "moneda": "ARS", "categoria": "Comida", "fecha": "2026-01-05"},
        {"tipo": "Ingreso", "monto": 5000, "moneda": "ARS", "categoria": None, "fecha": "2026-01-01"},
    ]


def test_requiere_pro(client, fake_db):
    _loguear(client, fake_db, pro=False)
    r = client.get("/api/finanzas/resumen-ia")
    assert r.status_code == 403
    assert r.get_json()["error"] == "pro_requerido"


def test_sin_api_key_configurada(client, fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    _loguear(client, fake_db)
    r = client.get("/api/finanzas/resumen-ia")
    assert r.status_code == 503
    assert r.get_json()["error"] == "ia_no_configurada"


def test_sin_transacciones_no_llama_a_la_api(client, fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(calls=calls))
    _loguear(client, fake_db)
    fake_db.tables["transacciones"] = []

    r = client.get("/api/finanzas/resumen-ia?mes=1&anio=2026")

    assert r.status_code == 400
    assert r.get_json()["error"] == "sin_datos"
    assert calls == []  # no se gasta la llamada a la API si no hay nada que resumir


def test_genera_resumen_de_un_mes_cerrado(client, fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("Resumen de prueba", calls))
    _loguear(client, fake_db)
    _con_transacciones(fake_db)

    r = client.get("/api/finanzas/resumen-ia?mes=1&anio=2026")

    assert r.status_code == 200
    body = r.get_json()
    assert body == {"ok": True, "resumen": "Resumen de prueba"}
    assert len(calls) == 1
    assert calls[0][0] == "gemini-3.6-flash"


def test_mes_cerrado_se_cachea_no_se_llama_dos_veces(client, fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("Resumen de prueba", calls))
    _loguear(client, fake_db)
    _con_transacciones(fake_db)

    r1 = client.get("/api/finanzas/resumen-ia?mes=1&anio=2026")
    r2 = client.get("/api/finanzas/resumen-ia?mes=1&anio=2026")

    assert r1.get_json() == r2.get_json()
    assert len(calls) == 1  # la segunda vez se sirvió del cache


def test_mes_actual_nunca_se_cachea(client, fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("Resumen de prueba", calls))
    _loguear(client, fake_db)
    hoy = app_module._hoy_ar()
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 1000, "moneda": "ARS", "categoria": "Comida", "fecha": hoy.isoformat()},
    ]

    client.get(f"/api/finanzas/resumen-ia?mes={hoy.month}&anio={hoy.year}")
    client.get(f"/api/finanzas/resumen-ia?mes={hoy.month}&anio={hoy.year}")

    assert len(calls) == 2  # el mes en curso puede cambiar, así que no se cachea


def test_api_caida_devuelve_error_generico(client, fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class FakeModelsQueRompe:
        def generate_content(self, model, contents):
            raise RuntimeError("la API de Gemini está caída")

    class FakeClientQueRompe:
        def __init__(self, api_key=None):
            self.models = FakeModelsQueRompe()

    monkeypatch.setattr(app_module.genai, "Client", FakeClientQueRompe)
    _loguear(client, fake_db)
    _con_transacciones(fake_db)

    r = client.get("/api/finanzas/resumen-ia?mes=1&anio=2026")

    assert r.status_code == 502
    assert r.get_json()["error"] == "ia_no_disponible"
