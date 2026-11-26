"""Semana: de lunes 00:00 a lunes siguiente 00:00, en la zona horaria de Costa Rica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from compulab.dominio.compartido.excepciones import SemanaInvalida, exigir_zona_horaria
from compulab.dominio.compartido.franja import Franja

# Costa Rica usa UTC-6 todo el año (no tiene horario de verano), por eso un
# desfase fijo basta y no hace falta instalar la base de datos de zonas horarias.
ZONA_COSTA_RICA = timezone(timedelta(hours=-6), "America/Costa_Rica")


@dataclass(frozen=True, init=False)
class Semana:
    """Objeto valor inmutable identificado por su lunes."""

    _lunes: date = field()

    def __init__(self, lunes: date) -> None:
        if isinstance(lunes, datetime) or lunes.weekday() != 0:
            raise SemanaInvalida(f"la semana debe empezar en lunes: {lunes!r}")
        object.__setattr__(self, "_lunes", lunes)

    @classmethod
    def de_fecha(cls, dia: date) -> Semana:
        """Semana que contiene el día dado."""
        return cls(dia - timedelta(days=dia.weekday()))

    @classmethod
    def de_momento(cls, momento: datetime) -> Semana:
        """Semana que contiene el momento, leído en hora de Costa Rica."""
        exigir_zona_horaria(momento)
        return cls.de_fecha(momento.astimezone(ZONA_COSTA_RICA).date())

    @property
    def lunes(self) -> date:
        return self._lunes

    @property
    def domingo(self) -> date:
        return self._lunes + timedelta(days=6)

    @property
    def franja(self) -> Franja:
        """Del lunes a las 00:00 al lunes siguiente a las 00:00, hora de Costa Rica."""
        inicio = datetime.combine(self._lunes, time(0, 0), tzinfo=ZONA_COSTA_RICA)
        return Franja(inicio, inicio + timedelta(days=7))

    def contiene(self, momento: datetime) -> bool:
        return self.franja.contiene(momento)

    def siguiente(self) -> Semana:
        return Semana(self._lunes + timedelta(days=7))

    def anterior(self) -> Semana:
        return Semana(self._lunes - timedelta(days=7))
