"""
Las transacciones en USD/EUR guardan la cotización del día en que se cargan
(columnas cotizacion_usd/cotizacion_eur), para que los totales no se
revaloricen solos cada vez que cambia el dólar - ver _cotiz_de_tx en
montor_server.py. Estos tests simulan que la cotización "de hoy" cambió
después de cargada la transacción, y verifican que el total no se mueva.
"""
import montor_server as app_module


def _loguear(client, fake_db, user_id="u1", pro=True):
    fake_db.tables["usuarios"] = [{
        "id": user_id, "plan": "pro" if pro else "free", "trial_expira": None,
    }]
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "nico"


def test_insertar_transaccion_guarda_la_cotizacion_de_su_fecha(fake_db, monkeypatch):
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1500.0, "EUR": 1650.0})

    ok, tx = app_module._insertar_transaccion("u1", "Gasto", 100, "2026-08-01", moneda="USD")

    assert ok is True
    assert tx["cotizacion_usd"] == 1500.0
    assert tx["cotizacion_eur"] == 1650.0


def test_insertar_transaccion_en_ars_tambien_guarda_la_foto(fake_db, monkeypatch):
    # Hace falta guardarla incluso para gastos en pesos: un viaje puede
    # necesitar convertir ese gasto a USD/EUR más adelante.
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1500.0, "EUR": 1650.0})

    ok, tx = app_module._insertar_transaccion("u1", "Gasto", 1000, "2026-08-01", moneda="ARS")

    assert ok is True
    assert tx["cotizacion_usd"] == 1500.0
    assert tx["cotizacion_eur"] == 1650.0


def test_insertar_transaccion_le_pasa_su_propia_fecha_al_lookup(fake_db, monkeypatch):
    # Carga tardía: dos transacciones con fechas distintas tienen que pedir
    # (y poder recibir) cotizaciones históricas distintas.
    vistas = []

    def fake_lookup(fecha):
        vistas.append(fecha)
        return {"USD": 1500.0, "EUR": 1650.0}

    monkeypatch.setattr(app_module, "_cotizacion_para_fecha", fake_lookup)

    app_module._insertar_transaccion("u1", "Gasto", 100, "2026-08-11", moneda="USD")
    app_module._insertar_transaccion("u1", "Gasto", 100, "2026-08-20", moneda="USD")

    assert vistas == ["2026-08-11", "2026-08-20"]


def test_stats_usa_la_cotizacion_guardada_no_la_de_hoy(fake_db, monkeypatch):
    # Se cargó cuando el dólar valía 1000. Si "hoy" el dólar vale 2000, el
    # total en pesos de ese gasto tiene que seguir dando 100.000, no 200.000.
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 100, "moneda": "USD", "categoria": "Viaje",
         "cotizacion_usd": 1000.0, "cotizacion_eur": 1100.0},
    ]
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 2000.0, "EUR": 2200.0})

    stats = app_module._stats_mes("u1", 8, 2026)

    assert stats["resumen"]["gastos_actual"] == 100_000.0


def test_stats_fila_vieja_sin_cotizacion_cae_a_la_de_hoy(fake_db, monkeypatch):
    # Filas cargadas antes de que existiera esta columna no tienen foto
    # guardada: ahí sí hay que usar la cotización actual como mejor esfuerzo.
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 100, "moneda": "USD", "categoria": "Viaje"},
    ]
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1500.0, "EUR": 1650.0})

    stats = app_module._stats_mes("u1", 8, 2026)

    assert stats["resumen"]["gastos_actual"] == 150_000.0


def test_viaje_usa_la_cotizacion_guardada_por_transaccion(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    fake_db.tables["viajes"] = [{"id": 1, "nombre": "Brasil", "user_id": "u1"}]
    fake_db.tables["transacciones"] = [
        {"tipo": "Gasto", "monto": 100, "moneda": "USD", "categoria": "Comida",
         "viaje_id": 1, "cotizacion_usd": 1000.0, "cotizacion_eur": 1100.0, "fecha": "2026-01-01"},
    ]
    # El dólar "hoy" duplicó su valor respecto de cuando se cargó el gasto.
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 2000.0, "EUR": 2200.0})

    r = client.get("/api/montor/viajes/1")

    assert r.status_code == 200
    assert r.get_json()["totales"]["ARS"] == 100_000.0


