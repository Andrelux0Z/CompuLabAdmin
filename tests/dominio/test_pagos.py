"""Pruebas de los tipos de datos de pagos: MarcaTrabajada y LineaPago."""

from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA, FechaSinZonaHoraria
from compulab.dominio.pagos import LineaPago, MarcaInvalida, MarcaTrabajada


def cr(dia: int, hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


def marca(**cambios) -> MarcaTrabajada:
    datos = {
        "asistente_id": "A-1",
        "categoria": "asistente",
        "tope_semanal": Decimal("20"),
        "inicio_turno": cr(23, 8),
        "fin_turno": cr(23, 12),
        "entrada": cr(23, 8, 5),
        "salida": cr(23, 12),
    }
    datos.update(cambios)
    return MarcaTrabajada(**datos)


def test_marca_trabajada_guarda_sus_datos_y_es_inmutable():
    m = marca()
    assert m.tope_semanal == Decimal("20")
    with pytest.raises(FrozenInstanceError):
        m.salida = m.entrada  # type: ignore[misc]


def test_horas_trabajadas_son_el_tiempo_real():
    assert marca().horas_trabajadas == Decimal("3.916666666666666666666666667")
    assert marca(entrada=cr(23, 8), salida=cr(23, 10, 30)).horas_trabajadas == Decimal("2.5")


def test_sin_salida_se_paga_hasta_el_fin_programado():
    m = marca(entrada=cr(23, 9), salida=None)
    assert m.sin_salida
    assert m.horas_trabajadas == Decimal("3")


def test_sin_salida_y_entrada_despues_del_fin_no_suma_horas():
    assert marca(entrada=cr(23, 13), salida=None).horas_trabajadas == Decimal("0")


@pytest.mark.parametrize("salida", [cr(23, 8, 5), cr(23, 7)])
def test_marca_rechaza_salida_que_no_es_posterior_a_la_entrada(salida):
    with pytest.raises(MarcaInvalida):
        marca(salida=salida)


def test_marca_rechaza_turno_con_inicio_no_anterior_al_fin():
    with pytest.raises(MarcaInvalida):
        marca(fin_turno=cr(23, 8))


@pytest.mark.parametrize("tope", [Decimal("0"), 20])
def test_marca_rechaza_tope_no_positivo_o_que_no_es_decimal(tope):
    with pytest.raises(MarcaInvalida):
        marca(tope_semanal=tope)


@pytest.mark.parametrize("campo", ["asistente_id", "categoria"])
def test_marca_rechaza_textos_vacios(campo):
    with pytest.raises(MarcaInvalida):
        marca(**{campo: ""})


def test_marca_exige_zona_horaria():
    with pytest.raises(FechaSinZonaHoraria):
        marca(entrada=datetime(2026, 11, 23, 8))


def test_linea_pago_guarda_montos_en_decimal_y_es_inmutable():
    linea = LineaPago("A-1", Decimal("18"), Decimal("2"), Decimal("1"), Decimal("45000.00"),
                      Decimal("2500"), Decimal("50"))
    assert linea.monto == Decimal("45000.00")
    with pytest.raises(FrozenInstanceError):
        linea.monto = Decimal("0")  # type: ignore[misc]
