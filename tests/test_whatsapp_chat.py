"""Interpretación de mensajes de WhatsApp con IA: carga de gasto/ingreso en
lenguaje natural (jerga, frases sueltas, español o inglés), pedidos de
borrar lo último dicho de cualquier forma, y el chat de preguntas sobre los
datos. Si el mensaje no resulta ser ninguna de las dos primeras cosas, se lo
mandamos a Gemini junto con los movimientos recientes del usuario para que
responda. Nunca llama a la API real."""
import json
from types import SimpleNamespace

import pytest

import montor_server as app_module


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
    assert app_module._wa_interpretar_mensaje_ia("gasté 500 en el kiosco") == (False, None, "es", None)


def test_interpretar_transaccion_en_lenguaje_informal(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({
        "idioma": "es", "intencion": "carga", "tipo": "Gasto", "monto": 5000, "moneda": "ARS",
        "categoria": "comida", "descripcion": "asado con amigos",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    disponible, accion, idioma, datos = app_module._wa_interpretar_mensaje_ia("me gasté como 5 lucas en un asado con los pibes")

    assert disponible is True
    assert accion == "carga"
    assert idioma == "es"
    assert datos == {
        "tipo": "Gasto", "monto": 5000.0, "moneda": "ARS",
        "categoria": "Comida", "descripcion": "asado con amigos",
    }


def test_interpretar_transaccion_en_ingles(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({
        "idioma": "en", "intencion": "carga", "tipo": "Gasto", "monto": 50, "moneda": "USD",
        "categoria": "food", "descripcion": "groceries",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    disponible, accion, idioma, datos = app_module._wa_interpretar_mensaje_ia("spent 50 bucks on groceries")

    assert disponible is True
    assert accion == "carga"
    assert idioma == "en"
    assert datos["monto"] == 50.0
    assert datos["moneda"] == "USD"


def test_interpretar_mensaje_que_no_es_transaccion_ni_borrado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"idioma": "es", "intencion": "otro"})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia("hola como andas") == (True, None, "es", None)


@pytest.mark.parametrize("frase", [
    "borrá lo último",
    "epa, me equivoqué, borralo",
    "deshacé eso",
    "corregí, sacá lo de recién",
    "no era eso, eliminalo",
])
def test_interpretar_reconoce_pedidos_de_borrar_dichos_de_cualquier_forma(monkeypatch, frase):
    # La gracia de usar IA en vez de una frase fija: entiende la intención
    # aunque cada uno lo pida a su manera, no solo "borrar ultimo" textual.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"idioma": "es", "intencion": "borrar_ultimo"})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia(frase) == (True, "borrar_ultimo", "es", None)


@pytest.mark.parametrize("frase", [
    "undo that",
    "delete the last one",
    "oops, remove it",
])
def test_interpretar_reconoce_pedidos_de_borrar_en_ingles(monkeypatch, frase):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"idioma": "en", "intencion": "borrar_ultimo"})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia(frase) == (True, "borrar_ultimo", "en", None)


def test_interpretar_sin_monto_valido_se_trata_como_no_transaccion(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"idioma": "es", "intencion": "carga", "monto": 0})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia("no sé cuánto gasté") == (True, None, "es", None)


def test_interpretar_json_invalido_no_esta_disponible(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("esto no es json"))

    assert app_module._wa_interpretar_mensaje_ia("gasté 500") == (False, None, "es", None)


def test_interpretar_idioma_invalido_cae_a_espanol(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({"idioma": "fr", "intencion": "otro"})
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    assert app_module._wa_interpretar_mensaje_ia("bonjour") == (True, None, "es", None)


def test_interpretar_respeta_descripcion_entre_parentesis(monkeypatch):
    # Convención de siempre (la misma que el parser regex): lo que va entre
    # paréntesis es la descripción tal cual, aunque la IA hubiese propuesto
    # otra cosa.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    respuesta = json.dumps({
        "idioma": "es", "intencion": "carga", "tipo": "Gasto", "monto": 500, "moneda": "ARS",
        "categoria": "comida", "descripcion": "una descripcion inventada por la IA",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta, calls))

    disponible, accion, idioma, datos = app_module._wa_interpretar_mensaje_ia("gasté 500 en supermercado (compra semanal)")

    assert disponible is True
    assert accion == "carga"
    assert datos["descripcion"] == "compra semanal"
    assert datos["categoria"] == "Comida"  # la categoría la sigue decidiendo la IA
    # el paréntesis no se le manda a la IA, para que no intente reinterpretarlo
    assert "(compra semanal)" not in calls[0][1]


