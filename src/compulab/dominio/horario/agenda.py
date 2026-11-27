"""AgendaSemanal: agregado con los turnos de un asistente en una semana."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from compulab.dominio.compartido import Semana
from compulab.dominio.horario.asistente import Asistente
from compulab.dominio.horario.excepciones import (
    TopeSemanalExcedido,
    TurnoInvalido,
    TurnoTraslapado,
)
from compulab.dominio.horario.turno import EstadoTurno, Turno

# Un turno sin asignar ya no tiene responsable: no ocupa la agenda ni suma horas.
_ESTADOS_QUE_NO_OCUPAN = frozenset({EstadoTurno.SIN_ASIGNAR})


class AgendaSemanal:
    """Protege como unidad las invariantes de traslape y tope (patrón Aggregate).

    Invariantes: todos los turnos son del asistente y empiezan en la semana; ningún
    par de turnos se traslapa; la suma de horas no pasa el tope semanal.
    """

    def __init__(self, asistente: Asistente, semana: Semana, turnos: Iterable[Turno] = ()) -> None:
        if not isinstance(asistente, Asistente):
            raise TypeError(f"la agenda necesita un Asistente: {asistente!r}")
        if not isinstance(semana, Semana):
            raise TypeError(f"la agenda necesita una Semana: {semana!r}")
        self._asistente = asistente
        self._semana = semana
        self._turnos: list[Turno] = []
        for turno in turnos:
            self.agregar(turno)

    @property
    def asistente(self) -> Asistente:
        return self._asistente

    @property
    def semana(self) -> Semana:
        return self._semana

    @property
    def turnos(self) -> tuple[Turno, ...]:
        return tuple(self._turnos)

    def horas_programadas(self) -> Decimal:
        """Suma de las horas de los turnos que ocupan la agenda."""
        return sum((t.duracion_horas for t in self._turnos_que_ocupan()), Decimal(0))

    def turno_en_conflicto(self, turno: Turno) -> Turno | None:
        """Primer turno de la agenda que se traslapa con el dado, o None."""
        for existente in self._turnos_que_ocupan():
            if existente != turno and existente.traslapa(turno):
                return existente
        return None

    def verificar_sin_traslape(self, turno: Turno) -> None:
        conflicto = self.turno_en_conflicto(turno)
        if conflicto is not None:
            raise TurnoTraslapado(
                f"el turno se traslapa con {conflicto.id} "
                f"({conflicto.franja.inicio:%Y-%m-%d %H:%M} a {conflicto.franja.fin:%H:%M})",
                turno_en_conflicto=conflicto,
            )

    def verificar_dentro_del_tope(self, turno: Turno) -> None:
        actuales = self.horas_programadas()
        tope = self._asistente.tope_semanal_horas
        total = actuales + turno.duracion_horas
        if total > tope:
            faltante = total - tope
            raise TopeSemanalExcedido(
                f"con el turno el asistente tendría {total} h y su tope es {tope} h "
                f"(lleva {actuales} h; sobran {faltante} h)",
                horas_actuales=actuales,
                tope=tope,
                faltante=faltante,
            )

    def agregar(self, turno: Turno) -> None:
        """Agrega el turno si respeta todas las invariantes; si no, no cambia nada."""
        if not isinstance(turno, Turno):
            raise TurnoInvalido(f"solo se agregan turnos: {turno!r}")
        if turno.asistente_id != self._asistente.id:
            raise TurnoInvalido(
                f"el turno {turno.id} es de {turno.asistente_id}, no de {self._asistente.id}"
            )
        if turno.semana != self._semana:
            raise TurnoInvalido(f"el turno {turno.id} no empieza en la semana del {self._semana.lunes}")
        if turno in self._turnos:
            raise TurnoInvalido(f"el turno {turno.id} ya está en la agenda")
        if turno.estado not in _ESTADOS_QUE_NO_OCUPAN:
            self.verificar_sin_traslape(turno)
            self.verificar_dentro_del_tope(turno)
        self._turnos.append(turno)

    def _turnos_que_ocupan(self) -> Iterable[Turno]:
        return (t for t in self._turnos if t.estado not in _ESTADOS_QUE_NO_OCUPAN)
