"""Interpretación de mensajes de WhatsApp con IA (carga de gasto/ingreso en
lenguaje natural, con jerga y frases sueltas) y el chat de preguntas sobre
los datos. Si el mensaje no resulta ser una carga, se lo mandamos a Gemini
junto con los movimientos recientes del usuario para que responda. Nunca
llama a la API real."""
import json
from types import SimpleNamespace

import finanzas_server as app_module


def _fake_client_factory(respuestas, calls=None):
    """respuestas: un string (siempre la misma respuesta) o una lista de
    strings (una por llamada sucesiva, en orden)."""
    calls = calls if calls is not None else []
    cola = list(respuestas) if isinstance(respuestas, list) else None

    class FakeModels:
        def generate_content(self, model, contents, config=None):
            calls.append((model, contents, config))
            return SimpleNamespace(text=cola.pop(0) if cola is not None else respuestas)

    class FakeClient:
        def __init__(self, api_key=None, **kwargs):
            self.models = FakeModels()

    return FakeClient


# ── _wa_interpretar_mensaje_ia ───────────────────────────────────────────────

def test_interpretar_sin_api_key_no_esta_disponible(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert app_module._wa_interpretar_mensaje_ia("gasté 500 en el kiosco") == (False, None)


def test_interpretar_transaccion_en_lenguaje_informal(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({
        "es_transaccion": True, "tipo": "Gasto", "monto": 5000, "moneda": "ARS",
        "categoria": "comida", "descripcion": "asado con amigos",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    disponible, datos = app_module._wa_interpretar_mensaje_ia("me gasté como 5 lucas en un asado con los pibes")

    assert disponible is True
    assert datos == {
        "tipo": "Gasto", "monto": 5000.0, "moneda": "ARS",
        "categoria": "Comida", "descripcion": "asado con amigos",
    }


def test_interpretar_mensaje_que_no_es_transaccion(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"es_transaccion": False})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia("hola como andas") == (True, None)


def test_interpretar_sin_monto_valido_se_trata_como_no_transaccion(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"es_transaccion": True, "monto": 0})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia("no sé cuánto gasté") == (True, None)


def test_interpretar_json_invalido_no_esta_disponible(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("esto no es json"))

    assert app_module._wa_interpretar_mensaje_ia("gasté 500") == (False, None)


def test_interpretar_respeta_descripcion_entre_parentesis(monkeypatch):
    # Convención de siempre (la misma que el parser regex): lo que va entre
    # paréntesis es la descripción tal cual, aunque la IA hubiese propuesto
    # otra cosa.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    respuesta = json.dumps({
        "es_transaccion": True, "tipo": "Gasto", "monto": 500, "moneda": "ARS",
        "categoria": "comida", "descripcion": "una descripcion inventada por la IA",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta, calls))

    disponible, datos = app_module._wa_interpretar_mensaje_ia("gasté 500 en supermercado (compra semanal)")

    assert disponible is True
    assert datos["descripcion"] == "compra semanal"
    assert datos["categoria"] == "Comida"  # la categoría la sigue decidiendo la IA
    # el paréntesis no se le manda a la IA, para que no intente reinterpretarlo
    assert "(compra semanal)" not in calls[0][1]


