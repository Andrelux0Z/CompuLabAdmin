"""Pruebas del puerto Reloj y su doble RelojFijo."""

from datetime import datetime

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA, FechaSinZonaHoraria, Reloj, RelojFijo

MOMENTO = datetime(2026, 11, 25, 21, 0, tzinfo=ZONA_COSTA_RICA)


def test_reloj_fijo_devuelve_siempre_el_mismo_momento():
    reloj = RelojFijo(MOMENTO)
    assert reloj.ahora() == MOMENTO
    assert reloj.ahora() == MOMENTO


def test_reloj_fijo_cumple_el_puerto_reloj():
    reloj: Reloj = RelojFijo(MOMENTO)
    assert reloj.ahora().tzinfo is not None


def test_reloj_fijo_rechaza_momento_sin_zona_horaria():
    with pytest.raises(FechaSinZonaHoraria):
        RelojFijo(datetime(2026, 11, 25, 21, 0))
