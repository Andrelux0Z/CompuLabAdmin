"""Pruebas de CierreMensual, Constancia y la franja del mes."""

from datetime import datetime
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA
from compulab.dominio.pagos import CierreInmutable, LineaPago
from compulab.dominio.pagos.cierre import (
    CierreMensual,
    Constancia,
    EstadoCierre,
    franja_del_mes,
)


def linea(asistente_id="A1", sobre_tope="0", monto="10000") -> LineaPago:
    return LineaPago(asistente_id, Decimal("10"), Decimal("0"), Decimal(sobre_tope),
                     Decimal(monto), Decimal("1000"), Decimal("50"))


def constancia(texto="Becas pagó 2 h más por error") -> Constancia:
    return Constancia(texto, "coord-soporte", datetime(2026, 12, 3, 9, tzinfo=ZONA_COSTA_RICA))


def cierre(*lineas) -> CierreMensual:
    return CierreMensual(2026, 11, lineas or [linea()])


# --- Invariantes ---


def test_cierre_nuevo_queda_cerrado_con_sus_lineas():
    c = cierre(linea("A1"), linea("A2"))
    assert (c.anio, c.mes) == (2026, 11)
    assert [l.asistente_id for l in c.lineas] == ["A1", "A2"]
    assert c.estado is EstadoCierre.CERRADO
    assert c.constancias == ()


@pytest.mark.parametrize("mes", [0, 13, "11", True])
def test_cierre_rechaza_mes_fuera_de_1_a_12(mes):
    with pytest.raises(CierreInmutable):
        CierreMensual(2026, mes, [linea()])


def test_cierre_rechaza_dos_lineas_del_mismo_asistente():
    with pytest.raises(CierreInmutable):
        cierre(linea("A1"), linea("A1"))


def test_cierre_rechaza_lineas_de_otro_tipo():
    with pytest.raises(CierreInmutable):
        CierreMensual(2026, 11, [("A1", 10)])


def test_cierre_sin_lineas_es_valido():
    assert CierreMensual(2026, 11, []).lineas == ()


# --- Inmutabilidad ---


def test_cierre_es_inmutable():
    c = cierre()
    with pytest.raises(CierreInmutable):
        c.mes = 12
    with pytest.raises(CierreInmutable):
        c._lineas = ()
    with pytest.raises(CierreInmutable):
        del c._anio
    assert isinstance(c.lineas, tuple)


def test_constancias_solo_se_agregan():
    c = cierre()
    primera, segunda = constancia("primera"), constancia("segunda")
    c.agregar_constancia(primera)
    c.agregar_constancia(segunda)
    assert c.constancias == (primera, segunda)
    assert isinstance(c.constancias, tuple)


def test_agregar_constancia_no_cambia_las_lineas():
    c = cierre()
    antes = c.lineas
    c.agregar_constancia(constancia())
    assert c.lineas is antes


def test_solo_se_agregan_constancias():
    with pytest.raises(CierreInmutable):
        cierre().agregar_constancia("texto suelto")


@pytest.mark.parametrize("campo", ["texto", "autor"])
def test_constancia_rechaza_textos_vacios(campo):
    datos = {"texto": "t", "autor": "a", "fecha": datetime(2026, 12, 3, tzinfo=ZONA_COSTA_RICA)}
    datos[campo] = " "
    with pytest.raises(CierreInmutable):
        Constancia(**datos)


# --- Consultas ---


def test_monto_total_y_lineas_con_horas_sobre_tope():
    c = cierre(linea("A1", monto="10000"), linea("A2", sobre_tope="3", monto="5000"))
    assert c.monto_total == Decimal("15000")
    assert [l.asistente_id for l in c.lineas_con_horas_sobre_tope()] == ["A2"]
    assert c.linea_de("A2").horas_sobre_tope == Decimal("3")
    assert c.linea_de("A9") is None


# --- Franja del mes ---


def test_franja_del_mes_va_del_dia_1_al_dia_1_siguiente_en_costa_rica():
    franja = franja_del_mes(2026, 11)
    assert franja.inicio == datetime(2026, 11, 1, tzinfo=ZONA_COSTA_RICA)
    assert franja.fin == datetime(2026, 12, 1, tzinfo=ZONA_COSTA_RICA)


def test_franja_de_diciembre_termina_en_enero():
    assert franja_del_mes(2026, 12).fin == datetime(2027, 1, 1, tzinfo=ZONA_COSTA_RICA)
