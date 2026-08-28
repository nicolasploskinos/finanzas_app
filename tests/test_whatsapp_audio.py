"""Notas de voz por WhatsApp: se descargan de la API de Meta (dos pasos: pedir
la URL temporal, después descargar el archivo) y se transcriben con Gemini
antes de pasar por el mismo pipeline que un mensaje de texto normal."""
from types import SimpleNamespace

import montor_server as app_module


def _fake_genai_client(texto):
    class FakeModels:
        def generate_content(self, model, contents):
            return SimpleNamespace(text=texto)

    class FakeClient:
        def __init__(self, api_key=None, **kwargs):
            self.models = FakeModels()

    return FakeClient


# ── _wa_descargar_media ──────────────────────────────────────────────────────

def test_descargar_media_sin_token_no_intenta_nada(monkeypatch):
    monkeypatch.delenv("WHATSAPP_TOKEN", raising=False)
    llamadas = []
    monkeypatch.setattr(app_module.req, "get", lambda *a, **kw: llamadas.append(1))

    assert app_module._wa_descargar_media("media-1") == (None, None)
    assert llamadas == []


def test_descargar_media_sin_id_no_intenta_nada(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")
    llamadas = []
    monkeypatch.setattr(app_module.req, "get", lambda *a, **kw: llamadas.append(1))

    assert app_module._wa_descargar_media(None) == (None, None)
    assert llamadas == []


def test_descargar_media_exitoso(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")

    class FakeMetaResp:
        def json(self):
            return {"url": "https://ejemplo.com/audio.ogg", "mime_type": "audio/ogg; codecs=opus"}

    class FakeArchivoResp:
        ok = True
        content = b"bytes-del-audio"

    respuestas = {"https://graph.facebook.com/v20.0/media-1": FakeMetaResp(),
                  "https://ejemplo.com/audio.ogg": FakeArchivoResp()}

    def fake_get(url, headers=None, timeout=None):
        return respuestas[url]

    monkeypatch.setattr(app_module.req, "get", fake_get)

    data, mime = app_module._wa_descargar_media("media-1")

    assert data == b"bytes-del-audio"
    assert mime == "audio/ogg; codecs=opus"


def test_descargar_media_sin_url_devuelve_none(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")

    class FakeMetaResp:
        def json(self):
            return {}

    monkeypatch.setattr(app_module.req, "get", lambda *a, **kw: FakeMetaResp())

    assert app_module._wa_descargar_media("media-1") == (None, None)


def test_descargar_media_descarga_fallida_devuelve_none(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")

    class FakeMetaResp:
        def json(self):
            return {"url": "https://ejemplo.com/audio.ogg", "mime_type": "audio/ogg"}

    class FakeArchivoResp:
        ok = False
        content = b""

    respuestas = {"https://graph.facebook.com/v20.0/media-1": FakeMetaResp(),
                  "https://ejemplo.com/audio.ogg": FakeArchivoResp()}
    monkeypatch.setattr(app_module.req, "get", lambda url, headers=None, timeout=None: respuestas[url])

    assert app_module._wa_descargar_media("media-1") == (None, None)


def test_descargar_media_excepcion_devuelve_none(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")

    def fake_get(*a, **kw):
        raise RuntimeError("timeout")

    monkeypatch.setattr(app_module.req, "get", fake_get)

    assert app_module._wa_descargar_media("media-1") == (None, None)


# ── _wa_transcribir_audio ─────────────────────────────────────────────────────

def test_transcribir_sin_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert app_module._wa_transcribir_audio(b"audio", "audio/ogg") is None


def test_transcribir_exitoso(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(app_module.genai, "Client", _fake_genai_client("gasté quinientos en el kiosco"))

    assert app_module._wa_transcribir_audio(b"audio", "audio/ogg") == "gasté quinientos en el kiosco"


def test_transcribir_api_caida_devuelve_none(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class FakeModelsQueRompe:
        def generate_content(self, model, contents):
            raise RuntimeError("caída")

    class FakeClientQueRompe:
        def __init__(self, api_key=None, **kwargs):
            self.models = FakeModelsQueRompe()

    monkeypatch.setattr(app_module.genai, "Client", FakeClientQueRompe)

    assert app_module._wa_transcribir_audio(b"audio", "audio/ogg") is None


# ── _procesar_mensaje_whatsapp con mensajes de audio ─────────────────────────

def test_audio_transcripto_se_procesa_como_texto_normal(fake_db, monkeypatch):
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]
    monkeypatch.setattr(app_module, "_wa_descargar_media", lambda media_id: (b"bytes", "audio/ogg"))
    monkeypatch.setattr(app_module, "_wa_transcribir_audio", lambda data, mime: "gasté 500 en el kiosco")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)  # el mensaje transcripto usa el parser regex, más directo
    monkeypatch.setattr(app_module, "_insertar_transaccion", lambda *a, **kw: (True, {"id": "t1"}))

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({
        "id": "wamid-audio-1", "from": "5491111111111", "type": "audio",
        "audio": {"id": "media-1"},
    })

    assert "Anoté" in enviados[0]


def test_audio_que_no_se_puede_transcribir_avisa_en_vez_de_fallar(fake_db, monkeypatch):
    fake_db.tables["whatsapp_users"] = [{"user_id": app_module._WHATSAPP_USER_ID, "ultima_transaccion_id": None}]
    monkeypatch.setattr(app_module, "_wa_descargar_media", lambda media_id: (None, None))

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({
        "id": "wamid-audio-2", "from": "5491111111111", "type": "audio",
        "audio": {"id": "media-2"},
    })

    assert "no llegué a entender" in enviados[0].lower()
