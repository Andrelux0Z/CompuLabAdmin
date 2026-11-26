"""Franja: intervalo de tiempo semiabierto [inicio, fin) con zona horaria."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from compulab.dominio.compartido.excepciones import FranjaInvalida, exigir_zona_horaria

if TYPE_CHECKING:
    from compulab.dominio.compartido.semana import Semana

_SEGUNDOS_POR_HORA = Decimal(3600)


@dataclass(frozen=True, init=False)
class Franja:
    """Objeto valor inmutable. Incluye el inicio y excluye el fin."""

    _inicio: datetime = field()
    _fin: datetime = field()

    def __init__(self, inicio: datetime, fin: datetime) -> None:
        exigir_zona_horaria(inicio, "inicio")
        exigir_zona_horaria(fin, "fin")
        if not inicio < fin:
            raise FranjaInvalida(f"el inicio ({inicio}) debe ser anterior al fin ({fin})")
        object.__setattr__(self, "_inicio", inicio)
        object.__setattr__(self, "_fin", fin)

    @property
    def inicio(self) -> datetime:
        return self._inicio

    @property
    def fin(self) -> datetime:
        return self._fin

    @property
    def duracion_horas(self) -> Decimal:
        """Duración en horas, como Decimal exacto."""
        segundos = Decimal(str((self._fin - self._inicio).total_seconds()))
        return segundos / _SEGUNDOS_POR_HORA

    def traslapa(self, otra: Franja) -> bool:
        """True si comparten algún instante. Franjas que solo se tocan no se traslapan."""
        return self._inicio < otra._fin and otra._inicio < self._fin

    def contiene(self, objeto: datetime | Franja) -> bool:
        """True si el instante o la franja dada queda completamente dentro de esta."""
        if isinstance(objeto, Franja):
            return self._inicio <= objeto._inicio and objeto._fin <= self._fin
        exigir_zona_horaria(objeto)
        return self._inicio <= objeto < self._fin

    @property
    def semana(self) -> Semana:
        """Semana (lunes a domingo, hora de Costa Rica) en la que empieza la franja."""
        from compulab.dominio.compartido.semana import Semana

        return Semana.de_momento(self._inicio)
