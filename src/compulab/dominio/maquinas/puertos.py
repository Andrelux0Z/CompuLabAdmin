"""Puertos del módulo de máquinas."""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from compulab.dominio.compartido.franja import Franja
from compulab.dominio.maquinas.maquina import Maquina
from compulab.dominio.maquinas.reserva import Reserva


class RepositorioMaquinas(Protocol):
    def obtener(self, maquina_id: str) -> Maquina: ...


class RepositorioReservas(Protocol):
    def de_maquina(self, maquina_id: str, franja: Franja) -> list[Reserva]:
        """Reservas de la máquina cuya franja se traslapa con la dada."""
        ...

    def del_estudiante(self, estudiante_id: str) -> list[Reserva]:
        """Reservas del estudiante vigentes o de la semana en curso."""
        ...

    def guardar(self, reserva: Reserva) -> None: ...


class ConsultaFranjasCubiertas(Protocol):
    def cubre(self, laboratorio_id: str, franja: Franja) -> bool:
        """True si toda la franja está cubierta por turnos asignados (laboratorio abierto)."""
        ...


class ProgramadorLiberaciones(Protocol):
    def programar_liberacion(self, reserva_id: str, momento: datetime) -> None:
        """Pide que en `momento` se libere la reserva si nadie se presentó."""
        ...
