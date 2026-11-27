"""Pruebas del contrato CU-07: una por poscondición (P) y una por extensión (E).

Los nombres son los de la tabla 11.2 del documento de diseño.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from compulab.aplicacion.asignar_turno import AsignarTurno, SolicitudAsignacion
from compulab.dominio.compartido import FranjaInvalida, Semana
from compulab.dominio.horario import (
    AsistenteInactivo,
    BloqueNoDisponible,
    EstadoAsistente,
    EstadoTurno,
    LaboratorioNoAutorizado,
    TopeSemanalExcedido,
    TurnoTraslapado,
)
from apoyo_horario import (
    AsistentesEnMemoria,
    CoordinacionesFijas,
    TurnosEnMemoria,
    asistente,
    h,
    turno,
)

LUNES_23 = date(2026, 11, 23)
MARTES_24 = date(2026, 11, 24)
SEMANA = Semana(LUNES_23)


class Escenario:
    """A1 está disponible los lunes de 8:00 a 12:00 y tiene tope de 10 h.

    C1 coordina LAB1; S1 es coordinador de soporte.
    """

    def __init__(self, turnos=(), asistentes=None):
        self.turnos = TurnosEnMemoria(*turnos)
        ids = iter(["NUEVO", "OTRO"])
        self.caso = AsignarTurno(
            turnos=self.turnos,
            asistentes=AsistentesEnMemoria(*(asistentes or [asistente("A1")])),
            coordinaciones=CoordinacionesFijas(soporte=("S1",), C1=("LAB1",)),
            nuevo_id=lambda: next(ids),
        )

    def asignar(self, dia=LUNES_23, inicio=time(8), fin=time(12), coordinador="C1",
                laboratorio="LAB1", asistente_id="A1", aceptado=False):
        return self.caso.ejecutar(SolicitudAsignacion(
            coordinador, laboratorio, asistente_id, dia, inicio, fin, aceptado))


# --- Poscondiciones ---


def test_asignar_turno_crea_turno_asignado_con_un_responsable():
    escenario = Escenario()
    creado = escenario.asignar()
    assert creado.id == "NUEVO"                                             # P1
    assert creado.laboratorio_id == "LAB1"
    assert creado.asistente_id == "A1"
    assert creado.franja.inicio == h(23, 8)
    assert creado.franja.fin == h(23, 12)
    assert creado.estado is EstadoTurno.ASIGNADO                            # P2
    assert escenario.turnos.todos == [creado]


def test_asignar_turno_suma_horas_a_la_semana():
    escenario = Escenario(turnos=[turno("T1", inicio=h(24, 8), fin=h(24, 10))],
                          asistentes=[asistente("A1")])
    antes = sum(t.duracion_horas for t in escenario.turnos.turnos_de_asistente("A1", SEMANA))
    creado = escenario.asignar()
    despues = sum(t.duracion_horas for t in escenario.turnos.turnos_de_asistente("A1", SEMANA))
    assert despues - antes == creado.duracion_horas == Decimal("4")       # P3


def test_bloque_no_declarado_con_aceptacion_se_asigna_y_registra():
    escenario = Escenario()
    creado = escenario.asignar(dia=MARTES_24, inicio=time(14), fin=time(16), aceptado=True)
    assert creado.aceptado_fuera_de_disponibilidad                          # P4 / E6
    assert escenario.turnos.todos == [creado]


def test_bloque_declarado_no_registra_aceptacion():
    assert not Escenario().asignar().aceptado_fuera_de_disponibilidad


def test_coordinador_de_soporte_puede_asignar_en_cualquier_laboratorio():
    creado = Escenario().asignar(coordinador="S1", laboratorio="LAB9")
    assert creado.laboratorio_id == "LAB9"


# --- Extensiones: en todas se rechaza y no se guarda nada ---


def test_coordinador_de_otro_laboratorio_es_rechazado():
    escenario = Escenario()
    with pytest.raises(LaboratorioNoAutorizado):                            # E1
        escenario.asignar(laboratorio="LAB2")
    assert escenario.turnos.todos == []


def test_asistente_inactivo_es_rechazado():
    escenario = Escenario(asistentes=[asistente("A1", estado=EstadoAsistente.DADO_DE_BAJA)])
    with pytest.raises(AsistenteInactivo):                                  # E2
        escenario.asignar()
    assert escenario.turnos.todos == []


def test_traslape_en_otro_campus_es_rechazado():
    otro_campus = turno("T1", laboratorio_id="LAB-SAN-JOSE", inicio=h(23, 11), fin=h(23, 13),
                        aceptado=True)
    escenario = Escenario(turnos=[otro_campus])
    with pytest.raises(TurnoTraslapado) as error:                           # E3
        escenario.asignar()
    assert error.value.turno_en_conflicto == otro_campus
    assert escenario.turnos.todos == [otro_campus]


def test_superar_tope_semanal_es_rechazado():
    previo = turno("T1", inicio=h(24, 8), fin=h(24, 16), aceptado=True)   # 8 h de 10
    escenario = Escenario(turnos=[previo])
    with pytest.raises(TopeSemanalExcedido) as error:                       # E4
        escenario.asignar()                                                 # +4 h
    assert error.value.horas_actuales == Decimal("8")
    assert error.value.tope == Decimal("10")
    assert error.value.faltante == Decimal("2")
    assert escenario.turnos.todos == [previo]


def test_bloque_no_declarado_sin_aceptacion_es_rechazado():
    escenario = Escenario()
    with pytest.raises(BloqueNoDisponible):                                 # E5
        escenario.asignar(dia=MARTES_24, inicio=time(14), fin=time(16))
    assert escenario.turnos.todos == []


def test_franja_con_inicio_despues_del_fin_es_invalida():
    escenario = Escenario()
    with pytest.raises(FranjaInvalida):                                     # E7
        escenario.asignar(inicio=time(12), fin=time(8))
    assert escenario.turnos.todos == []


def test_turnos_de_otras_semanas_no_cuentan_para_el_tope():
    semana_anterior = turno("T1", inicio=h(16, 8), fin=h(16, 18), aceptado=True)  # 10 h
    creado = Escenario(turnos=[semana_anterior]).asignar()
    assert creado.duracion_horas == Decimal("4")
