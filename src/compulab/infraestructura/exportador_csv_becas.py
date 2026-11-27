"""Adaptador de ExportadorPago: archivo CSV que se entrega a Becas.

Formato supuesto (pendiente de confirmar con Becas): UTF-8, separador coma,
una fila por asistente ordenada por id, horas y montos con dos decimales."""
from __future__ import annotations

import csv
import io
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Sequence

from compulab.dominio.pagos import LineaPago

COLUMNAS = ["anio", "mes", "asistente_id", "horas_normales", "horas_con_recargo",
            "horas_sobre_tope", "monto"]
_DOS_DECIMALES = Decimal("0.01")


def _dec(valor: Decimal) -> str:
    return str(Decimal(valor).quantize(_DOS_DECIMALES, rounding=ROUND_HALF_UP))


class ExportadorCsvBecas:
    def __init__(self, carpeta: Path) -> None:
        self._carpeta = Path(carpeta)

    @staticmethod
    def nombre_archivo(anio: int, mes: int) -> str:
        return f"becas_{anio}_{mes:02d}.csv"

    @staticmethod
    def contenido(anio: int, mes: int, lineas: Sequence[LineaPago]) -> str:
        buffer = io.StringIO()
        escritor = csv.writer(buffer, lineterminator="\n")
        escritor.writerow(COLUMNAS)
        for linea in sorted(lineas, key=lambda l: l.asistente_id):
            escritor.writerow([anio, mes, linea.asistente_id, _dec(linea.horas_normales),
                               _dec(linea.horas_con_recargo), _dec(linea.horas_sobre_tope),
                               _dec(linea.monto)])
        return buffer.getvalue()

    def exportar(self, anio: int, mes: int, lineas: Sequence[LineaPago]) -> str:
        self._carpeta.mkdir(parents=True, exist_ok=True)
        ruta = self._carpeta / self.nombre_archivo(anio, mes)
        if ruta.exists():
            raise FileExistsError(f"Ya existe {ruta}: un mes cerrado no se vuelve a exportar")
        ruta.write_text(self.contenido(anio, mes, lineas), encoding="utf-8")
        return str(ruta)
