"""Pruebas de Turno."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja, Semana
from compulab.dominio.horario import EstadoTurno, Turno, TurnoInvalido


def cr(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre de 2026 en hora de Costa Rica. El 23 es lunes."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


def turno(**cambios) -> Turno:
    datos = {
        "id": "t-1",
        "laboratorio_id": "lab-1",
        "asistente_id": "a-1",
        "franja": Franja(cr(23, 8), cr(23, 12)),
    }
    datos.update(cambios)
    return Turno(**datos)


# --- Invariantes ---


def test_turno_valido_expone_sus_datos():
    t = turno()
    assert t.id == "t-1"
    assert t.laboratorio_id == "lab-1"
    assert t.asistente_id == "a-1"
    assert t.franja == Franja(cr(23, 8), cr(23, 12))
    assert t.aceptado_fuera_de_disponibilidad is False


def test_turno_nuevo_queda_asignado():
    assert turno().estado is EstadoTurno.ASIGNADO


@pytest.mark.parametrize("asistente_id", ["", "   ", None, ["a-1", "a-2"]])
def test_turno_rechaza_sin_exactamente_un_asistente(asistente_id):
    with pytest.raises(TurnoInvalido):
        turno(asistente_id=asistente_id)


@pytest.mark.parametrize("campo", ["id", "laboratorio_id"])
def test_turno_rechaza_campos_vacios(campo):
    with pytest.raises(TurnoInvalido):
        turno(**{campo: ""})


def test_turno_rechaza_franja_que_no_es_franja():
    with pytest.raises(TurnoInvalido):
        turno(franja=(cr(23, 8), cr(23, 12)))


def test_turno_rechaza_cruzar_medianoche():
    with pytest.raises(TurnoInvalido):
        turno(franja=Franja(cr(23, 22), cr(24, 2)))


def test_turno_rechaza_terminar_a_medianoche_del_dia_siguiente():
    with pytest.raises(TurnoInvalido):
        turno(franja=Franja(cr(23, 20), cr(24, 0)))


def test_turno_usa_el_dia_de_costa_rica_y_no_el_de_utc():
    # 18:00 a 23:00 en Costa Rica es 00:00 a 05:00 UTC del día siguiente: es válido.
    assert turno(franja=Franja(cr(23, 18), cr(23, 23))).duracion_horas == Decimal("5")
    # 20:00 a 04:00 UTC parece otro día en UTC, pero en Costa Rica cruza medianoche.
    inicio = datetime(2026, 11, 24, 4, 0, tzinfo=timezone.utc)  # 22:00 del 23 en Costa Rica
    with pytest.raises(TurnoInvalido):
        turno(franja=Franja(inicio, inicio + timedelta(hours=4)))


def test_turno_rechaza_aceptacion_que_no_es_booleana():
    with pytest.raises(TurnoInvalido):
        turno(aceptado_fuera_de_disponibilidad="sí")


def test_turno_rechaza_estado_desconocido():
    with pytest.raises(TurnoInvalido):
        turno(estado="Asignado")


# --- Comportamiento ---


def test_turno_registra_aceptacion_fuera_de_disponibilidad():
    assert turno(aceptado_fuera_de_disponibilidad=True).aceptado_fuera_de_disponibilidad


def test_duracion_en_horas():
    assert turno(franja=Franja(cr(23, 8), cr(23, 10, 30))).duracion_horas == Decimal("2.5")


def test_semana_del_turno():
    assert turno(franja=Franja(cr(29, 8), cr(29, 12))).semana == Semana(date(2026, 11, 23))


def test_turnos_traslapados():
    otro = turno(id="t-2", franja=Franja(cr(23, 11), cr(23, 14)))
    assert turno().traslapa(otro)


def test_turnos_que_solo_se_tocan_no_se_traslapan():
    otro = turno(id="t-2", franja=Franja(cr(23, 12), cr(23, 14)))
    assert not turno().traslapa(otro)


def test_atributos_son_de_solo_lectura():
    with pytest.raises(AttributeError):
        turno().asistente_id = "a-2"


def test_turnos_con_el_mismo_id_son_iguales():
    assert turno() == turno(asistente_id="a-2")
    assert hash(turno()) == hash(turno(laboratorio_id="lab-2"))


def test_turnos_con_distinto_id_son_distintos():
    assert turno() != turno(id="t-2")