def test_interpretar_sin_parentesis_usa_la_descripcion_de_la_ia(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuesta = json.dumps({
        "idioma": "es", "intencion": "carga", "tipo": "Gasto", "monto": 500, "moneda": "ARS",
        "categoria": "comida", "descripcion": "en el kiosco de la esquina",
    })
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))

    _, _, _, datos = app_module._wa_interpretar_mensaje_ia("gasté 500 en el kiosco de la esquina")

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


def test_prompt_de_pregunta_pide_responder_en_el_idioma_de_la_pregunta(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = []
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory("You spent 100 on food.", calls))
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"},
    ]

    r = app_module._wa_responder_pregunta("u1", "how much did I spend on food?")

    assert r == "You spent 100 on food."
    assert "how much did I spend on food?" in calls[0][1]
    assert "mismo idioma" in calls[0][1]  # la instrucción de espejar el idioma va en el prompt


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


# ── _procesar_mensaje_whatsapp: ruteo carga vs. borrar vs. pregunta ─────────

def test_mensaje_sin_monto_se_trata_como_pregunta(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    respuestas = [
        json.dumps({"idioma": "es", "intencion": "otro"}),  # 1: intento de interpretar como carga/borrado
        "Gastaste poco este mes.",                          # 2: respuesta del chat
    ]
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuestas))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 100, "moneda": "ARS", "categoria": "Comida", "descripcion": "", "fecha": "2026-08-01"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid1", "from": "5491111111111", "text": {"body": "cuánto gasté este mes?"}})

    assert enviados == ["Gastaste poco este mes."]


def test_mensaje_informal_interpretado_como_transaccion_se_carga_sin_preguntar(fake_db, monkeypatch):
    calls = []
    respuesta = json.dumps({
        "idioma": "es", "intencion": "carga", "tipo": "Gasto", "monto": 5000, "moneda": "ARS",
        "categoria": "comida", "descripcion": "",
    })
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta, calls))
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid2", "from": "5491111111111", "text": {"body": "me gasté 5 lucas en un asado"}})

    assert len(calls) == 1  # una sola llamada a Gemini: interpretar. no llega a preguntar.
    assert "Anoté" in enviados[0]


def test_mensaje_en_ingles_se_carga_y_confirma_en_ingles(fake_db, monkeypatch):
    respuesta = json.dumps({
        "idioma": "en", "intencion": "carga", "tipo": "Gasto", "monto": 50, "moneda": "USD",
        "categoria": "food", "descripcion": "",
    })
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(respuesta))
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid-en", "from": "5491111111111", "text": {"body": "spent 50 bucks on groceries"}})

    assert "Logged your expense" in enviados[0]
    assert "Anoté" not in enviados[0]


def test_sin_api_key_usa_el_parser_regex_como_respaldo(fake_db, monkeypatch):
    # Si Gemini no está disponible, la carga de gastos por WhatsApp no debe
    # dejar de funcionar: cae al parser viejo basado en regex.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid3", "from": "5491111111111", "text": {"body": "gasté 500 en supermercado"}})

    assert "Anoté" in enviados[0]


# ── respaldo sin IA: también entiende inglés (regex + detección de idioma) ──

@pytest.mark.parametrize("frase,tipo_esperado,moneda_esperada", [
    ("spent 500 on groceries", "Gasto", "ARS"),
    ("paid 50 bucks for the gym", "Gasto", "USD"),
    ("received 1200 income", "Ingreso", "ARS"),
])
def test_parser_regex_entiende_ingles(frase, tipo_esperado, moneda_esperada):
    r = app_module._parse_mensaje_whatsapp(frase)
    assert r is not None
    assert r["tipo"] == tipo_esperado
    assert r["moneda"] == moneda_esperada


@pytest.mark.parametrize("frase,idioma_esperado", [
    ("spent 500 on groceries", "en"),
    ("gasté 500 en el kiosco", "es"),
    ("undo that", "en"),
    ("borrar ultimo", "es"),
    ("delete the last one", "en"),
])
def test_deteccion_de_idioma_por_regex(frase, idioma_esperado):
    assert app_module._wa_detectar_idioma_regex(frase) == idioma_esperado


