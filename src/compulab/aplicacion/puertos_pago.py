"""Puertos que usa el caso de uso Cerrar mes."""
from __future__ import annotations

from typing import Protocol, Sequence

from compulab.dominio.pagos import LineaPago


class ExportadorPago(Protocol):
    def exportar(self, anio: int, mes: int, lineas: Sequence[LineaPago]) -> str:
        """Genera el archivo del cierre para Becas/Planilla y devuelve su ubicación."""
        ...
