"""Pruebas de la jerarquía de excepciones del dominio."""

import pytest

from compulab.dominio.compartido import (
    ErrorDeDominio,
    FechaSinZonaHoraria,
    FranjaInvalida,
    SemanaInvalida,
)


@pytest.mark.parametrize("excepcion", [FranjaInvalida, SemanaInvalida, FechaSinZonaHoraria])
def test_todas_heredan_de_error_de_dominio(excepcion):
    assert issubclass(excepcion, ErrorDeDominio)
