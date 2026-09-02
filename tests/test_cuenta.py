"""Perfil de usuario: ver estado de cuenta/suscripción, cambiar nombre y
contraseña, y cancelar la suscripción Pro."""
from werkzeug.security import generate_password_hash

import montor_server as app_module


def _loguear(client, fake_db, user_id="u1", **extra):
    fake_db.tables["usuarios"] = [{
        "id": user_id,
        "username": "nico",
        "password_hash": generate_password_hash("clave1234"),
        "plan": "free",
        "trial_expira": None,
        "plan_ciclo": None,
        "mp_preapproval_id": None,
        "mp_proximo_pago": None,
        **extra,
    }]
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "nico"


def test_cuenta_sin_sesion_devuelve_401(client):
    r = client.get("/api/montor/cuenta")
    assert r.status_code == 302  # login_required redirige (mismo criterio que el resto de /api/montor/*)


def test_cuenta_plan_free(client, fake_db):
    _loguear(client, fake_db)
    r = client.get("/api/montor/cuenta")
    data = r.get_json()
    assert data["username"] == "nico"
    assert data["is_pro"] is False
    assert data["suscripcion"] is None


def test_cuenta_pro_con_suscripcion(client, fake_db):
    _loguear(client, fake_db, plan="pro", plan_ciclo="anual",
             mp_preapproval_id="pre-123", mp_proximo_pago="2026-10-01T00:00:00Z")
    r = client.get("/api/montor/cuenta")
    data = r.get_json()
    assert data["is_pro"] is True
    assert data["suscripcion"] == {"ciclo": "anual", "proximo_pago": "2026-10-01T00:00:00Z"}


def test_cambiar_nombre_ok(client, fake_db):
    _loguear(client, fake_db)
    r = client.put("/api/montor/cuenta/nombre", json={"username": "nicolas"})
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "username": "nicolas"}
    with client.session_transaction() as sess:
        assert sess["username"] == "nicolas"


def test_cambiar_nombre_ya_tomado(client, fake_db):
    _loguear(client, fake_db)
    fake_db.tables["usuarios"].append({"id": "otro-user", "username": "existente"})
    r = client.put("/api/montor/cuenta/nombre", json={"username": "existente"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "username_taken"


def test_cambiar_nombre_muy_corto(client, fake_db):
    _loguear(client, fake_db)
    r = client.put("/api/montor/cuenta/nombre", json={"username": "ab"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "too_short"


def test_cambiar_password_ok(client, fake_db):
    _loguear(client, fake_db)
    r = client.put("/api/montor/cuenta/password", json={"actual": "clave1234", "nueva": "otraclave1"})
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}


def test_cambiar_password_actual_incorrecta(client, fake_db):
    _loguear(client, fake_db)
    r = client.put("/api/montor/cuenta/password", json={"actual": "mal", "nueva": "otraclave1"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "wrong_password"


def test_cambiar_password_nueva_muy_debil(client, fake_db):
    _loguear(client, fake_db)
    r = client.put("/api/montor/cuenta/password", json={"actual": "clave1234", "nueva": "corta"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "weak_password"


def test_cancelar_suscripcion(client, fake_db, monkeypatch):
    _loguear(client, fake_db, plan="pro", mp_preapproval_id="pre-123")
    llamadas = []

    def fake_put(url, headers=None, json=None):
        llamadas.append((url, json))
        class R:
            def json(self):
                return {}
        return R()

    monkeypatch.setattr(app_module.req, "put", fake_put)
    r = client.post("/api/montor/cuenta/cancelar-suscripcion")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}
    assert llamadas[0][0] == "https://api.mercadopago.com/preapproval/pre-123"
    assert llamadas[0][1] == {"status": "cancelled"}
