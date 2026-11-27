"""Excepciones de las reglas de máquinas y reservas (contrato CU-13)."""

from compulab.dominio.compartido.excepciones import ErrorDeDominio


class LaboratorioInvalido(ErrorDeDominio):
    """El laboratorio no cumple sus invariantes."""


class MaquinaInvalida(ErrorDeDominio):
    """La máquina no cumple sus invariantes."""


class TransicionInvalida(ErrorDeDominio):
    """Se intentó un cambio de estado que la máquina o la reserva no permite."""


class DuracionExcedida(ErrorDeDominio):
    """E1: la reserva dura más de 2 horas."""


class LaboratorioCerrado(ErrorDeDominio):
    """E2: alguna parte de la franja no está cubierta por un turno."""


class MaquinaFueraDeServicio(ErrorDeDominio):
    """E3: la máquina está marcada fuera de servicio."""


class MaquinaOcupada(ErrorDeDominio):
    """E4: la máquina ya tiene una reserva vigente que se traslapa."""


class ReservaActivaExistente(ErrorDeDominio):
    """E5: el estudiante ya tiene una reserva activa."""


class LimiteSemanalExcedido(ErrorDeDominio):
    """E6: el estudiante superaría 6 horas reservadas en la semana."""