def test_carga_en_ingles_sin_ia_confirma_en_ingles(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid-en-regex", "from": "5491111111111", "text": {"body": "spent 500 on groceries"}})

    assert "Logged your expense" in enviados[0]
    assert "Anoté" not in enviados[0]


def test_borrar_ultimo_en_ingles_sin_ia_confirma_en_ingles(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": 42}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid-en-del-regex", "from": "5491111111111", "text": {"body": "delete the last one"}})

    assert "Done, deleted" in enviados[0]


# ── "borrar último" ───────────────────────────────────────────────────────────
# El id de la última transacción cargada por WhatsApp vive en la columna
# whatsapp_users.ultima_transaccion_id (persistido en la base, no en memoria,
# para que sobreviva a un reinicio del servidor).

@pytest.mark.parametrize("frase", [
    "borrar ultimo",
    "borrar último",
    "borrar ultimo gasto",
    "borrar ultimo ingreso",
    "borrar la ultima",
    "eliminar la ultima",
    "eliminar ultimo gasto",
    "ELIMINAR ULTIMO INGRESO",
])
def test_variantes_fijas_de_borrar_ultimo_sin_ia_se_interpretan_igual(fake_db, monkeypatch, frase):
    # Sin GEMINI_API_KEY: usa la regla de respaldo (regex), más rígida.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": 42}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": f"wamid-{frase}", "from": "5491111111111", "text": {"body": frase}})

    assert "borré" in enviados[0].lower()


@pytest.mark.parametrize("frase", [
    "borrá lo último que cargué",
    "epa me equivoqué, sacalo",
    "no, borrá eso",
    "deshacé el último gasto",
])
def test_borrar_ultimo_con_ia_entiende_cualquier_forma_de_pedirlo(fake_db, monkeypatch, frase):
    # Con IA disponible, no hace falta decir "borrar ultimo" textual.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(json.dumps({"idioma": "es", "intencion": "borrar_ultimo"})))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": 42}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": f"wamid-ia-{frase}", "from": "5491111111111", "text": {"body": frase}})

    assert "borré" in enviados[0].lower()


def test_borrar_ultimo_en_ingles_confirma_en_ingles(fake_db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_client_factory(json.dumps({"idioma": "en", "intencion": "borrar_ultimo"})))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": 42}]
    fake_db.tables["transacciones"] = [{"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid-en-del", "from": "5491111111111", "text": {"body": "undo that"}})

    assert "Done, deleted" in enviados[0]
    assert "Listo" not in enviados[0]


def test_cargar_una_transaccion_guarda_su_id_en_la_base_para_poder_borrarla(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)  # usa el parser regex, más directo
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "tx-999"}))
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: None)

    app_module._procesar_mensaje_whatsapp({"id": "wamid4", "from": "5491111111111", "text": {"body": "gasté 500 en supermercado"}})

    updates = [
        call for (tabla, q) in fake_db.queries if tabla == "whatsapp_users"
        for call in q.calls if call[0] == "update"
    ]
    assert len(updates) == 1
    assert updates[0][1][0] == {"ultima_transaccion_id": "tx-999"}


def test_borrar_ultimo_sin_carga_previa_no_borra_nada(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid5", "from": "5491111111111", "text": {"body": "borrar ultimo"}})

    assert "no tengo ninguna carga reciente" in enviados[0].lower()
    deletes = [c for (tabla, q) in fake_db.queries if tabla == "transacciones" for c in q.calls if c[0] == "delete"]
    assert deletes == []


def test_borrar_ultimo_borra_la_transaccion_y_limpia_el_puntero_en_la_base(fake_db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": 42}]
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 500, "moneda": "ARS", "categoria": "Comida"},
    ]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid6", "from": "5491111111111", "text": {"body": "Borrar Último"}})

    assert "borré" in enviados[0].lower()
    assert "500" in enviados[0]

    deletes = [c for (tabla, q) in fake_db.queries if tabla == "transacciones" for c in q.calls if c[0] == "delete"]
    assert len(deletes) == 1

    updates = [
        call for (tabla, q) in fake_db.queries if tabla == "whatsapp_users"
        for call in q.calls if call[0] == "update"
    ]
    assert len(updates) == 1
    assert updates[0][1][0] == {"ultima_transaccion_id": None}
