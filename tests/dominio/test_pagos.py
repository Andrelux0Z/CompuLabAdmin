"""Pruebas de los tipos de datos de pagos (solo forma, no tienen lógica)."""

from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA
from compulab.dominio.pagos import LineaPago, MarcaTrabajada


def test_marca_trabajada_guarda_sus_datos_y_es_inmutable():
    marca = MarcaTrabajada(
        asistente_id="A-1",
        categoria="asistente",
        tope_semanal=Decimal("20"),
        inicio_turno=datetime(2026, 11, 23, 8, tzinfo=ZONA_COSTA_RICA),
        entrada=datetime(2026, 11, 23, 8, 5, tzinfo=ZONA_COSTA_RICA),
        salida=datetime(2026, 11, 23, 12, tzinfo=ZONA_COSTA_RICA),
    )
    assert marca.tope_semanal == Decimal("20")
    with pytest.raises(FrozenInstanceError):
        marca.salida = marca.entrada  # type: ignore[misc]


def test_linea_pago_guarda_montos_en_decimal_y_es_inmutable():
    linea = LineaPago("A-1", Decimal("18"), Decimal("2"), Decimal("1"), Decimal("45000.00"),
                      Decimal("2500"), Decimal("50"))
    assert linea.monto == Decimal("45000.00")
    with pytest.raises(FrozenInstanceError):
        linea.monto = Decimal("0")  # type: ignore[misc]
