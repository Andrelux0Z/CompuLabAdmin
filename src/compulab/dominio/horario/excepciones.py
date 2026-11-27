"""Excepciones del horario: las reglas que puede romper una asignación de turno."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from compulab.dominio.compartido.excepciones import ErrorDeDominio

if TYPE_CHECKING:
    from compulab.dominio.horario.turno import Turno


class AsistenteInvalido(ErrorDeDominio):
    """Los datos del asistente no cumplen sus invariantes."""


class TurnoInvalido(ErrorDeDominio):
    """Los datos del turno no cumplen sus invariantes."""


class AsistenteInactivo(ErrorDeDominio):
    """Se intentó asignar un turno a un asistente que no está activo."""


class LaboratorioNoAutorizado(ErrorDeDominio):
    """El coordinador no puede modificar el horario de ese laboratorio."""


class BloqueNoDisponible(ErrorDeDominio):
    """El turno cae fuera de la disponibilidad declarada y el asistente no lo aceptó."""


class TurnoTraslapado(ErrorDeDominio):
    """El turno se traslapa con otro turno del mismo asistente."""

    def __init__(self, mensaje: str, *, turno_en_conflicto: Turno | None = None) -> None:
        super().__init__(mensaje)
        self.turno_en_conflicto = turno_en_conflicto


class TopeSemanalExcedido(ErrorDeDominio):
    """Con el turno, el asistente pasaría su tope de horas de la semana."""

    def __init__(
        self,
        mensaje: str,
        *,
        horas_actuales: Decimal | None = None,
        tope: Decimal | None = None,
        faltante: Decimal | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.horas_actuales = horas_actuales
        self.tope = tope
        self.faltante = faltante
