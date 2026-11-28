"""Pruebas del contrato CU-18: una por poscondición (P) y una por extensión (E).

Los nombres son los de la tabla 11.2 del documento de diseño.
"""

from datetime import date
from decimal import Decimal

import pytest

from compulab.aplicacion.cerrar_mes import COORDINACION_DE_SOPORTE, CerrarMes
from compulab.dominio.compartido.reloj import RelojFijo
from compulab.dominio.pagos import (
    CierreInmutable,
    MesNoTerminado,
    MesYaCerrado,
    TarifaNoConfigurada,
)
from compulab.dominio.pagos.cierre import CierreMensual, EstadoCierre
from apoyo_pagos import (
    CierresEnMemoria,
    ExportadorEspia,
    MarcasEnMemoria,
    NotificadorEspia,
    TarifasFijas,
    m,
    marca,
)

PRIMERO_DE_DICIEMBRE = m(12, 1, 0, 5)  # el planificador corre el día 1 a las 00:05


class Escenario:
    """Tarifa A = 1000 por hora, tarifa B = 2000, recargo del 50 %."""

    def __init__(self, *marcas, ahora=PRIMERO_DE_DICIEMBRE, cierres=(),
                 tarifas=None, recargo=50):
        self.cierres = CierresEnMemoria(*cierres)
        self.marcas = MarcasEnMemoria(*marcas)
        self.configuracion = TarifasFijas(tarifas if tarifas is not None else {"A": 1000, "B": 2000},
                                          recargo)
        self.exportador = ExportadorEspia()
        self.notificador = NotificadorEspia()
        self.caso = CerrarMes(RelojFijo(ahora), self.cierres, self.marcas, self.configuracion,
                              self.exportador, self.notificador)

    def cerrar(self, anio=2026, mes=11):
        return self.caso.ejecutar(anio, mes)

    def nada_cambio(self, cierres_previos=0):
        return (len(self.cierres.todos) == cierres_previos and not self.exportador.exportados
                and not self.notificador.enviados)


# --- Poscondiciones ---


def test_cierre_tiene_una_linea_por_asistente_con_marcas():
    cierre = Escenario(
        marca(m(11, 23, 8), 4, asistente="A1"),
        marca(m(11, 24, 8), 2, asistente="A1"),
        marca(m(11, 24, 8), 3, asistente="A2", categoria="B"),
    ).cerrar()
    assert [l.asistente_id for l in cierre.lineas] == ["A1", "A2"]        # P1
    assert cierre.linea_de("A1").horas_normales == Decimal("6")


def test_monto_aplica_tarifa_y_recargo():
    cierre = Escenario(
        marca(m(11, 23, 8), 10),     # lunes de día: 10 h normales
        marca(m(11, 24, 18), 4),     # martes 18:00: 4 h con recargo
    ).cerrar()
    linea = cierre.linea_de("A1")
    assert linea.horas_normales == Decimal("10")                           # P2
    assert linea.horas_con_recargo == Decimal("4")
    assert linea.monto == Decimal("16000")  # 10 × 1000 + 4 × 1000 × 1.5
    assert (linea.tarifa, linea.recargo) == (Decimal("1000"), Decimal("50"))


def test_horas_sobre_tope_no_se_pagan_y_se_notifican():
    escenario = Escenario(marca(m(11, 23, 8), 8, tope=6))
    linea = escenario.cerrar().linea_de("A1")
    assert linea.horas_sobre_tope == Decimal("2")                          # P3 / E5
    assert linea.monto == Decimal("6000")
    [aviso] = escenario.notificador.a(COORDINACION_DE_SOPORTE)
    assert "A1" in aviso and "2 h sobre su tope" in aviso


def test_horas_sobre_tope_son_las_ultimas_de_la_semana():
    linea = Escenario(
        marca(m(11, 27, 18), 4, tope=10),   # viernes noche: la última de la semana
        marca(m(11, 23, 8), 8, tope=10),
        marca(m(11, 25, 8), 2, tope=10),
    ).cerrar().linea_de("A1")
    assert linea.horas_normales == Decimal("10")                           # P3
    assert linea.horas_con_recargo == Decimal("0")
    assert linea.horas_sobre_tope == Decimal("4")


