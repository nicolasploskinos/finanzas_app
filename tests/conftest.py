"""
Fixtures compartidas para los tests.

Los tests nunca tocan la base de datos real: se reemplaza finanzas_server.db
por un FakeDB en memoria (ver más abajo) antes de que cualquier test corra,
así que no hace falta credenciales de Supabase reales ni conexión a internet.
"""
import os
import sys

# Variables dummy: finanzas_server las lee al importarse (app.secret_key,
# create_client), pero create_client no valida nada hasta la primera consulta
# real, y esa consulta nunca ocurre porque reemplazamos "db" antes de usarlo.
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import finanzas_server as app_module


class FakeResult:
    """Imita la forma de PostgrestResponse: solo importa .data."""
    def __init__(self, data):
        self.data = data


class FakeQuery:
    """
    Imita la interfaz encadenable de supabase-py (.select().eq().order()...).
    Cualquier método que no sea execute() devuelve la misma instancia, así
    que las cadenas .select("*").eq("user_id", x).order("fecha") funcionan
    sin tener que implementar cada método a mano.

    Si en la cadena hubo un .insert()/.upsert(), execute() devuelve esa
    misma fila como si la base se la hubiese devuelto (con un id generado
    si no traía uno) — así un test no tiene que precargar "la tabla ya
    tiene la fila que recién voy a insertar".
    """
    def __init__(self, data):
        self._data = data
        self.calls = []
        self._written = None

    def __getattr__(self, name):
        def method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name in ("insert", "update", "upsert") and args:
                self._written = args[0]
            return self
        return method

    def execute(self):
        if self._written is not None:
            rows = self._written if isinstance(self._written, list) else [self._written]
            rows = [{"id": row.get("id", "generated-id"), **row} for row in rows]
            return FakeResult(rows)
        return FakeResult(self._data)


class FakeDB:
    """
    Reemplazo de finanzas_server.db para tests.

    `tables` mapea nombre de tabla -> lista de filas que debe devolver
    CUALQUIER .execute() sobre esa tabla (alcanza para los tests actuales,
    que solo hacen una consulta relevante por tabla y por request).
    `queries` guarda cada (tabla, FakeQuery) para poder inspeccionar en el
    test qué se intentó guardar/filtrar.
    """
    def __init__(self, tables=None):
        self.tables = tables or {}
        self.queries = []

    def table(self, name):
        q = FakeQuery(self.tables.get(name, []))
        self.queries.append((name, q))
        return q


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(app_module, "db", db)
    return db


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    # _login_intentos vive a nivel de módulo (así persiste entre requests
    # reales), así que sin esto un test que agota el límite dejaría a los
    # siguientes tests con ese username bloqueado.
    app_module._login_intentos.clear()
    yield
    app_module._login_intentos.clear()


@pytest.fixture(autouse=True)
def _reset_resumen_ia_cache():
    # Mismo motivo que _reset_rate_limit: _resumen_ia_cache es un dict a
    # nivel de módulo, y varios tests reutilizan el mismo user_id/mes.
    app_module._resumen_ia_cache.clear()
    yield
    app_module._resumen_ia_cache.clear()


@pytest.fixture(autouse=True)
def _mock_cotizaciones(monkeypatch):
    # _obtener_cotizaciones y _evolucion_usd pegan contra APIs externas
    # (bluelytics). Desde que las transacciones guardan una foto de la
    # cotización al cargarse (ver _insertar_transaccion / _cotizacion_para_fecha),
    # cualquier test que cree/edite/importe una transacción pasa por acá -
    # mockeadas por default para no depender de internet. Con _evolucion_usd
    # vacío, _cotizacion_para_fecha cae siempre al valor fijo de
    # _obtener_cotizaciones, salvo que un test pise cualquiera de las dos
    # (ver test_cotizaciones_es_publica_a_proposito y TestCotizacionParaFecha
    # en test_cotizacion_historica.py, que sí ejercitan el lookup histórico real).
    monkeypatch.setattr(app_module, "_obtener_cotizaciones", lambda: {"USD": 1000.0, "EUR": 1100.0})
    monkeypatch.setattr(app_module, "_evolucion_usd", lambda: {})


