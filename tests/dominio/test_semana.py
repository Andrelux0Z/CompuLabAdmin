"""Pruebas de Semana."""

from datetime import date, datetime, timedelta

import pytest

from compulab.dominio.compartido import (
    ZONA_COSTA_RICA,
    FechaSinZonaHoraria,
    Semana,
    SemanaInvalida,
)

LUNES = date(2026, 11, 23)


def test_rechaza_un_dia_que_no_es_lunes():
    with pytest.raises(SemanaInvalida):
        Semana(date(2026, 11, 25))


def test_va_de_lunes_a_domingo():
    semana = Semana(LUNES)
    assert semana.lunes == LUNES
    assert semana.domingo == date(2026, 11, 29)


def test_de_fecha_devuelve_la_semana_del_dia():
    assert Semana.de_fecha(date(2026, 11, 29)) == Semana(LUNES)
    assert Semana.de_fecha(LUNES) == Semana(LUNES)


def test_de_momento_rechaza_momento_sin_zona_horaria():
    with pytest.raises(FechaSinZonaHoraria):
        Semana.de_momento(datetime(2026, 11, 25, 9))


def test_franja_va_de_lunes_a_lunes_en_hora_de_costa_rica():
    franja = Semana(LUNES).franja
    assert franja.inicio == datetime(2026, 11, 23, 0, 0, tzinfo=ZONA_COSTA_RICA)
    assert franja.fin == datetime(2026, 11, 30, 0, 0, tzinfo=ZONA_COSTA_RICA)
    assert franja.duracion_horas == 168


def test_zona_de_costa_rica_es_utc_menos_seis():
    assert ZONA_COSTA_RICA.utcoffset(None) == timedelta(hours=-6)


def test_contiene_el_domingo_en_la_noche_pero_no_el_lunes_siguiente():
    semana = Semana(LUNES)
    assert semana.contiene(datetime(2026, 11, 29, 23, 59, tzinfo=ZONA_COSTA_RICA))
    assert not semana.contiene(datetime(2026, 11, 30, 0, 0, tzinfo=ZONA_COSTA_RICA))


def test_siguiente_y_anterior():
    semana = Semana(LUNES)
    assert semana.siguiente() == Semana(date(2026, 11, 30))
    assert semana.anterior() == Semana(date(2026, 11, 16))


def test_una_semana_puede_cruzar_dos_meses():
    semana = Semana(date(2026, 11, 30))
    assert semana.domingo == date(2026, 12, 6)