def test_cierre_genera_archivo_para_becas():
    escenario = Escenario(marca(m(11, 23, 8), 4))
    cierre = escenario.cerrar()
    assert escenario.exportador.exportados == [(2026, 11, cierre.lineas)]  # P4


def test_cierre_es_inmutable():
    escenario = Escenario(marca(m(11, 23, 8), 4))
    cierre = escenario.cerrar()
    assert cierre.estado is EstadoCierre.CERRADO                           # P5
    assert escenario.cierres.todos == [cierre]
    with pytest.raises(CierreInmutable):
        cierre.mes = 12


# --- Extensiones ---


def test_mes_ya_cerrado_es_rechazado():
    escenario = Escenario(marca(m(11, 23, 8), 4), cierres=[CierreMensual(2026, 11, [])])
    with pytest.raises(MesYaCerrado):                                      # E1
        escenario.cerrar()
    assert escenario.nada_cambio(cierres_previos=1)


def test_mes_no_terminado_es_rechazado():
    escenario = Escenario(marca(m(11, 23, 8), 4), ahora=m(11, 30, 23, 59))
    with pytest.raises(MesNoTerminado):                                    # E2
        escenario.cerrar()
    assert escenario.nada_cambio()


def test_asistente_sin_marcas_no_aparece():
    cierre = Escenario(marca(m(11, 23, 8), 4, asistente="A1")).cerrar()
    assert cierre.linea_de("A2") is None                                   # E3
    assert len(cierre.lineas) == 1


def test_entrada_sin_salida_se_paga_hasta_fin_programado():
    escenario = Escenario(marca(m(11, 23, 8), 4, sin_salida=True))
    linea = escenario.cerrar().linea_de("A1")
    assert linea.horas_normales == Decimal("4")                            # E4
    [aviso] = escenario.notificador.a(COORDINACION_DE_SOPORTE)
    assert "no marcó salida" in aviso


def test_sin_tarifa_configurada_es_rechazado():
    escenario = Escenario(marca(m(11, 23, 8), 4, categoria="C"))
    with pytest.raises(TarifaNoConfigurada):                               # E6
        escenario.cerrar()
    assert escenario.nada_cambio()


def test_sin_recargo_configurado_es_rechazado():
    escenario = Escenario(marca(m(11, 23, 8), 4), recargo=None)
    with pytest.raises(TarifaNoConfigurada):                               # E6
        escenario.cerrar()
    assert escenario.nada_cambio()


def test_turno_nocturno_y_fin_de_semana_llevan_un_solo_recargo():
    linea = Escenario(marca(m(11, 28, 20), 2)).cerrar().linea_de("A1")    # sábado 20:00
    assert linea.horas_con_recargo == Decimal("2")                         # E7
    assert linea.monto == Decimal("3000")  # 2 × 1000 × 1.5, no 1.5 × 1.5


def test_semana_que_cruza_meses_cuenta_horas_del_mes_anterior_contra_el_tope():
    # Ejemplo del documento: tope 20 h; lunes 30 de noviembre 8 h; del 1 al 6 de
    # diciembre 15 h. Diciembre paga 12 h y registra 3 h sobre el tope.
    escenario = Escenario(
        marca(m(11, 30, 8), 8),
        marca(m(12, 1, 8), 5),
        marca(m(12, 2, 8), 5),
        marca(m(12, 3, 8), 5),
        ahora=m(1, 1, 0, 5, anio=2027),
    )
    diciembre = escenario.cerrar(2026, 12).linea_de("A1")
    assert diciembre.horas_normales == Decimal("12")                       # E8
    assert diciembre.horas_sobre_tope == Decimal("3")
    assert escenario.marcas.franjas_pedidas[0].inicio == m(11, 30, 0)


# --- Otros ---


def test_tarifas_y_recargo_vigentes_son_los_del_dia_1_del_mes():
    escenario = Escenario(marca(m(11, 23, 8), 4))
    escenario.cerrar()
    assert set(escenario.configuracion.fechas_pedidas) == {date(2026, 11, 1)}


def test_mes_invalido_es_rechazado():
    with pytest.raises(CierreInmutable):
        Escenario().cerrar(2026, 13)
