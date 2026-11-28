"""Reglas de turno (patrón Specification).

Cada regla verifica una condición para asignar un turno y lanza su excepción si no se
cumple. Las mismas reglas sirven para Asignar turno (CU-07) y para aprobar un cambio
(CU-10); una regla nueva es una clase nueva.
"""

from __future__ import annotations

from typing import Protocol

from compulab.dominio.horario.agenda import AgendaSemanal
from compulab.dominio.horario.excepciones import AsistenteInactivo, BloqueNoDisponible
from compulab.dominio.horario.turno import Turno


class ReglaTurno(Protocol):
    def verificar(self, agenda: AgendaSemanal, turno: Turno) -> None: ...


class AsistenteActivo:
    """El asistente no renunció, no fue dado de baja y no terminó su nombramiento."""

    def verificar(self, agenda: AgendaSemanal, turno: Turno) -> None:
        asistente = agenda.asistente
        if not asistente.esta_activo:
            raise AsistenteInactivo(
                f"el asistente {asistente.id} no está activo ({asistente.estado.value})"
            )


class SinTraslape:
    """El turno no choca con otro turno del asistente, en cualquier laboratorio o campus."""

    def verificar(self, agenda: AgendaSemanal, turno: Turno) -> None:
        agenda.verificar_sin_traslape(turno)


class DentroDelTope:
    """Las horas de la semana más las del turno no pasan el tope del asistente."""

    def verificar(self, agenda: AgendaSemanal, turno: Turno) -> None:
        agenda.verificar_dentro_del_tope(turno)


class DentroDeDisponibilidad:
    """El turno cae en un bloque declarado, o el asistente aceptó trabajarlo fuera."""

    def verificar(self, agenda: AgendaSemanal, turno: Turno) -> None:
        if turno.aceptado_fuera_de_disponibilidad:
            return
        if not agenda.asistente.tiene_disponible(turno.franja):
            raise BloqueNoDisponible(
                f"el asistente {agenda.asistente.id} no declaró disponible ese bloque "
                "y no aceptó trabajarlo"
            )


# Orden del flujo principal de CU-07: activo, traslape, tope y disponibilidad.
REGLAS_DE_ASIGNACION: tuple[ReglaTurno, ...] = (
    AsistenteActivo(),
    SinTraslape(),
    DentroDelTope(),
    DentroDeDisponibilidad(),
)
