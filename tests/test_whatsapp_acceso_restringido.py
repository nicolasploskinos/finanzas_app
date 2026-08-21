"""La app de Meta está en modo desarrollo, así que el bot de WhatsApp solo
puede hablarle a números permitidos a mano. Por ahora eso significa: solo la
cuenta de Nicolás. Nadie más puede generar un código de vinculación, y si
por algún motivo hubiera un vínculo viejo de otra cuenta, se ignora."""
import finanzas_server as app_module


def _loguear(client, fake_db, user_id):
    fake_db.tables["usuarios"] = [{"id": user_id, "username": "quien-sea"}]
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "quien-sea"


def test_otro_usuario_no_puede_generar_codigo(client, fake_db):
    _loguear(client, fake_db, "otro-usuario-cualquiera")

    r = client.post("/api/finanzas/whatsapp/codigo")

    assert r.status_code == 403
    assert r.get_json()["error"] == "whatsapp_no_disponible"


def test_nicolas_si_puede_generar_codigo(client, fake_db, monkeypatch):
    monkeypatch.setenv("WHATSAPP_DISPLAY_NUMBER", "+15551729935")
    _loguear(client, fake_db, app_module._WHATSAPP_USER_ID)

    r = client.post("/api/finanzas/whatsapp/codigo")

    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_procesar_mensaje_ignora_vinculos_de_otras_cuentas(fake_db, monkeypatch):
    # Por si quedó un vínculo viejo en la tabla de otra cuenta que no sea
    # la habilitada: no debe responder nada, ni siquiera el mensaje de
    # "no reconozco este número".
    fake_db.tables["whatsapp_users"] = [{"user_id": "otro-usuario-cualquiera"}]

    enviados = []
    monkeypatch.setattr(app_module, "_wa_enviar_mensaje", lambda tel, txt: enviados.append(txt))

    app_module._procesar_mensaje_whatsapp({"id": "wamid-x", "from": "5491111111111", "text": {"body": "gasté 500"}})

    assert enviados == []