def test_editar_transaccion_no_pisa_la_cotizacion_ya_guardada(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    fake_db.tables["transacciones"] = [{
        "id": 5, "cotizacion_usd": 1000.0, "cotizacion_eur": 1100.0,
    }]
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 2000.0, "EUR": 2200.0})

    r = client.put("/api/montor/5", json={
        "tipo": "Gasto", "monto": 50, "fecha": "2026-01-01", "moneda": "USD",
    })

    assert r.status_code == 200
    payload_enviado = [
        call for (tabla, q) in fake_db.queries if tabla == "transacciones"
        for call in q.calls if call[0] == "update"
    ][-1][1][0]
    assert "cotizacion_usd" not in payload_enviado


def test_editar_transaccion_vieja_completa_la_cotizacion_faltante(client, fake_db, monkeypatch):
    _loguear(client, fake_db)
    fake_db.tables["transacciones"] = [{"id": 5, "cotizacion_usd": None, "cotizacion_eur": None}]
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 2000.0, "EUR": 2200.0})

    r = client.put("/api/montor/5", json={
        "tipo": "Gasto", "monto": 50, "fecha": "2026-01-01", "moneda": "USD",
    })

    assert r.status_code == 200
    payload_enviado = [
        call for (tabla, q) in fake_db.queries if tabla == "transacciones"
        for call in q.calls if call[0] == "update"
    ][-1][1][0]
    assert payload_enviado["cotizacion_usd"] == 2000.0
    assert payload_enviado["cotizacion_eur"] == 2200.0


class TestCotizacionParaFecha:
    """_cotizacion_para_fecha: la carga tardía (fecha pasada) tiene que usar
    la cotización histórica de esa fecha, no la de hoy."""

    def _fijar_hoy(self, monkeypatch, fecha_iso):
        from datetime import date as date_cls
        monkeypatch.setattr(app_module, "_hoy_ar", lambda: date_cls.fromisoformat(fecha_iso))

    def test_fecha_de_hoy_usa_la_cotizacion_en_vivo(self, monkeypatch):
        self._fijar_hoy(monkeypatch, "2026-08-26")
        monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1531.0, "EUR": 1666.0})
        monkeypatch.setattr(app_module, "_evolucion_usd", lambda: (_ for _ in ()).throw(
            AssertionError("no debería consultar el histórico para la fecha de hoy")))

        cotiz = app_module._cotizacion_para_fecha("2026-08-26")

        assert cotiz == {"USD": 1531.0, "EUR": 1666.0}

    def test_fecha_pasada_con_dato_exacto_usa_el_historico(self, monkeypatch):
        self._fijar_hoy(monkeypatch, "2026-08-26")
        monkeypatch.setattr(app_module, "_evolucion_usd", lambda: {"2026-08-11": 1500.0})
        monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1531.0, "EUR": 1666.0})

        cotiz = app_module._cotizacion_para_fecha("2026-08-11")

        assert cotiz["USD"] == 1500.0
        # El euro se aproxima con la relación EUR/USD de hoy sobre el dólar histórico.
        assert cotiz["EUR"] == round(1500.0 * (1666.0 / 1531.0), 2)

    def test_fin_de_semana_sin_dato_cae_al_dia_habil_anterior(self, monkeypatch):
        # Sábado 2026-08-22 y domingo 2026-08-23 no tienen publicación:
        # tiene que usar el viernes 2026-08-21.
        self._fijar_hoy(monkeypatch, "2026-08-26")
        monkeypatch.setattr(app_module, "_evolucion_usd", lambda: {"2026-08-21": 1520.0})
        monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1531.0, "EUR": 1666.0})

        cotiz = app_module._cotizacion_para_fecha("2026-08-23")

        assert cotiz["USD"] == 1520.0

    def test_sin_ningun_dato_historico_cae_a_la_cotizacion_en_vivo(self, monkeypatch):
        self._fijar_hoy(monkeypatch, "2026-08-26")
        monkeypatch.setattr(app_module, "_evolucion_usd", lambda: {})
        monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1531.0, "EUR": 1666.0})

        cotiz = app_module._cotizacion_para_fecha("2026-08-11")

        assert cotiz == {"USD": 1531.0, "EUR": 1666.0}
