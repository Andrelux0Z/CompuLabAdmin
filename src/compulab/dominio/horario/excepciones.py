"""Excepciones del horario: las reglas que puede romper una asignación de turno."""

from compulab.dominio.compartido.excepciones import ErrorDeDominio


class AsistenteInvalido(ErrorDeDominio):
    """Los datos del asistente no cumplen sus invariantes."""


class TurnoInvalido(ErrorDeDominio):
    """Los datos del turno no cumplen sus invariantes."""


class AsistenteInactivo(ErrorDeDominio):
    """Se intentó asignar un turno a un asistente que no está activo."""


class LaboratorioNoAutorizado(ErrorDeDominio):
    """El asistente no está autorizado para trabajar en ese laboratorio."""


class BloqueNoDisponible(ErrorDeDominio):
    """El turno cae fuera de la disponibilidad declarada por el asistente."""


class TurnoTraslapado(ErrorDeDominio):
    """El turno se traslapa con otro turno del mismo asistente."""


class TopeSemanalExcedido(ErrorDeDominio):
    """Con el turno, el asistente pasaría su tope de horas de la semana."""
