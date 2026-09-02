"""El endpoint de suscripción arma la preaprobación de MercadoPago con el
monto y la frecuencia que corresponda según el ciclo elegido (mensual o
anual). Nunca llama a la API real de MercadoPago."""
import montor_server as app_module


def _loguear(client, fake_db, user_id="u1"):
    fake_db.tables["usuarios"] = [{"id": user_id, "username": "nico"}]
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "nico"


def _mock_mp_post(monkeypatch, preapproval_id=None):
    llamadas = []

    class FakeResp:
        def json(self):
            data = {"init_point": "https://mercadopago.com/checkout/fake"}
            if preapproval_id:
                data["id"] = preapproval_id
            return data

    def fake_post(url, headers=None, json=None):
        llamadas.append(json)
        return FakeResp()

    monkeypatch.setattr(app_module.req, "post", fake_post)
    return llamadas


def _mock_mp_put(monkeypatch):
    llamadas = []

    class FakeResp:
        def json(self):
            return {}

    def fake_put(url, headers=None, json=None):
        llamadas.append((url, json))
        return FakeResp()

    monkeypatch.setattr(app_module.req, "put", fake_put)
    return llamadas


def test_ciclo_mensual_por_defecto(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    llamadas = _mock_mp_post(monkeypatch)

    r = client.get("/api/montor/suscribir")

    assert r.status_code == 302
    assert llamadas[0]["auto_recurring"] == {
        "frequency": 1, "frequency_type": "months", "transaction_amount": 6000, "currency_id": "ARS",
    }


def test_ciclo_anual(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    llamadas = _mock_mp_post(monkeypatch)

    r = client.get("/api/montor/suscribir?ciclo=anual")

    assert r.status_code == 302
    assert llamadas[0]["auto_recurring"] == {
        "frequency": 12, "frequency_type": "months", "transaction_amount": 60000, "currency_id": "ARS",
    }


def test_ciclo_invalido_cae_a_mensual(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    llamadas = _mock_mp_post(monkeypatch)

    client.get("/api/montor/suscribir?ciclo=lo-que-sea")

    assert llamadas[0]["auto_recurring"]["transaction_amount"] == 6000


def test_guarda_preapproval_id_y_ciclo(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    _mock_mp_post(monkeypatch, preapproval_id="pre-nuevo")

    client.get("/api/montor/suscribir?ciclo=anual")

    updates = [
        call[1][0] for (tabla, q) in fake_db.queries if tabla == "usuarios"
        for call in q.calls if call[0] == "update"
    ]
    assert {"mp_preapproval_id": "pre-nuevo", "plan_ciclo": "anual"} in updates


def test_cancela_preapproval_previa_antes_de_crear_una_nueva(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    fake_db.tables["usuarios"][0]["mp_preapproval_id"] = "pre-viejo"
    _mock_mp_post(monkeypatch, preapproval_id="pre-nuevo")
    llamadas_put = _mock_mp_put(monkeypatch)

    client.get("/api/montor/suscribir")

    assert llamadas_put[0] == ("https://api.mercadopago.com/preapproval/pre-viejo", {"status": "cancelled"})


def test_no_intenta_cancelar_si_no_tenia_preapproval(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    _mock_mp_post(monkeypatch)
    llamadas_put = _mock_mp_put(monkeypatch)

    client.get("/api/montor/suscribir")

    assert llamadas_put == []
