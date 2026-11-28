"""Puertos del módulo de horario. Los adaptadores reales viven en infraestructura."""

from __future__ import annotations

from typing import Protocol

from compulab.dominio.compartido import Franja, Semana
from compulab.dominio.horario.asistente import Asistente
from compulab.dominio.horario.turno import Turno


class RepositorioTurnos(Protocol):
    def turnos_de_asistente(self, asistente_id: str, semana: Semana) -> list[Turno]:
        """Turnos del asistente que empiezan en la semana, en cualquier laboratorio o campus."""
        ...

    def turnos_de_laboratorio(self, laboratorio_id: str, franja: Franja) -> list[Turno]:
        """Turnos del laboratorio cuya franja se traslapa con la dada."""
        ...

    def guardar(self, turno: Turno) -> None:
        """Crea el turno o reemplaza el que tenga el mismo id."""
        ...


class ConsultaAsistentes(Protocol):
    def obtener(self, asistente_id: str) -> Asistente:
        """Asistente con ese id. Que exista es precondición de quien llama."""
        ...


class ConsultaCoordinaciones(Protocol):
    def puede_modificar(self, coordinador_id: str, laboratorio_id: str) -> bool:
        """True si el coordinador puede cambiar el horario de ese laboratorio.

        El coordinador de soporte puede modificar todos; el de laboratorio, solo el suyo.
        """
        ...
