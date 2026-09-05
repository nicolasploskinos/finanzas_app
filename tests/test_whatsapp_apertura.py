"""
El interruptor que abre el bot de WhatsApp a todos los usuarios.

Importa que esto no se abra por accidente: mientras la app de Meta no tenga
Business Verification, el bot solo puede responderle a los números cargados a
mano en la lista de prueba. Si se abriera antes, cualquiera podría hacer todo
el flujo de vinculación y después no recibir respuesta — peor experiencia que
no tener la función.
"""
import montor_server as core

ADMIN = core._WHATSAPP_USER_ID
OTRO = "00000000-0000-0000-0000-000000000001"


def test_cerrado_por_defecto(monkeypatch):
    """Sin la variable puesta, solo el admin. Este es el estado de hoy."""
    monkeypatch.delenv("WHATSAPP_ABIERTO", raising=False)

    assert core._whatsapp_disponible_para(ADMIN) is True
    assert core._whatsapp_disponible_para(OTRO) is False


def test_abierto_habilita_a_cualquiera(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ABIERTO", "1")

    assert core._whatsapp_disponible_para(OTRO) is True


def test_valores_negativos_no_lo_abren(monkeypatch):
    """Una variable puesta en '0' o vacía tiene que dejarlo cerrado: es fácil
    escribirla mal y el modo inseguro no puede ser el accidental."""
    for valor in ("0", "false", "no", "", "  "):
        monkeypatch.setenv("WHATSAPP_ABIERTO", valor)
        assert core._whatsapp_disponible_para(OTRO) is False, valor


def test_el_admin_entra_igual_este_como_este_el_interruptor(monkeypatch):
    """El admin lo usa siempre: es quien recibe los avisos de error."""
    for valor in ("0", "1"):
        monkeypatch.setenv("WHATSAPP_ABIERTO", valor)
        assert core._whatsapp_disponible_para(ADMIN) is True
