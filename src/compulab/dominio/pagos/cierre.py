"""CierreMensual: instantánea inmutable del pago de un mes (ADR-05).

Un mes cerrado no se recalcula ni se corrige; las correcciones externas se agregan como
constancias anexas, que solo se pueden agregar.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from enum import Enum

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja
from compulab.dominio.compartido.excepciones import exigir_zona_horaria
from compulab.dominio.pagos.excepciones import CierreInmutable
from compulab.dominio.pagos.tipos import LineaPago


def validar_periodo(anio: int, mes: int) -> None:
    for nombre, valor in (("anio", anio), ("mes", mes)):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise CierreInmutable(f"{nombre} debe ser un entero: {valor!r}")
    if not 1 <= mes <= 12:
        raise CierreInmutable(f"el mes debe ir de 1 a 12: {mes}")


def franja_del_mes(anio: int, mes: int) -> Franja:
    """Del día 1 a las 00:00 al día 1 del mes siguiente a las 00:00, hora de Costa Rica."""
    validar_periodo(anio, mes)
    inicio = datetime(anio, mes, 1, tzinfo=ZONA_COSTA_RICA)
    siguiente = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    fin = datetime.combine(datetime(*siguiente, 1).date(), time(0), tzinfo=ZONA_COSTA_RICA)
    return Franja(inicio, fin)


class EstadoCierre(Enum):
    CERRADO = "Cerrado"


@dataclass(frozen=True)
class Constancia:
    """Corrección externa registrada sobre un mes ya cerrado."""

    texto: str
    autor: str
    fecha: datetime

    def __post_init__(self) -> None:
        for nombre in ("texto", "autor"):
            valor = getattr(self, nombre)
            if not isinstance(valor, str) or not valor.strip():
                raise CierreInmutable(f"la constancia debe tener {nombre}")
        exigir_zona_horaria(self.fecha, "fecha")


class CierreMensual:
    """Agregado del cierre: año, mes, una línea por asistente y sus constancias."""

    def __init__(self, anio: int, mes: int, lineas: Iterable[LineaPago]) -> None:
        validar_periodo(anio, mes)
        lineas = tuple(lineas)
        if not all(isinstance(linea, LineaPago) for linea in lineas):
            raise CierreInmutable("las líneas del cierre deben ser LineaPago")
        ids = [linea.asistente_id for linea in lineas]
        if len(ids) != len(set(ids)):
            raise CierreInmutable("el cierre debe tener una sola línea por asistente")
        object.__setattr__(self, "_anio", anio)
        object.__setattr__(self, "_mes", mes)
        object.__setattr__(self, "_lineas", lineas)
        object.__setattr__(self, "_constancias", ())
        object.__setattr__(self, "_estado", EstadoCierre.CERRADO)

    def __setattr__(self, nombre: str, valor: object) -> None:
        raise CierreInmutable("un mes cerrado no se modifica; agregue una constancia")

    def __delattr__(self, nombre: str) -> None:
        raise CierreInmutable("un mes cerrado no se modifica; agregue una constancia")

    @property
    def anio(self) -> int:
        return self._anio

    @property
    def mes(self) -> int:
        return self._mes

    @property
    def lineas(self) -> tuple[LineaPago, ...]:
        return self._lineas

    @property
    def constancias(self) -> tuple[Constancia, ...]:
        return self._constancias

    @property
    def estado(self) -> EstadoCierre:
        return self._estado

    @property
    def monto_total(self) -> Decimal:
        return sum((linea.monto for linea in self._lineas), Decimal(0))

    def lineas_con_horas_sobre_tope(self) -> tuple[LineaPago, ...]:
        return tuple(linea for linea in self._lineas if linea.horas_sobre_tope > 0)

    def linea_de(self, asistente_id: str) -> LineaPago | None:
        return next((l for l in self._lineas if l.asistente_id == asistente_id), None)

    def agregar_constancia(self, constancia: Constancia) -> None:
        """Lo único que cambia en un cierre: se agrega una constancia al final."""
        if not isinstance(constancia, Constancia):
            raise CierreInmutable("solo se agregan constancias")
        object.__setattr__(self, "_constancias", self._constancias + (constancia,))

    def __repr__(self) -> str:
        return f"CierreMensual({self._anio}-{self._mes:02d}, {len(self._lineas)} líneas)"
