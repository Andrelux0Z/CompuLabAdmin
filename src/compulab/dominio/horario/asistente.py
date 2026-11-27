"""Asistente: estudiante admitido que puede recibir turnos, con su tope y su disponibilidad."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import time
from decimal import Decimal
from enum import Enum

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja
from compulab.dominio.horario.excepciones import AsistenteInvalido


class EstadoAsistente(Enum):
    """Estados del asistente (sección 9.6 del documento de diseño)."""

    ACTIVO = "Activo"
    RENUNCIADO = "Renunciado"
    DADO_DE_BAJA = "DadoDeBaja"
    FINALIZADO = "Finalizado"


@dataclass(frozen=True, init=False)
class BloqueDisponible:
    """Objeto valor: un bloque semanal que el asistente declaró en su postulación.

    El día va de 0 (lunes) a 6 (domingo), igual que date.weekday(). Las horas se leen
    en hora de Costa Rica. Incluye la hora de inicio y excluye la de fin.
    """

    _dia_semana: int = field()
    _inicio: time = field()
    _fin: time = field()

    def __init__(self, dia_semana: int, inicio: time, fin: time) -> None:
        if isinstance(dia_semana, bool) or not isinstance(dia_semana, int):
            raise AsistenteInvalido(f"el día del bloque debe ser un entero: {dia_semana!r}")
        if not 0 <= dia_semana <= 6:
            raise AsistenteInvalido(f"el día del bloque debe ir de 0 a 6: {dia_semana}")
        if inicio.tzinfo is not None or fin.tzinfo is not None:
            raise AsistenteInvalido("las horas del bloque no llevan zona horaria")
        if not inicio < fin:
            raise AsistenteInvalido(f"el inicio del bloque ({inicio}) debe ser anterior al fin ({fin})")
        object.__setattr__(self, "_dia_semana", dia_semana)
        object.__setattr__(self, "_inicio", inicio)
        object.__setattr__(self, "_fin", fin)

    @property
    def dia_semana(self) -> int:
        return self._dia_semana

    @property
    def inicio(self) -> time:
        return self._inicio

    @property
    def fin(self) -> time:
        return self._fin

    def cubre(self, franja: Franja) -> bool:
        """True si la franja cae completa dentro del bloque, en hora de Costa Rica."""
        inicio = franja.inicio.astimezone(ZONA_COSTA_RICA)
        fin = franja.fin.astimezone(ZONA_COSTA_RICA)
        if inicio.weekday() != self._dia_semana:
            return False
        if fin.date() != inicio.date():
            # Una franja que termina a la medianoche solo la cubre un bloque que no
            # tenga fin, y los bloques siempre terminan antes de las 24:00.
            return False
        return self._inicio <= inicio.time() and fin.time() <= self._fin


class Asistente:
    """Entidad identificada por su id. Las invariantes se verifican al construirla."""

    def __init__(
        self,
        id: str,
        categoria: str,
        tope_semanal_horas: Decimal | int,
        bloques: Iterable[BloqueDisponible],
        estado: EstadoAsistente = EstadoAsistente.ACTIVO,
    ) -> None:
        if not isinstance(id, str) or not id.strip():
            raise AsistenteInvalido("el asistente debe tener un id")
        if not isinstance(categoria, str) or not categoria.strip():
            raise AsistenteInvalido("el asistente debe tener una categoría")
        if isinstance(tope_semanal_horas, bool) or not isinstance(tope_semanal_horas, (Decimal, int)):
            raise AsistenteInvalido(
                f"el tope semanal debe ser Decimal o entero: {tope_semanal_horas!r}"
            )
        tope = Decimal(tope_semanal_horas)
        if not tope.is_finite() or tope <= 0:
            raise AsistenteInvalido(f"el tope semanal debe ser mayor que 0: {tope}")
        bloques = tuple(bloques)
        if not bloques:
            raise AsistenteInvalido("el asistente debe tener al menos un bloque disponible")
        if not all(isinstance(bloque, BloqueDisponible) for bloque in bloques):
            raise AsistenteInvalido("los bloques deben ser BloqueDisponible")
        if not isinstance(estado, EstadoAsistente):
            raise AsistenteInvalido(f"estado de asistente desconocido: {estado!r}")

        self._id = id
        self._categoria = categoria
        self._tope_semanal_horas = tope
        self._bloques = bloques
        self._estado = estado

    @property
    def id(self) -> str:
        return self._id

    @property
    def categoria(self) -> str:
        return self._categoria

    @property
    def tope_semanal_horas(self) -> Decimal:
        return self._tope_semanal_horas

    @property
    def bloques(self) -> tuple[BloqueDisponible, ...]:
        return self._bloques

    @property
    def estado(self) -> EstadoAsistente:
        return self._estado

    @property
    def esta_activo(self) -> bool:
        return self._estado is EstadoAsistente.ACTIVO

    def tiene_disponible(self, franja: Franja) -> bool:
        """True si algún bloque declarado cubre la franja completa."""
        return any(bloque.cubre(franja) for bloque in self._bloques)

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Asistente):
            return NotImplemented
        return self._id == otro._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Asistente(id={self._id!r}, estado={self._estado.value})"
