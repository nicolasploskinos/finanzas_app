"""
Movimientos de ejemplo de la cuenta recién creada.

Lo que se cuida: que el registro no dependa de que los ejemplos se puedan
sembrar, que queden marcados (si no, el usuario no puede distinguirlos de los
suyos ni borrarlos de una), que no le coman el cupo del plan gratis, y sobre
todo que borrarlos no pueda llevarse por delante un movimiento real.
"""
import montor_server as app_module
import routes_auth


def _insertados(fake_db, tabla="transacciones"):
    return [q._written for (nombre, q) in fake_db.queries if nombre == tabla and q._written]


def test_la_cuenta_nueva_arranca_con_ejemplos(client, fake_db):
    fake_db.tables["usuarios"] = []

    r = client.post("/api/montor/register", json={"username": "nuevo", "password": "unaclave123"})

    assert r.status_code == 201
    filas = _insertados(fake_db)[-1]
    assert len(filas) == 3
    assert all(f["es_ejemplo"] is True for f in filas)
    # El gasto en dólares es el que muestra el diferencial del producto.
    assert {f["moneda"] for f in filas} == {"ARS", "USD"}


def test_los_ejemplos_avisan_que_son_de_prueba(client, fake_db):
    fake_db.tables["usuarios"] = []

    client.post("/api/montor/register", json={"username": "nuevo", "password": "unaclave123"})

    for f in _insertados(fake_db)[-1]:
        assert "ejemplo" in f["descripcion"].lower()


def test_si_falla_sembrar_los_ejemplos_el_registro_igual_funciona(client, fake_db, monkeypatch):
    """Nadie pierde una cuenta nueva porque no se pudo poner un dato de
    demostración."""
    fake_db.tables["usuarios"] = []
    llamadas = {"n": 0}
    original = fake_db.table

    def falla_en_la_segunda(nombre):
        llamadas["n"] += 1
        if nombre == "transacciones":
            raise RuntimeError("Supabase caído")
        return original(nombre)

    monkeypatch.setattr(fake_db, "table", falla_en_la_segunda)

    r = client.post("/api/montor/register", json={"username": "nuevo", "password": "unaclave123"})

    assert r.status_code == 201


def test_borrar_ejemplos_solo_toca_los_ejemplos_de_esa_cuenta(client, fake_db):
    """El filtro es lo único que separa 'limpiar la demo' de 'borrarle los
    datos al usuario'."""
    with client.session_transaction() as s:
        s["user_id"] = "u1"
        s["username"] = "nico"

    r = client.delete("/api/montor/ejemplos")

    assert r.status_code == 200
    _, query = [q for q in fake_db.queries if q[0] == "transacciones"][-1]
    hechas = [(nombre, args) for (nombre, args, _kw) in query.calls]
    assert ("delete", ()) in hechas
    assert ("eq", ("user_id", "u1")) in hechas
    assert ("eq", ("es_ejemplo", True)) in hechas


def test_los_ejemplos_no_consumen_el_cupo_del_plan_gratis(fake_db, monkeypatch):
    """Son movimientos que pusimos nosotros: contarlos contra los 50 del plan
    gratis sería cobrarle al usuario nuestro propio onboarding."""
    monkeypatch.setattr(app_module, "_es_pro", lambda uid: False)

    app_module._insertar_transaccion("u1", "Gasto", 100, "2026-09-03", categoria="Test")

    conteo = [q for (nombre, q) in fake_db.queries if nombre == "transacciones"][0]
    hechas = [(nombre, args) for (nombre, args, _kw) in conteo.calls]
    assert ("eq", ("es_ejemplo", False)) in hechas
