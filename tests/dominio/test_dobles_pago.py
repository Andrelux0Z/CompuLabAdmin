"""Pruebas de los dobles en memoria de los puertos del pago.

Fijan el comportamiento que el caso de uso espera de cualquier adaptador de esos puertos.
"""

from datetime import date
from decimal import Decimal

from compulab.dominio.compartido import Franja
from compulab.dominio.pagos import LineaPago
from compulab.dominio.pagos.cierre import CierreMensual
from apoyo_pagos import (
    CierresEnMemoria,
    ExportadorEspia,
    MarcasEnMemoria,
    NotificadorEspia,
    TarifasFijas,
    m,
    marca,
)


def test_cierres_en_memoria_sabe_si_el_mes_existe():
    repo = CierresEnMemoria()
    assert not repo.existe(2026, 11)
    repo.guardar(CierreMensual(2026, 11, []))
    assert repo.existe(2026, 11)
    assert not repo.existe(2026, 10)


def test_marcas_de_franja_filtra_por_inicio_del_turno():
    dentro, fuera = marca(m(11, 23, 8)), marca(m(12, 1, 8))
    consulta = MarcasEnMemoria(dentro, fuera)
    assert consulta.de_franja(Franja(m(11, 1, 0), m(12, 1, 0))) == [dentro]


def test_marca_sin_salida():
    assert marca(m(11, 23, 8), sin_salida=True).salida is None


def test_tarifas_fijas_devuelven_none_si_no_hay_configuracion():
    config = TarifasFijas({"A": 1000}, recargo=None)
    assert config.tarifa_vigente("A", date(2026, 11, 1)).monto_por_hora == Decimal("1000")
    assert config.tarifa_vigente("B", date(2026, 11, 1)) is None
    assert config.recargo_vigente(date(2026, 11, 1)) is None


def test_espias_registran_lo_que_reciben():
    notificador, exportador = NotificadorEspia(), ExportadorEspia()
    notificador.notificar("soporte", "hola")
    linea = LineaPago("A1", Decimal("1"), Decimal("0"), Decimal("0"), Decimal("1000"),
                      Decimal("1000"), Decimal("50"))
    assert exportador.exportar(2026, 11, [linea]) == "becas_2026_11.csv"
    assert notificador.a("soporte") == ["hola"]
    assert exportador.exportados == [(2026, 11, (linea,))]
