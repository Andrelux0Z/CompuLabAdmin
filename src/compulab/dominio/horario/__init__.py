"""Horario: asistentes, turnos y las reglas para asignarlos."""

from compulab.dominio.horario.excepciones import (
    AsistenteInactivo,
    AsistenteInvalido,
    BloqueNoDisponible,
    LaboratorioNoAutorizado,
    TopeSemanalExcedido,
    TurnoInvalido,
    TurnoTraslapado,
)

__all__ = [
    "AsistenteInactivo",
    "AsistenteInvalido",
    "BloqueNoDisponible",
    "LaboratorioNoAutorizado",
    "TopeSemanalExcedido",
    "TurnoInvalido",
    "TurnoTraslapado",
]
