"""Pruebas de las excepciones del pago."""

import pytest

from compulab.dominio.compartido import ErrorDeDominio
from compulab.dominio.pagos import (
    CierreInmutable,
    LineaPagoInvalida,
    MarcaInvalida,
    MesNoTerminado,
    MesYaCerrado,
    TarifaInvalida,
    TarifaNoConfigurada,
)

EXCEPCIONES_DEL_PAGO = [
    CierreInmutable,
    LineaPagoInvalida,
    MarcaInvalida,
    MesNoTerminado,
    MesYaCerrado,
    TarifaInvalida,
    TarifaNoConfigurada,
]


@pytest.mark.parametrize("excepcion", EXCEPCIONES_DEL_PAGO)
def test_todas_heredan_de_error_de_dominio(excepcion):
    assert issubclass(excepcion, ErrorDeDominio)


@pytest.mark.parametrize("excepcion", EXCEPCIONES_DEL_PAGO)
def test_se_atrapan_como_error_de_dominio(excepcion):
    with pytest.raises(ErrorDeDominio, match="detalle"):
        raise excepcion("detalle")


def test_son_excepciones_distintas():
    assert len(set(EXCEPCIONES_DEL_PAGO)) == 7
