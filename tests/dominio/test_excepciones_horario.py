"""Pruebas de las excepciones del horario."""

import pytest

from compulab.dominio.compartido import ErrorDeDominio
from compulab.dominio.horario import (
    AsistenteInactivo,
    AsistenteInvalido,
    BloqueNoDisponible,
    LaboratorioNoAutorizado,
    TopeSemanalExcedido,
    TurnoInvalido,
    TurnoTraslapado,
)

EXCEPCIONES_DEL_HORARIO = [
    AsistenteInactivo,
    AsistenteInvalido,
    BloqueNoDisponible,
    LaboratorioNoAutorizado,
    TopeSemanalExcedido,
    TurnoInvalido,
    TurnoTraslapado,
]


@pytest.mark.parametrize("excepcion", EXCEPCIONES_DEL_HORARIO)
def test_todas_heredan_de_error_de_dominio(excepcion):
    assert issubclass(excepcion, ErrorDeDominio)


@pytest.mark.parametrize("excepcion", EXCEPCIONES_DEL_HORARIO)
def test_se_atrapan_como_error_de_dominio(excepcion):
    with pytest.raises(ErrorDeDominio, match="detalle"):
        raise excepcion("detalle")


def test_son_excepciones_distintas():
    assert len(set(EXCEPCIONES_DEL_HORARIO)) == 7
