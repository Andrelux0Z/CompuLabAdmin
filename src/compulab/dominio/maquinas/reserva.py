from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from compulab.dominio.compartido.franja import Franja
from compulab.dominio.maquinas.excepciones import DuracionExcedida, TransicionInvalida


class EstadoReserva(Enum):
    ACTIVA = "ACTIVA"
    EN_USO = "EN_USO"
    LIBERADA = "LIBERADA"
    CANCELADA = "CANCELADA"
    FINALIZADA = "FINALIZADA"


class Reserva:
    """Reserva de una máquina por un estudiante (patrón State en sus transiciones)."""

    DURACION_MAXIMA = timedelta(hours=2)
    TOLERANCIA = timedelta(minutes=15)

    def __init__(self, id: str, estudiante_id: str, maquina_id: str, franja: Franja,
                 estado: EstadoReserva = EstadoReserva.ACTIVA) -> None:
        if not id or not estudiante_id or not maquina_id:
            raise ValueError("La reserva necesita id, estudiante y máquina")
        if franja.fin - franja.inicio > self.DURACION_MAXIMA:
            raise DuracionExcedida(
                f"Una reserva no puede pasar de 2 h (pidió {franja.duracion_horas:g} h)")
        self._id = id
        self._estudiante_id = estudiante_id
        self._maquina_id = maquina_id
        self._franja = franja
        self._estado = estado
        self._motivo_cancelacion: str | None = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def estudiante_id(self) -> str:
        return self._estudiante_id

    @property
    def maquina_id(self) -> str:
        return self._maquina_id

    @property
    def franja(self) -> Franja:
        return self._franja

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def motivo_cancelacion(self) -> str | None:
        return self._motivo_cancelacion

    @property
    def limite_para_presentarse(self) -> datetime:
        return self._franja.inicio + self.TOLERANCIA

    def esta_vigente(self) -> bool:
        """Activa o en uso: ocupa la máquina y cuenta como 'reserva activa'."""
        return self._estado in (EstadoReserva.ACTIVA, EstadoReserva.EN_USO)

    def cuenta_para_limite_semanal(self) -> bool:
        return self._estado in (EstadoReserva.ACTIVA, EstadoReserva.EN_USO,
                                EstadoReserva.FINALIZADA)

    def horas(self) -> Decimal:
        return self._franja.duracion_horas

    def presentarse(self, ahora: datetime) -> None:
        if self._estado is not EstadoReserva.ACTIVA:
            raise TransicionInvalida("Solo una reserva activa admite presentarse")
        if ahora > self.limite_para_presentarse:
            raise TransicionInvalida("Pasaron los 15 minutos de tolerancia")
        self._estado = EstadoReserva.EN_USO

    def liberar_si_no_se_presento(self, ahora: datetime) -> bool:
        """Libera la máquina si pasaron 15 min sin presentarse. Devuelve si la liberó."""
        if self._estado is EstadoReserva.ACTIVA and ahora >= self.limite_para_presentarse:
            self._estado = EstadoReserva.LIBERADA
            return True
        return False

    def cancelar(self, motivo: str) -> None:
        if self._estado is not EstadoReserva.ACTIVA:
            raise TransicionInvalida("Solo se cancela una reserva activa")
        self._estado = EstadoReserva.CANCELADA
        self._motivo_cancelacion = motivo

    def finalizar(self) -> None:
        if self._estado is not EstadoReserva.EN_USO:
            raise TransicionInvalida("Solo finaliza una reserva en uso")
        self._estado = EstadoReserva.FINALIZADA
