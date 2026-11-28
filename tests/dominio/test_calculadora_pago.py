"""Pruebas de CalculadoraEstandar: clasificación de horas y regla del tope semanal."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA
from compulab.dominio.pagos import MarcaTrabajada, Recargo, Tarifa
from compulab.dominio.pagos.calculadora import CalculadoraEstandar, es_del_mes

TARIFAS = {"A": Tarifa("A", 1000), "B": Tarifa("B", 2000)}
RECARGO = Recargo(50)


def momento(mes: int, dia: int, hora: int, anio: int = 2026) -> datetime:
    return datetime(anio, mes, dia, hora, tzinfo=ZONA_COSTA_RICA)


def marca(dia: int, desde: int, horas: int, mes: int = 11, asistente="A1", categoria="A",
          tope=20, anio: int = 2026) -> MarcaTrabajada:
    """Turno trabajado completo: entra a la hora de inicio y sale al fin programado."""
    inicio = momento(mes, dia, desde, anio)
    fin = inicio + timedelta(hours=horas)
    return MarcaTrabajada(asistente, categoria, Decimal(tope), inicio, fin, inicio, fin)


def calcular(marcas, anio=2026, mes=11):
    return CalculadoraEstandar().calcular(anio, mes, marcas, TARIFAS.__getitem__, RECARGO)


# --- Clasificación ---


def test_turno_diurno_entre_semana_es_normal():
    [linea] = calcular([marca(23, 8, 4)])  # lunes
    assert (linea.horas_normales, linea.horas_con_recargo) == (Decimal("4"), Decimal("0"))
    assert linea.monto == Decimal("4000")


def test_turno_nocturno_y_fin_de_semana_llevan_un_solo_recargo():
    [linea] = calcular([
        marca(23, 18, 3),   # lunes 18:00: nocturno
        marca(28, 8, 2),    # sábado de día
        marca(29, 19, 2),   # domingo de noche: un solo recargo, no dos
    ])
    assert linea.horas_con_recargo == Decimal("7")
    assert linea.horas_normales == Decimal("0")
    assert linea.monto == Decimal("10500")  # 7 × 1000 × 1.5


def test_el_recargo_depende_del_inicio_del_turno():
    # Empieza 17:00 y termina 19:00: todas sus horas son normales.
    [linea] = calcular([marca(23, 17, 2)])
    assert linea.horas_normales == Decimal("2")


# --- Una línea por asistente ---


def test_una_linea_por_asistente_ordenada_por_id_y_con_su_tarifa():
    lineas = calcular([marca(23, 8, 2, asistente="A2", categoria="B"), marca(24, 8, 3)])
    assert [l.asistente_id for l in lineas] == ["A1", "A2"]
    assert lineas[0].tarifa == Decimal("1000")
    assert lineas[1].tarifa == Decimal("2000")
    assert lineas[1].monto == Decimal("4000")


def test_asistente_sin_marcas_en_el_mes_no_aparece():
    assert calcular([marca(23, 8, 2, mes=10)]) == []
    assert calcular([]) == []


# --- Tope semanal ---


def test_horas_sobre_tope_son_las_ultimas_de_la_semana():
    lineas = calcular([
        marca(27, 18, 4, tope=10),  # viernes noche, la última
        marca(23, 8, 8, tope=10),   # lunes
        marca(24, 8, 4, tope=10),   # martes
    ])
    [linea] = lineas
    # Lunes 8 h + martes 2 h llegan al tope; martes 2 h y viernes 4 h quedan sobre el tope.
    assert linea.horas_normales == Decimal("10")
    assert linea.horas_con_recargo == Decimal("0")
    assert linea.horas_sobre_tope == Decimal("6")
    assert linea.monto == Decimal("10000")


def test_si_la_hora_sobre_tope_tiene_recargo_se_resta_del_recargo():
    [linea] = calcular([marca(23, 8, 8, tope=10), marca(23, 18, 4, tope=10)])
    assert linea.horas_normales == Decimal("8")
    assert linea.horas_con_recargo == Decimal("2")
    assert linea.horas_sobre_tope == Decimal("2")


def test_el_tope_se_aplica_por_semana():
    # 10 h en dos semanas distintas con tope 8: cada semana se compara por separado.
    [linea] = calcular([marca(16, 8, 6, tope=8), marca(23, 8, 6, tope=8)])
    assert linea.horas_normales == Decimal("12")
    assert linea.horas_sobre_tope == Decimal("0")


def test_semana_que_cruza_meses_cuenta_horas_del_mes_anterior_contra_el_tope():
    # Ejemplo del documento: tope 20, lunes 30 de noviembre 8 h y del 1 al 6 de
    # diciembre 15 h. Diciembre solo paga 12 h y registra 3 h sobre el tope.
    marcas = [
        marca(30, 8, 8, mes=11),
        marca(1, 8, 5, mes=12),
        marca(2, 8, 5, mes=12),
        marca(3, 8, 5, mes=12),
    ]
    [diciembre] = calcular(marcas, mes=12)
    assert diciembre.horas_normales == Decimal("12")
    assert diciembre.horas_sobre_tope == Decimal("3")
    # Noviembre paga sus 8 h completas: lo que pase en diciembre no lo cambia.
    [noviembre] = calcular(marcas, mes=11)
    assert noviembre.horas_normales == Decimal("8")
    assert noviembre.horas_sobre_tope == Decimal("0")


def test_horas_del_mes_anterior_no_se_pagan_ni_se_registran():
    [diciembre] = calcular([marca(30, 0, 12, mes=11), marca(30, 12, 10, mes=11),
                            marca(1, 8, 4, mes=12)], mes=12)
    # Noviembre ya tenía 22 h (2 sobre el tope) en esa semana: diciembre no las vuelve a registrar.
    assert diciembre.horas_normales == Decimal("0")
    assert diciembre.horas_sobre_tope == Decimal("4")


def test_marca_sin_salida_se_paga_hasta_el_fin_programado():
    inicio = momento(11, 23, 8)
    sin_salida = MarcaTrabajada("A1", "A", Decimal("20"), inicio, inicio + timedelta(hours=4),
                                inicio + timedelta(hours=1))
    [linea] = calcular([sin_salida])
    assert linea.horas_normales == Decimal("3")


@pytest.mark.parametrize("anio, mes, esperado", [(2026, 11, True), (2026, 12, False)])
def test_cada_turno_es_del_mes_del_dia_en_que_ocurre(anio, mes, esperado):
    # 23:00 del 30 de noviembre en Costa Rica ya es 1 de diciembre en UTC.
    assert es_del_mes(marca(30, 22, 1), anio, mes) is esperado
