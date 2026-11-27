"""Pruebas de AgendaSemanal y de las reglas de turno."""

from datetime import date, datetime, time
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja, Semana
from compulab.dominio.horario import (
    REGLAS_DE_ASIGNACION,
    AgendaSemanal,
    Asistente,
    AsistenteActivo,
    AsistenteInactivo,
    BloqueDisponible,
    BloqueNoDisponible,
    DentroDeDisponibilidad,
    DentroDelTope,
    EstadoAsistente,
    EstadoTurno,
    SinTraslape,
    TopeSemanalExcedido,
    Turno,
    TurnoInvalido,
    TurnoTraslapado,
)

SEMANA = Semana(date(2026, 11, 23))  # lunes 23 a domingo 29 de noviembre
LUNES = 0


def cr(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre de 2026 en hora de Costa Rica. El 23 es lunes."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


def asistente(tope=Decimal("10"), estado=EstadoAsistente.ACTIVO) -> Asistente:
    return Asistente(
        id="a-1",
        categoria="horas-asistente",
        tope_semanal_horas=tope,
        bloques=[BloqueDisponible(LUNES, time(8, 0), time(12, 0))],
        estado=estado,
    )


def turno(id_: str, dia: int, desde: int, hasta: int, **cambios) -> Turno:
    datos = {
        "id": id_,
        "laboratorio_id": "lab-1",
        "asistente_id": "a-1",
        "franja": Franja(cr(dia, desde), cr(dia, hasta)),
    }
    datos.update(cambios)
    return Turno(**datos)


def agenda(*turnos, **datos_asistente) -> AgendaSemanal:
    return AgendaSemanal(asistente(**datos_asistente), SEMANA, turnos)


# --- AgendaSemanal: invariantes ---


def test_agenda_vacia_no_tiene_horas():
    assert agenda().horas_programadas() == Decimal("0")


def test_agenda_suma_las_horas_de_sus_turnos():
    a = agenda(turno("t-1", 23, 8, 12), turno("t-2", 24, 14, 16))
    assert a.horas_programadas() == Decimal("6")
    assert len(a.turnos) == 2


def test_agenda_rechaza_turnos_traslapados_al_construirse():
    with pytest.raises(TurnoTraslapado):
        agenda(turno("t-1", 23, 8, 12), turno("t-2", 23, 11, 13))


def test_agenda_rechaza_pasar_el_tope_al_construirse():
    with pytest.raises(TopeSemanalExcedido):
        agenda(turno("t-1", 23, 8, 14), turno("t-2", 24, 8, 13))  # 11 h con tope 10


def test_agenda_acepta_llegar_justo_al_tope():
    a = agenda(turno("t-1", 23, 8, 14), turno("t-2", 24, 8, 12))
    assert a.horas_programadas() == Decimal("10")


def test_agenda_rechaza_turno_de_otro_asistente():
    with pytest.raises(TurnoInvalido):
        agenda(turno("t-1", 23, 8, 12, asistente_id="a-2"))


def test_agenda_rechaza_turno_de_otra_semana():
    with pytest.raises(TurnoInvalido):
        agenda(turno("t-1", 30, 8, 12))


def test_agenda_rechaza_el_mismo_turno_dos_veces():
    a = agenda(turno("t-1", 23, 8, 12))
    with pytest.raises(TurnoInvalido):
        a.agregar(turno("t-1", 23, 8, 12))


def test_agregar_que_falla_no_cambia_la_agenda():
    a = agenda(turno("t-1", 23, 8, 12))
    with pytest.raises(TurnoTraslapado):
        a.agregar(turno("t-2", 23, 10, 11))
    assert [t.id for t in a.turnos] == ["t-1"]


def test_turno_sin_asignar_no_ocupa_ni_suma_horas():
    a = agenda(turno("t-1", 23, 8, 12, estado=EstadoTurno.SIN_ASIGNAR))
    assert a.horas_programadas() == Decimal("0")
    a.agregar(turno("t-2", 23, 8, 12))
    assert a.horas_programadas() == Decimal("4")


def test_turnos_de_la_agenda_no_se_modifican_desde_afuera():
    a = agenda(turno("t-1", 23, 8, 12))
    assert isinstance(a.turnos, tuple)


# --- Reglas: AsistenteActivo ---


def test_asistente_activo_pasa():
    AsistenteActivo().verificar(agenda(), turno("t-1", 23, 8, 12))


@pytest.mark.parametrize(
    "estado",
    [EstadoAsistente.RENUNCIADO, EstadoAsistente.DADO_DE_BAJA, EstadoAsistente.FINALIZADO],
)
def test_asistente_no_activo_es_rechazado(estado):
    with pytest.raises(AsistenteInactivo):
        AsistenteActivo().verificar(agenda(estado=estado), turno("t-1", 23, 8, 12))


# --- Reglas: SinTraslape ---


def test_sin_traslape_pasa_si_no_choca():
    SinTraslape().verificar(agenda(turno("t-1", 23, 8, 12)), turno("t-2", 23, 12, 14))


def test_sin_traslape_indica_el_turno_en_conflicto():
    existente = turno("t-1", 23, 8, 12)
    with pytest.raises(TurnoTraslapado) as error:
        SinTraslape().verificar(agenda(existente), turno("t-2", 23, 11, 13))
    assert error.value.turno_en_conflicto == existente


def test_sin_traslape_cuenta_turnos_de_otros_laboratorios():
    existente = turno("t-1", 23, 8, 12, laboratorio_id="lab-otro-campus")
    with pytest.raises(TurnoTraslapado):
        SinTraslape().verificar(agenda(existente), turno("t-2", 23, 9, 10))


# --- Reglas: DentroDelTope ---


def test_dentro_del_tope_pasa_si_alcanza():
    DentroDelTope().verificar(agenda(turno("t-1", 23, 8, 14)), turno("t-2", 24, 8, 12))


def test_dentro_del_tope_indica_horas_actuales_tope_y_faltante():
    with pytest.raises(TopeSemanalExcedido) as error:
        DentroDelTope().verificar(agenda(turno("t-1", 23, 8, 16)), turno("t-2", 24, 8, 12))
    assert error.value.horas_actuales == Decimal("8")
    assert error.value.tope == Decimal("10")
    assert error.value.faltante == Decimal("2")


# --- Reglas: DentroDeDisponibilidad ---


def test_dentro_de_disponibilidad_pasa_en_bloque_declarado():
    DentroDeDisponibilidad().verificar(agenda(), turno("t-1", 23, 9, 11))


def test_bloque_no_declarado_sin_aceptacion_es_rechazado():
    with pytest.raises(BloqueNoDisponible):
        DentroDeDisponibilidad().verificar(agenda(), turno("t-1", 24, 9, 11))


def test_bloque_no_declarado_con_aceptacion_pasa():
    t = turno("t-1", 24, 9, 11, aceptado_fuera_de_disponibilidad=True)
    DentroDeDisponibilidad().verificar(agenda(), t)


# --- Conjunto de reglas de CU-07 ---


def test_reglas_de_asignacion_siguen_el_orden_del_flujo_principal():
    tipos = [type(regla) for regla in REGLAS_DE_ASIGNACION]
    assert tipos == [AsistenteActivo, SinTraslape, DentroDelTope, DentroDeDisponibilidad]


def test_las_reglas_no_modifican_la_agenda():
    a = agenda(turno("t-1", 23, 8, 12))
    nuevo = turno("t-2", 23, 13, 14, aceptado_fuera_de_disponibilidad=True)
    for regla in REGLAS_DE_ASIGNACION:
        regla.verificar(a, nuevo)
    assert [t.id for t in a.turnos] == ["t-1"]
