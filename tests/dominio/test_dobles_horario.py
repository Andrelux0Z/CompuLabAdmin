"""Pruebas de los dobles en memoria de los puertos del horario.

Fijan el comportamiento que el caso de uso espera de cualquier adaptador de esos puertos.
"""

from datetime import date

import pytest

from compulab.dominio.compartido import Franja, Semana
from apoyo_horario import (
    AsistentesEnMemoria,
    CoordinacionesFijas,
    TurnosEnMemoria,
    asistente,
    h,
    turno,
)

SEMANA = Semana(date(2026, 11, 23))


# --- RepositorioTurnos ---


def test_turnos_de_asistente_filtra_por_asistente_y_semana():
    repo = TurnosEnMemoria(
        turno("T1"),
        turno("T2", asistente_id="A2"),
        turno("T3", inicio=h(30, 8), fin=h(30, 10)),  # semana siguiente
    )
    assert [t.id for t in repo.turnos_de_asistente("A1", SEMANA)] == ["T1"]


def test_turnos_de_asistente_incluye_todos_los_laboratorios():
    repo = TurnosEnMemoria(turno("T1"), turno("T2", laboratorio_id="LAB2", inicio=h(24, 8), fin=h(24, 9)))
    assert {t.id for t in repo.turnos_de_asistente("A1", SEMANA)} == {"T1", "T2"}


def test_turnos_de_laboratorio_filtra_por_laboratorio_y_traslape():
    repo = TurnosEnMemoria(
        turno("T1"),
        turno("T2", laboratorio_id="LAB2"),
        turno("T3", inicio=h(23, 12), fin=h(23, 14)),
    )
    resultado = repo.turnos_de_laboratorio("LAB1", Franja(h(23, 9), h(23, 10)))
    assert [t.id for t in resultado] == ["T1"]


def test_guardar_agrega_un_turno_nuevo():
    repo = TurnosEnMemoria()
    repo.guardar(turno("T1"))
    assert [t.id for t in repo.todos] == ["T1"]


def test_guardar_reemplaza_el_turno_con_el_mismo_id():
    repo = TurnosEnMemoria(turno("T1"))
    repo.guardar(turno("T1", laboratorio_id="LAB2"))
    assert len(repo.todos) == 1
    assert repo.todos[0].laboratorio_id == "LAB2"


# --- ConsultaAsistentes ---


def test_obtener_devuelve_el_asistente():
    consulta = AsistentesEnMemoria(asistente("A1"), asistente("A2"))
    assert consulta.obtener("A2").id == "A2"


def test_obtener_asistente_inexistente_falla():
    with pytest.raises(KeyError):
        AsistentesEnMemoria().obtener("A9")


# --- ConsultaCoordinaciones ---


def test_coordinador_de_soporte_puede_modificar_cualquier_laboratorio():
    assert CoordinacionesFijas(soporte=("S1",)).puede_modificar("S1", "LAB7")


def test_coordinador_de_laboratorio_solo_modifica_los_suyos():
    coordinaciones = CoordinacionesFijas(C1=("LAB1",))
    assert coordinaciones.puede_modificar("C1", "LAB1")
    assert not coordinaciones.puede_modificar("C1", "LAB2")


def test_coordinador_desconocido_no_modifica_nada():
    assert not CoordinacionesFijas().puede_modificar("X", "LAB1")
