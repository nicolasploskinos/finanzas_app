"""
Ingreso con Google.

Es un camino de autenticación, así que lo que se cuida es sobre todo lo que
puede salir mal: que sin configurar no quede una puerta a medio abrir, que el
state (anti-CSRF) se valide de verdad, que no se pueda entrar con un email
que Google no verificó, y que vincular por email no le entregue la cuenta de
alguien a un tercero por accidente.
"""
import base64
import json

import pytest

import montor_server as app_module
import routes_google


def _id_token(payload):
    """Arma un JWT con el payload pedido (firma de mentira: el código no la
    verifica a propósito — ver el encabezado de routes_google)."""
    cuerpo = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"encabezado.{cuerpo}.firma"


class _RespuestaToken:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return {"id_token": _id_token(self._payload)}


@pytest.fixture
def google_configurado(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id-de-prueba")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secreto-de-prueba")


@pytest.fixture
def google_responde(monkeypatch):
    """Reemplaza el POST al endpoint de token de Google."""
    def _configurar(payload):
        monkeypatch.setattr(app_module.req, "post", lambda *a, **kw: _RespuestaToken(payload))
    return _configurar


def test_sin_configurar_no_expone_el_ingreso(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

    assert client.get("/api/montor/auth/config").get_json() == {"google": False}

    r = client.get("/api/montor/auth/google")
    assert r.status_code == 302
    assert "google_no_configurado" in r.headers["Location"]


def test_configurado_manda_a_google_con_state(client, google_configurado):
    assert client.get("/api/montor/auth/config").get_json() == {"google": True}

    r = client.get("/api/montor/auth/google")

    assert r.status_code == 302
    destino = r.headers["Location"]
    assert destino.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "state=" in destino and "scope=openid+email+profile" in destino
    with client.session_transaction() as s:
        assert s["google_state"]  # quedó guardado para comparar a la vuelta


def test_el_callback_rechaza_un_state_que_no_coincide(client, google_configurado, fake_db):
    """Sin esto, un tercero podría inducir el callback con su propio código y
    dejar al visitante logueado en una cuenta ajena."""
    with client.session_transaction() as s:
        s["google_state"] = "el-bueno"

    r = client.get("/api/montor/auth/google/callback?code=x&state=el-malo")

    assert r.status_code == 302
    assert "google_state" in r.headers["Location"]
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_el_callback_rechaza_un_state_ausente(client, google_configurado):
    r = client.get("/api/montor/auth/google/callback?code=x&state=inventado")

    assert "google_state" in r.headers["Location"]


def test_no_entra_con_un_email_sin_verificar(client, google_configurado, google_responde, fake_db):
    """Sin email_verified, cualquiera con una cuenta de Google propia podría
    reclamar el email de otra persona."""
    google_responde({"email": "ajeno@gmail.com", "sub": "123", "email_verified": False})
    with client.session_transaction() as s:
        s["google_state"] = "ok"

    r = client.get("/api/montor/auth/google/callback?code=x&state=ok")

    assert "google_email" in r.headers["Location"]
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_si_ya_entro_antes_lo_reconoce_por_google_id(client, google_configurado, google_responde, fake_db):
    fake_db.tables["usuarios"] = [{"id": "u1", "username": "nico", "google_id": "sub-123"}]
    google_responde({"email": "nico@gmail.com", "sub": "sub-123", "email_verified": True})
    with client.session_transaction() as s:
        s["google_state"] = "ok"

    r = client.get("/api/montor/auth/google/callback?code=x&state=ok")

    assert r.headers["Location"].endswith("/montor")
    with client.session_transaction() as s:
        assert s["user_id"] == "u1"


def test_el_state_no_se_puede_reusar(client, google_configurado, google_responde, fake_db):
    """Se consume al usarlo (pop), así que un callback repetido no sirve."""
    fake_db.tables["usuarios"] = [{"id": "u1", "username": "nico", "google_id": "sub-123"}]
    google_responde({"email": "nico@gmail.com", "sub": "sub-123", "email_verified": True})
    with client.session_transaction() as s:
        s["google_state"] = "ok"

    client.get("/api/montor/auth/google/callback?code=x&state=ok")
    r2 = client.get("/api/montor/auth/google/callback?code=x&state=ok")

    assert "google_state" in r2.headers["Location"]


def test_cancelar_en_google_vuelve_al_login_sin_error(client, google_configurado, fake_db):
    """Cancelar es una decisión, no una falla: no hay por qué mostrar un
    cartel rojo."""
    with client.session_transaction() as s:
        s["google_state"] = "ok"

    r = client.get("/api/montor/auth/google/callback?error=access_denied&state=ok")

    assert r.headers["Location"] == "/montor/login"


def test_si_google_falla_no_se_crea_sesion(client, google_configurado, monkeypatch, fake_db):
    def explota(*a, **kw):
        raise RuntimeError("timeout con Google")

    monkeypatch.setattr(app_module.req, "post", explota)
    with client.session_transaction() as s:
        s["google_state"] = "ok"

    r = client.get("/api/montor/auth/google/callback?code=x&state=ok")

    assert "error=google" in r.headers["Location"]
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_username_derivado_del_email_se_limpia(fake_db):
    fake_db.tables["usuarios"] = []

    assert routes_google._username_libre("Juan.Perez@gmail.com") == "juan.perez"
    assert routes_google._username_libre("maría+etiqueta@gmail.com") == "mariaetiqueta"


def test_username_no_pisa_a_uno_existente(fake_db, monkeypatch):
    """El username es único en la base: chocar rompería el alta."""
    ocupados = {"nico"}
    monkeypatch.setattr(
        routes_google.core.db, "table",
        lambda _n: type("Q", (), {
            "select": lambda self, *a: self,
            "eq": lambda self, campo, valor: setattr(self, "v", valor) or self,
            "execute": lambda self: type("R", (), {"data": [{"id": 1}] if self.v in ocupados else []})(),
        })(),
    )

    assert routes_google._username_libre("nico@gmail.com") == "nico2"
