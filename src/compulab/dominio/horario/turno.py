"""Turno: un bloque de trabajo en un laboratorio con exactamente un asistente responsable."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja, Semana
from compulab.dominio.horario.excepciones import TurnoInvalido


class EstadoTurno(Enum):
    """Estados del turno (sección 9.4 del documento de diseño)."""

    ASIGNADO = "Asignado"
    OFRECIDO = "Ofrecido"
    CAMBIO_PENDIENTE = "CambioPendiente"
    SIN_ASIGNAR = "SinAsignar"
    EN_CURSO = "EnCurso"
    CUBIERTO = "Cubierto"
    NO_CUBIERTO = "NoCubierto"


def _texto_no_vacio(valor: object) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


class Turno:
    """Entidad identificada por su id. Las invariantes se verifican al construirlo.

    Un turno empieza y termina el mismo día en hora de Costa Rica: no cruza medianoche.
    """

    def __init__(
        self,
        id: str,
        laboratorio_id: str,
        asistente_id: str,
        franja: Franja,
        aceptado_fuera_de_disponibilidad: bool = False,
        estado: EstadoTurno = EstadoTurno.ASIGNADO,
    ) -> None:
        if not _texto_no_vacio(id):
            raise TurnoInvalido("el turno debe tener un id")
        if not _texto_no_vacio(laboratorio_id):
            raise TurnoInvalido("el turno debe tener un laboratorio")
        if not _texto_no_vacio(asistente_id):
            raise TurnoInvalido("el turno debe tener exactamente un asistente responsable")
        if not isinstance(franja, Franja):
            raise TurnoInvalido(f"la franja del turno debe ser una Franja: {franja!r}")
        inicio = franja.inicio.astimezone(ZONA_COSTA_RICA)
        fin = franja.fin.astimezone(ZONA_COSTA_RICA)
        if inicio.date() != fin.date():
            raise TurnoInvalido(
                f"el turno debe empezar y terminar el mismo día: {inicio} a {fin}"
            )
        if not isinstance(aceptado_fuera_de_disponibilidad, bool):
            raise TurnoInvalido("aceptado_fuera_de_disponibilidad debe ser verdadero o falso")
        if not isinstance(estado, EstadoTurno):
            raise TurnoInvalido(f"estado de turno desconocido: {estado!r}")

        self._id = id
        self._laboratorio_id = laboratorio_id
        self._asistente_id = asistente_id
        self._franja = franja
        self._aceptado_fuera_de_disponibilidad = aceptado_fuera_de_disponibilidad
        self._estado = estado

    @property
    def id(self) -> str:
        return self._id

    @property
    def laboratorio_id(self) -> str:
        return self._laboratorio_id

    @property
    def asistente_id(self) -> str:
        return self._asistente_id

    @property
    def franja(self) -> Franja:
        return self._franja

    @property
    def aceptado_fuera_de_disponibilidad(self) -> bool:
        """Verdadero si el asistente aceptó un bloque que no declaró en su postulación."""
        return self._aceptado_fuera_de_disponibilidad

    @property
    def estado(self) -> EstadoTurno:
        return self._estado

    @property
    def duracion_horas(self) -> Decimal:
        return self._franja.duracion_horas

    @property
    def semana(self) -> Semana:
        return self._franja.semana

    def traslapa(self, otro: Turno) -> bool:
        """True si las franjas de los dos turnos comparten algún instante."""
        return self._franja.traslapa(otro._franja)

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Turno):
            return NotImplemented
        return self._id == otro._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return (
            f"Turno(id={self._id!r}, asistente_id={self._asistente_id!r}, "
            f"inicio={self._franja.inicio.isoformat()}, fin={self._franja.fin.isoformat()})"
        )
