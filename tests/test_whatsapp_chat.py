"""Chat de WhatsApp: si el mensaje no se puede parsear como carga de gasto/
ingreso, se lo mandamos a Gemini junto con los movimientos recientes del
usuario para que responda la pregunta. Nunca llama a la API real."""
from types import SimpleNamespace

import finanzas_server as app_module


def _fake_client_factory(texto="Este mes gastaste más en comida.", calls=None):
    calls = calls if calls is not None else []

    class FakeModels:
        def generate_content(self, model, contents):
            calls.append((model, contents))
            return SimpleNamespace(text=texto)

    class FakeClient:
        def __init__(self, api_key=None):
            self.models = FakeModels()

    return FakeClient


# ── _wa_responder_pregunta ───────────────────────────────────────────────────

def test_sin_api_key_no_responde(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    assert app_module._wa_responder_pregunta("u1", "cuánto gasté?") is None


def test_sin_movimientos_responde_sin_llamar_a_la_api(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(calls=calls))
    fake_db.tables["transacciones"] = []

    r = app_module._wa_responder_pregunta("u1", "cuánto gasté?")

    assert r is not None
    assert calls == []


def test_con_movimientos_llama_a_gemini_y_devuelve_el_texto(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("Gastaste 100 en comida.", calls))
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"},
    ]

    r = app_module._wa_responder_pregunta("u1", "¿cuánto gasté en comida?")

    assert r == "Gastaste 100 en comida."
    assert len(calls) == 1
    assert calls[0][0] == "gemini-3.6-flash"
    assert "cuánto gasté en comida" in calls[0][1]
    assert "Comida" in calls[0][1]  # los movimientos van en el prompt


def test_api_caida_devuelve_none(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class FakeModelsQueRompe:
        def generate_content(self, model, contents):
            raise RuntimeError("caída")

    class FakeClientQueRompe:
        def __init__(self, api_key=None):
            self.models = FakeModelsQueRompe()

    monkeypatch.setattr(app_module.genai, "Client", FakeClientQueRompe)
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    assert app_module._wa_responder_pregunta("u1", "cuánto gasté?") is None


# ── _procesar_mensaje_whatsapp: ruteo mensaje vs. pregunta ──────────────────

def test_mensaje_sin_monto_se_trata_como_pregunta(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("Gastaste poco este mes."))
    fake_db.tables["whatsapp_users"] = [{"user_id": "u1"}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid1", "from": "5491111111111", "text": {"body": "cuánto gasté este mes?"}})

    assert enviados == ["Gastaste poco este mes."]


def test_mensaje_con_monto_sigue_cargando_transaccion_no_pregunta(fake_db, monkeypatch):
    # Regresión: un mensaje que sí matchea el parser de carga no debe pasar
    # nunca por el chat de IA, para no gastar una llamada de más ni confundir
    # una carga real con una pregunta.
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(calls=calls))
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": "u1"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid2", "from": "5491111111111", "text": {"body": "gasté 500 en supermercado"}})

    assert calls == []
    assert "registrado" in enviados[0]
