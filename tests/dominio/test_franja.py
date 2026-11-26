"""Pruebas de Franja."""

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from compulab.dominio.compartido import (
    ZONA_COSTA_RICA,
    FechaSinZonaHoraria,
    Franja,
    FranjaInvalida,
    Semana,
)


def cr(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre de 2026 en hora de Costa Rica."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


def test_rechaza_inicio_igual_al_fin():
    with pytest.raises(FranjaInvalida):
        Franja(cr(23, 8), cr(23, 8))


def test_rechaza_inicio_posterior_al_fin():
    with pytest.raises(FranjaInvalida):
        Franja(cr(23, 10), cr(23, 8))


def test_rechaza_fechas_sin_zona_horaria():
    with pytest.raises(FechaSinZonaHoraria):
        Franja(datetime(2026, 11, 23, 8), datetime(2026, 11, 23, 10))


def test_expone_inicio_y_fin():
    franja = Franja(cr(23, 8), cr(23, 10))
    assert franja.inicio == cr(23, 8)
    assert franja.fin == cr(23, 10)


def test_es_inmutable():
    franja = Franja(cr(23, 8), cr(23, 10))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        franja.inicio = cr(23, 9)  # type: ignore[misc]


def test_dos_franjas_iguales_son_iguales():
    assert Franja(cr(23, 8), cr(23, 10)) == Franja(cr(23, 8), cr(23, 10))


def test_duracion_en_horas_es_decimal_exacto():
    assert Franja(cr(23, 8), cr(23, 10, 30)).duracion_horas == Decimal("2.5")


def test_duracion_de_veinte_minutos():
    assert Franja(cr(23, 8), cr(23, 8, 20)).duracion_horas.quantize(Decimal("0.0001")) == Decimal("0.3333")


def test_traslapa_cuando_comparten_tiempo():
    assert Franja(cr(23, 8), cr(23, 10)).traslapa(Franja(cr(23, 9), cr(23, 11)))


def test_no_traslapa_si_solo_se_tocan():
    assert not Franja(cr(23, 8), cr(23, 10)).traslapa(Franja(cr(23, 10), cr(23, 12)))


def test_no_traslapa_si_estan_separadas():
    assert not Franja(cr(23, 8), cr(23, 9)).traslapa(Franja(cr(23, 10), cr(23, 11)))


def test_traslapa_con_zonas_horarias_distintas():
    utc = Franja(datetime(2026, 11, 23, 15, tzinfo=timezone.utc), datetime(2026, 11, 23, 16, tzinfo=timezone.utc))
    assert Franja(cr(23, 8), cr(23, 10)).traslapa(utc)  # 15:00 UTC = 09:00 en Costa Rica


def test_contiene_el_inicio_pero_no_el_fin():
    franja = Franja(cr(23, 8), cr(23, 10))
    assert franja.contiene(cr(23, 8))
    assert not franja.contiene(cr(23, 10))


def test_contiene_una_franja_interna():
    assert Franja(cr(23, 8), cr(23, 12)).contiene(Franja(cr(23, 9), cr(23, 10)))


def test_no_contiene_una_franja_que_se_sale():
    assert not Franja(cr(23, 8), cr(23, 10)).contiene(Franja(cr(23, 9), cr(23, 11)))


def test_contiene_rechaza_momento_sin_zona_horaria():
    with pytest.raises(FechaSinZonaHoraria):
        Franja(cr(23, 8), cr(23, 10)).contiene(datetime(2026, 11, 23, 9))


def test_semana_de_la_franja_empieza_en_lunes():
    assert Franja(cr(26, 8), cr(26, 10)).semana == Semana(date(2026, 11, 23))


def test_semana_se_calcula_en_hora_de_costa_rica():
    # Lunes 30 a las 03:00 UTC todavía es domingo 29 a las 21:00 en Costa Rica.
    inicio = datetime(2026, 11, 30, 3, tzinfo=timezone.utc)
    assert Franja(inicio, inicio + timedelta(hours=1)).semana == Semana(date(2026, 11, 23))
