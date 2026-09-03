"""La lista de transacciones acepta un rango de fechas y un tope, para que el
frontend baje sólo el período que está mirando en vez de todo el historial."""
import montor_server as app_module


def _loguear(client, fake_db, plan="pro"):
    fake_db.tables["usuarios"] = [{"id": "u1", "username": "nico", "plan": plan, "trial_expira": None}]
    fake_db.tables["transacciones"] = []
    fake_db.tables["recurrentes"] = []
    with client.session_transaction() as sess:
        sess["user_id"] = "u1"
        sess["username"] = "nico"


def _filtros(fake_db, tabla="transacciones"):
    """(método, args) de cada llamada encadenada sobre la tabla."""
    return [
        call
        for (nombre, q) in fake_db.queries
        if nombre == tabla
        for call in q.calls
    ]


def test_sin_parametros_no_filtra_por_fecha(client, fake_db):
    _loguear(client, fake_db)
    client.get("/api/montor")
    llamadas = _filtros(fake_db)
    assert not [c for c in llamadas if c[0] in ("gte", "lte") and c[1][0] == "fecha"]


def test_desde_y_hasta_se_aplican(client, fake_db):
    _loguear(client, fake_db)
    client.get("/api/montor?desde=2026-08-01&hasta=2026-08-31")
    llamadas = _filtros(fake_db)
    assert ("gte", ("fecha", "2026-08-01"), {}) in llamadas
    assert ("lte", ("fecha", "2026-08-31"), {}) in llamadas


def test_fechas_invalidas_se_ignoran(client, fake_db):
    _loguear(client, fake_db)
    r = client.get("/api/montor?desde=ayer&hasta=<script>")
    assert r.status_code == 200
    llamadas = _filtros(fake_db)
    assert not [c for c in llamadas if c[0] in ("gte", "lte") and c[1][0] == "fecha"]


def test_el_plan_gratis_no_puede_pedir_mas_de_90_dias(client, fake_db, monkeypatch):
    _loguear(client, fake_db, plan="free")
    client.get("/api/montor?desde=2020-01-01")
    gte = [c for c in _filtros(fake_db) if c[0] == "gte" and c[1][0] == "fecha"]
    # Se queda con el tope de la cuenta gratis, no con la fecha pedida.
    assert gte and gte[0][1][1] != "2020-01-01"


def test_el_plan_gratis_conserva_un_desde_mas_reciente(client, fake_db):
    _loguear(client, fake_db, plan="free")
    hoy = app_module._hoy_ar().isoformat()
    client.get(f"/api/montor?desde={hoy}")
    gte = [c for c in _filtros(fake_db) if c[0] == "gte" and c[1][0] == "fecha"]
    assert gte and gte[0][1][1] == hoy


def test_hay_un_tope_de_filas(client, fake_db):
    _loguear(client, fake_db)
    client.get("/api/montor")
    limites = [c for c in _filtros(fake_db) if c[0] == "limit"]
    assert limites and limites[0][1][0] == 2000


def test_el_limit_pedido_tiene_techo(client, fake_db):
    _loguear(client, fake_db)
    client.get("/api/montor?limit=999999")
    limites = [c for c in _filtros(fake_db) if c[0] == "limit"]
    assert limites and limites[0][1][0] == 5000


def test_limit_basura_cae_al_default(client, fake_db):
    _loguear(client, fake_db)
    client.get("/api/montor?limit=muchas")
    limites = [c for c in _filtros(fake_db) if c[0] == "limit"]
    assert limites and limites[0][1][0] == 2000


class TestCategorias:
    def test_devuelve_las_mas_usadas_primero(self, client, fake_db):
        _loguear(client, fake_db)
        fake_db.tables["transacciones"] = [
            {"categoria": "Comida"}, {"categoria": "Comida"}, {"categoria": "Comida"},
            {"categoria": "Alquiler"}, {"categoria": "Alquiler"},
            {"categoria": "Ocio"},
        ]
        r = client.get("/api/montor/categorias")
        assert [c["nombre"] for c in r.get_json()] == ["Comida", "Alquiler", "Ocio"]

    def test_agrupa_ignorando_mayusculas_y_tildes(self, client, fake_db):
        _loguear(client, fake_db)
        fake_db.tables["transacciones"] = [
            {"categoria": "Almacén"}, {"categoria": "almacen"}, {"categoria": "ALMACEN"},
        ]
        datos = client.get("/api/montor/categorias").get_json()
        assert len(datos) == 1
        assert datos[0] == {"nombre": "Almacén", "usos": 3}

    def test_ignora_las_vacias(self, client, fake_db):
        _loguear(client, fake_db)
        fake_db.tables["transacciones"] = [{"categoria": "  "}, {"categoria": None}]
        assert client.get("/api/montor/categorias").get_json() == []
