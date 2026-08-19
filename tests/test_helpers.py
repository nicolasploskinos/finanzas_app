"""Funciones puras (sin base de datos) — las más fáciles de romper sin darse cuenta."""
from datetime import date, datetime, timezone

import finanzas_server as app_module


class TestHoyAr:
    def test_devuelve_un_date(self):
        assert isinstance(app_module._hoy_ar(), date)

    def test_es_utc_menos_3(self):
        # A las 01:00 UTC del día 2, en Buenos Aires (UTC-3) todavía es
        # el día 1 a las 22:00. Si esto alguna vez usara date.today() del
        # servidor (UTC) en vez de restar el offset, este test lo detecta.
        fake_now = datetime(2026, 8, 2, 1, 0, tzinfo=timezone.utc)

        class FakeDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fake_now

        original = app_module.datetime
        app_module.datetime = FakeDatetime
        try:
            assert app_module._hoy_ar() == date(2026, 8, 1)
        finally:
            app_module.datetime = original


class TestConvertirMoneda:
    COTIZ = {"USD": 1500.0, "EUR": 1650.0}

    def test_misma_moneda_no_convierte(self):
        assert app_module._convertir_moneda(100, "USD", "USD", self.COTIZ) == 100

    def test_ars_a_usd(self):
        resultado = app_module._convertir_moneda(1500, "ARS", "USD", self.COTIZ)
        assert resultado == 1.0

    def test_usd_a_ars(self):
        resultado = app_module._convertir_moneda(2, "USD", "ARS", self.COTIZ)
        assert resultado == 3000.0

    def test_usd_a_eur_pasa_por_ars(self):
        resultado = app_module._convertir_moneda(1, "USD", "EUR", self.COTIZ)
        assert round(resultado, 4) == round(1500.0 / 1650.0, 4)

    def test_sin_cotizacion_devuelve_none_no_explota(self):
        cotiz_caida = {"USD": None, "EUR": None}
        assert app_module._convertir_moneda(100, "USD", "ARS", cotiz_caida) is None
        assert app_module._convertir_moneda(100, "ARS", "USD", cotiz_caida) is None


class TestSiguienteFecha:
    def test_semanal_suma_siete_dias(self):
        assert app_module._siguiente_fecha("2026-08-01", "semanal") == "2026-08-08"

    def test_mensual_avanza_un_mes(self):
        assert app_module._siguiente_fecha("2026-08-15", "mensual") == "2026-09-15"

    def test_mensual_en_diciembre_pasa_al_siguiente_anio(self):
        assert app_module._siguiente_fecha("2026-12-10", "mensual") == "2027-01-10"

    def test_mensual_recorta_dia_31_a_febrero(self):
        # No existe el 31 de febrero: tiene que caer en el último día real del mes.
        assert app_module._siguiente_fecha("2026-01-31", "mensual") == "2026-02-28"
