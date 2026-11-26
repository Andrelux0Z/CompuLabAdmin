"""Núcleo compartido del dominio: tiempo, franjas, semanas y excepciones base."""

from compulab.dominio.compartido.excepciones import (
    ErrorDeDominio,
    FechaSinZonaHoraria,
    FranjaInvalida,
    SemanaInvalida,
)
from compulab.dominio.compartido.franja import Franja
from compulab.dominio.compartido.reloj import Reloj, RelojFijo
from compulab.dominio.compartido.semana import ZONA_COSTA_RICA, Semana

__all__ = [
    "ErrorDeDominio",
    "FechaSinZonaHoraria",
    "Franja",
    "FranjaInvalida",
    "Reloj",
    "RelojFijo",
    "Semana",
    "SemanaInvalida",
    "ZONA_COSTA_RICA",
]
