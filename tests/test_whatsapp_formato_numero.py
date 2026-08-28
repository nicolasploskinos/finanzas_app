"""Conversión del número al formato que la API de envío de Meta espera para
Argentina (54+área+15+número), distinto del formato en que llegan los
mensajes entrantes (549+área+número)."""
import montor_server as app_module


def test_convierte_numero_argentino_moderno_a_formato_de_envio():
    assert app_module._wa_a_formato_envio("5491131806622") == "54111531806622"


def test_no_toca_numeros_que_no_matchean_el_patron_argentino():
    # otro país, o algo que ya viene en otro formato: se manda tal cual
    assert app_module._wa_a_formato_envio("14155552671") == "14155552671"
    assert app_module._wa_a_formato_envio("54111531806622") == "54111531806622"


def test_wa_enviar_mensaje_usa_el_numero_convertido(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "12345")

    llamadas = []

    class FakeResp:
        ok = True

    def fake_post(url, headers=None, json=None, timeout=None):
        llamadas.append(json)
        return FakeResp()

    monkeypatch.setattr(app_module.req, "post", fake_post)

    app_module._wa_enviar_mensaje("5491131806622", "hola")

    assert len(llamadas) == 1
    assert llamadas[0]["to"] == "54111531806622"
