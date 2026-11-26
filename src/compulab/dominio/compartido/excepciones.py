"""Excepciones base del dominio."""

from datetime import datetime


class ErrorDeDominio(Exception):
    """Raíz de todos los errores que lanzan las reglas del dominio."""


class FranjaInvalida(ErrorDeDominio):
    """La franja no cumple que el inicio sea anterior al fin."""


class SemanaInvalida(ErrorDeDominio):
    """La semana no empieza en lunes."""


class FechaSinZonaHoraria(ErrorDeDominio):
    """Se recibió una fecha y hora sin zona horaria."""


def exigir_zona_horaria(momento: datetime, nombre: str = "momento") -> None:
    """Lanza FechaSinZonaHoraria si el momento no trae zona horaria."""
    if momento.tzinfo is None or momento.utcoffset() is None:
        raise FechaSinZonaHoraria(f"{nombre} debe tener zona horaria: {momento!r}")
