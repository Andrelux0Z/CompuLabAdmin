"""Pruebas de Tarifa, Recargo y de las invariantes de LineaPago."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA, FechaSinZonaHoraria
from compulab.dominio.pagos import (
    LineaPago,
    LineaPagoInvalida,
    Recargo,
    Tarifa,
    TarifaInvalida,
    linea_de_pago,
)


def cr(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre de 2026 en hora de Costa Rica. El 23 es lunes."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


def linea(**cambios) -> LineaPago:
    datos = {
        "asistente_id": "A1",
        "horas_normales": Decimal("10"),
        "horas_con_recargo": Decimal("2"),
        "horas_sobre_tope": Decimal("0"),
        "monto": Decimal("32500"),
        "tarifa": Decimal("2500"),
        "recargo": Decimal("50"),
    }
    datos.update(cambios)
    return LineaPago(**datos)


# --- Tarifa ---


def test_tarifa_valida_expone_sus_datos():
    tarifa = Tarifa("horas-asistente", Decimal("2500"))
    assert tarifa.categoria == "horas-asistente"
    assert tarifa.monto_por_hora == Decimal("2500")


def test_tarifa_acepta_entero_y_lo_guarda_como_decimal():
    assert isinstance(Tarifa("horas-asistente", 2500).monto_por_hora, Decimal)


@pytest.mark.parametrize("monto", [Decimal("0"), Decimal("-1"), Decimal("NaN"), 2500.0, "2500", True])
def test_tarifa_rechaza_monto_no_positivo_o_de_otro_tipo(monto):
    with pytest.raises(TarifaInvalida):
        Tarifa("horas-asistente", monto)


@pytest.mark.parametrize("categoria", ["", "  ", None])
def test_tarifa_rechaza_categoria_vacia(categoria):
    with pytest.raises(TarifaInvalida):
        Tarifa(categoria, Decimal("2500"))


def test_tarifa_es_inmutable():
    with pytest.raises(FrozenInstanceError):
        Tarifa("horas-asistente", 2500)._monto_por_hora = Decimal("1")


# --- Recargo ---


def test_recargo_calcula_su_factor():
    assert Recargo(Decimal("50")).factor == Decimal("1.5")
    assert Recargo(0).factor == Decimal("1")


@pytest.mark.parametrize("porcentaje", [Decimal("-1"), Decimal("Infinity"), 0.5, None])
def test_recargo_rechaza_porcentaje_negativo_o_de_otro_tipo(porcentaje):
    with pytest.raises(TarifaInvalida):
        Recargo(porcentaje)


def test_recargo_no_aplica_a_turno_diurno_entre_semana():
    assert not Recargo(50).aplica_a(cr(23, 8))
    assert not Recargo(50).aplica_a(cr(27, 17, 59))


def test_recargo_aplica_a_turno_que_empieza_a_las_18_o_despues():
    assert Recargo(50).aplica_a(cr(23, 18))
    assert Recargo(50).aplica_a(cr(23, 20, 30))


@pytest.mark.parametrize("dia", [28, 29])  # sábado y domingo
def test_recargo_aplica_en_fin_de_semana(dia):
    assert Recargo(50).aplica_a(cr(dia, 8))


def test_recargo_lee_la_hora_de_costa_rica():
    # 00:00 UTC del martes 24 son las 18:00 del lunes 23 en Costa Rica.
    assert Recargo(50).aplica_a(datetime(2026, 11, 24, 0, 0, tzinfo=timezone.utc))


def test_recargo_exige_zona_horaria():
    with pytest.raises(FechaSinZonaHoraria):
        Recargo(50).aplica_a(datetime(2026, 11, 23, 18, 0))


# --- LineaPago ---


def test_linea_valida_guarda_tarifa_y_recargo_aplicados():
    l = linea()
    assert l.tarifa == Decimal("2500")
    assert l.recargo == Decimal("50")


@pytest.mark.parametrize(
    "campo", ["horas_normales", "horas_con_recargo", "horas_sobre_tope", "monto", "recargo"]
)
def test_linea_rechaza_valores_negativos(campo):
    with pytest.raises(LineaPagoInvalida):
        linea(**{campo: Decimal("-1")})


@pytest.mark.parametrize("tarifa", [Decimal("0"), Decimal("-2500"), 2500])
def test_linea_rechaza_tarifa_no_positiva_o_que_no_es_decimal(tarifa):
    with pytest.raises(LineaPagoInvalida):
        linea(tarifa=tarifa)


def test_linea_rechaza_asistente_vacio():
    with pytest.raises(LineaPagoInvalida):
        linea(asistente_id="")


def test_monto_aplica_tarifa_y_recargo():
    calculada = linea_de_pago(
        "A1",
        horas_normales=Decimal("10"),
        horas_con_recargo=Decimal("4"),
        horas_sobre_tope=Decimal("3"),
        tarifa=Tarifa("horas-asistente", 2500),
        recargo=Recargo(50),
    )
    # 10 × 2500 + 4 × 2500 × 1.5 = 25000 + 15000
    assert calculada.monto == Decimal("40000")
    assert calculada.horas_sobre_tope == Decimal("3")
    assert calculada.tarifa == Decimal("2500")
    assert calculada.recargo == Decimal("50")


def test_horas_sobre_tope_no_suman_al_monto():
    tarifa, recargo = Tarifa("horas-asistente", 2500), Recargo(50)
    sin_exceso = linea_de_pago("A1", Decimal("10"), Decimal("0"), Decimal("0"), tarifa, recargo)
    con_exceso = linea_de_pago("A1", Decimal("10"), Decimal("0"), Decimal("5"), tarifa, recargo)
    assert sin_exceso.monto == con_exceso.monto