def test_interpretar_sin_parentesis_usa_la_descripcion_de_la_ia(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({
        "es_transaccion": True, "tipo": "Gasto", "monto": 500, "moneda": "ARS",
        "categoria": "comida", "descripcion": "en el kiosco de la esquina",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    _, datos = app_module._wa_interpretar_mensaje_ia("gasté 500 en el kiosco de la esquina")

    assert datos["descripcion"] == "en el kiosco de la esquina"


# ── _wa_responder_pregunta ───────────────────────────────────────────────────

def test_sin_api_key_no_responde(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    assert app_module._wa_responder_pregunta("u1", "cuánto gasté?") is None


def test_sin_movimientos_responde_sin_llamar_a_la_api(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("no debería usarse", calls))
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
    assert calls[0][0] == "gemini-3.5-flash-lite"
    assert "cuánto gasté en comida" in calls[0][1]
    assert "Comida" in calls[0][1]  # los movimientos van en el prompt


def test_api_caida_devuelve_none(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class FakeModelsQueRompe:
        def generate_content(self, model, contents, config=None):
            raise RuntimeError("caída")

    class FakeClientQueRompe:
        def __init__(self, api_key=None, **kwargs):
            self.models = FakeModelsQueRompe()

    monkeypatch.setattr(app_module.genai, "Client", FakeClientQueRompe)
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    assert app_module._wa_responder_pregunta("u1", "cuánto gasté?") is None


# ── _procesar_mensaje_whatsapp: ruteo mensaje vs. pregunta ──────────────────

def test_mensaje_sin_monto_se_trata_como_pregunta(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuestas = [
        json.dumps({"es_transaccion": False}),  # 1: intento de interpretar como carga
        "Gastaste poco este mes.",              # 2: respuesta del chat
    ]
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuestas))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid1", "from": "5491111111111", "text": {"body": "cuánto gasté este mes?"}})

    assert enviados == ["Gastaste poco este mes."]


def test_mensaje_informal_interpretado_como_transaccion_se_carga_sin_preguntar(fake_db, monkeypatch):
    calls = []
    respuesta = json.dumps({
        "es_transaccion": True, "tipo": "Gasto", "monto": 5000, "moneda": "ARS",
        "categoria": "comida", "descripcion": "",
    })
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta, calls))
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid2", "from": "5491111111111", "text": {"body": "me gasté 5 lucas en un asado"}})

    assert len(calls) == 1  # una sola llamada a Gemini: interpretar. no llega a preguntar.
    assert "registrado" in enviados[0]


def test_sin_api_key_usa_el_parser_regex_como_respaldo(fake_db, monkeypatch):
    # Si Gemini no está disponible, la carga de gastos por WhatsApp no debe
    # dejar de funcionar: cae al parser viejo basado en regex.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid3", "from": "5491111111111", "text": {"body": "gasté 500 en supermercado"}})

    assert "registrado" in enviados[0]


# ── "borrar último" ──────────────────────────────────────────────────────────

def test_cargar_una_transaccion_guarda_su_id_para_poder_borrarla(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)  # usa el parser regex, más directo
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "tx-999"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: None)

    app_module._procesar_mensaje_whatsapp({"id": "wamid4", "from": "5491111111111", "text": {"body": "gasté 500 en supermercado"}})

    assert app_module._wa_ultima_transaccion[app_module._WHATSAPP_USER_ID] == "tx-999"


def test_borrar_ultimo_sin_carga_previa_no_borra_nada(fake_db, monkeypatch):
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid5", "from": "5491111111111", "text": {"body": "borrar ultimo"}})

    assert "no tengo ninguna carga reciente" in enviados[0].lower()
    deletes = [c for (tabla, q) in fake_db.queries if tabla == "transacciones" for c in q.calls if c[0] == "delete"]
    assert deletes == []


def test_borrar_ultimo_borra_la_transaccion_y_confirma(fake_db, monkeypatch):
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"},
    ]
    app_module._wa_ultima_transaccion[app_module._WHATSAPP_USER_ID] = 42

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid6", "from": "5491111111111", "text": {"body": "Borrar Último"}})

    assert "Borrado" in enviados[0]
    assert "500" in enviados[0]
    assert app_module._WHATSAPP_USER_ID not in app_module._wa_ultima_transaccion
    deletes = [c for (tabla, q) in fake_db.queries if tabla == "transacciones" for c in q.calls if c[0] == "delete"]
    assert len(deletes) == 1


def test_borrar_ultimo_dos_veces_seguidas_la_segunda_no_encuentra_nada(fake_db, monkeypatch):
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"}]
    app_module._wa_ultima_transaccion[app_module._WHATSAPP_USER_ID] = 42

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid7", "from": "5491111111111", "text": {"body": "eliminar la ultima"}})
    app_module._procesar_mensaje_whatsapp({"id": "wamid8", "from": "5491111111111", "text": {"body": "eliminar la ultima"}})

    assert "Borrado" in enviados[0]
    assert "no tengo ninguna carga reciente" in enviados[1].lower()
