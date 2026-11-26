"""Puerto Reloj: el dominio pide la hora actual a través de él, nunca a datetime.now()."""

from datetime import datetime
from typing import Protocol

from compulab.dominio.compartido.excepciones import exigir_zona_horaria


class Reloj(Protocol):
    """Fuente de la hora actual, siempre con zona horaria."""

    def ahora(self) -> datetime: ...


class RelojFijo:
    """Doble de prueba: devuelve siempre el mismo momento."""

    def __init__(self, momento: datetime) -> None:
        exigir_zona_horaria(momento)
        self._momento = momento

    def ahora(self) -> datetime:
        return self._momento
