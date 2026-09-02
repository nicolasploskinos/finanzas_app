"""
/api/montor/me es de donde el frontend en React saca el usuario y el plan.
A diferencia del resto de las rutas con sesión, cuando no hay sesión tiene
que contestar 401 con JSON y no un 302 al login: quien llama es un fetch.
"""
from datetime import datetime, timedelta, timezone

import montor_server as app_module


def _con_sesion(client, user_id="u1", username="nico"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username


def test_sin_sesion_devuelve_401_json(client):
    r = client.get("/api/montor/me")
    assert r.status_code == 401
    assert r.get_json()["error"]


def test_usuario_pro(client, fake_db):
    fake_db.tables["usuarios"] = [{"id": "u1", "plan": "pro", "trial_expira": None}]
    _con_sesion(client)

    datos = client.get("/api/montor/me").get_json()

    assert datos["username"] == "nico"
    assert datos["is_pro"] is True
    assert datos["is_trial"] is False
    assert datos["trial_dias"] == 0


def test_usuario_free(client, fake_db):
    fake_db.tables["usuarios"] = [{"id": "u1", "plan": "free", "trial_expira": None}]
    _con_sesion(client)

    datos = client.get("/api/montor/me").get_json()

    assert datos["is_pro"] is False
    assert datos["is_trial"] is False


def test_trial_vigente_cuenta_como_pro(client, fake_db):
    expira = datetime.now(timezone.utc) + timedelta(days=3)
    fake_db.tables["usuarios"] = [
        {"id": "u1", "plan": "trial", "trial_expira": expira.isoformat()}
    ]
    _con_sesion(client)

    datos = client.get("/api/montor/me").get_json()

    assert datos["is_pro"] is True
    assert datos["is_trial"] is True
    assert datos["trial_dias"] >= 1


def test_trial_vencido_no_es_pro(client, fake_db):
    expira = datetime.now(timezone.utc) - timedelta(days=1)
    fake_db.tables["usuarios"] = [
        {"id": "u1", "plan": "trial", "trial_expira": expira.isoformat()}
    ]
    _con_sesion(client)

    datos = client.get("/api/montor/me").get_json()

    assert datos["is_pro"] is False
    assert datos["is_trial"] is False


def test_whatsapp_solo_para_el_usuario_habilitado(client, fake_db):
    fake_db.tables["usuarios"] = [
        {"id": app_module._WHATSAPP_USER_ID, "plan": "pro", "trial_expira": None}
    ]
    _con_sesion(client, user_id=app_module._WHATSAPP_USER_ID)

    assert client.get("/api/montor/me").get_json()["whatsapp_habilitado"] is True
