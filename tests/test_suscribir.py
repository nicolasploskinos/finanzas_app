"""El endpoint de suscripción arma la preaprobación de MercadoPago con el
monto y la frecuencia que corresponda según el ciclo elegido (mensual o
anual). Nunca llama a la API real de MercadoPago."""
import finanzas_server as app_module


def _loguear(client, fake_db, user_id="u1"):
    fake_db.tables["usuarios"] = [{"id": user_id, "username": "nico"}]
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "nico"


def _mock_mp_post(monkeypatch):
    llamadas = []

    class FakeResp:
        def json(self):
            return {"init_point": "https://mercadopago.com/checkout/fake"}

    def fake_post(url, headers=None, json=None):
        llamadas.append(json)
        return FakeResp()

    monkeypatch.setattr(app_module.req, "post", fake_post)
    return llamadas


def test_ciclo_mensual_por_defecto(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    llamadas = _mock_mp_post(monkeypatch)

    r = client.get("/api/finanzas/suscribir")

    assert r.status_code == 302
    assert llamadas[0]["auto_recurring"] == {
        "frequency": 1, "frequency_type": "months", "transaction_amount": 6000, "currency_id": "ARS",
    }


def test_ciclo_anual(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    llamadas = _mock_mp_post(monkeypatch)

    r = client.get("/api/finanzas/suscribir?ciclo=anual")

    assert r.status_code == 302
    assert llamadas[0]["auto_recurring"] == {
        "frequency": 12, "frequency_type": "months", "transaction_amount": 60000, "currency_id": "ARS",
    }


def test_ciclo_invalido_cae_a_mensual(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    llamadas = _mock_mp_post(monkeypatch)

    client.get("/api/finanzas/suscribir?ciclo=lo-que-sea")

    assert llamadas[0]["auto_recurring"]["transaction_amount"] == 6000
