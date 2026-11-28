"""Cálculo del pago de un mes (patrón Strategy: CalculadoraPago / CalculadoraEstandar).

Regla del tope: el tope es semanal (lunes a domingo, hora de Costa Rica). Dentro de la
semana las horas se ordenan por entrada; las que quedan después de alcanzar el tope son
horas sobre el tope y no se pagan. Si una semana empezó el mes anterior, esas horas ya
cerradas cuentan primero contra el tope, pero no se vuelven a pagar ni a registrar.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from compulab.dominio.compartido import ZONA_COSTA_RICA, Semana
from compulab.dominio.pagos.tarifas import Recargo, Tarifa, linea_de_pago
from compulab.dominio.pagos.tipos import LineaPago, MarcaTrabajada

_CERO = Decimal(0)


class CalculadoraPago(Protocol):
    def calcular(
        self,
        anio: int,
        mes: int,
        marcas: Iterable[MarcaTrabajada],
        tarifa_de: Callable[[str], Tarifa],
        recargo: Recargo,
    ) -> list[LineaPago]:
        """Una línea por asistente con marcas en el mes, ordenadas por id de asistente.

        `marcas` trae las del mes y, para la primera semana, también las de sus días que
        caen en el mes anterior. `tarifa_de` da la tarifa vigente de una categoría.
        """
        ...


@dataclass
class _Acumulado:
    normales: Decimal = _CERO
    con_recargo: Decimal = _CERO
    sobre_tope: Decimal = _CERO
    categoria: str = ""


def es_del_mes(marca: MarcaTrabajada, anio: int, mes: int) -> bool:
    """Cada turno se paga en el mes del día en que ocurre, en hora de Costa Rica."""
    dia = marca.inicio_turno.astimezone(ZONA_COSTA_RICA).date()
    return (dia.year, dia.month) == (anio, mes)


class CalculadoraEstandar:
    def calcular(
        self,
        anio: int,
        mes: int,
        marcas: Iterable[MarcaTrabajada],
        tarifa_de: Callable[[str], Tarifa],
        recargo: Recargo,
    ) -> list[LineaPago]:
        por_asistente_y_semana: dict[tuple[str, Semana], list[MarcaTrabajada]] = defaultdict(list)
        for marca in marcas:
            semana = Semana.de_momento(marca.inicio_turno)
            por_asistente_y_semana[(marca.asistente_id, semana)].append(marca)

        acumulados: dict[str, _Acumulado] = {}
        for (asistente_id, _semana), de_la_semana in por_asistente_y_semana.items():
            self._repartir_semana(asistente_id, de_la_semana, anio, mes, recargo, acumulados)

        return [
            linea_de_pago(
                asistente_id,
                total.normales,
                total.con_recargo,
                total.sobre_tope,
                tarifa_de(total.categoria),
                recargo,
            )
            for asistente_id, total in sorted(acumulados.items())
        ]

    @staticmethod
    def _repartir_semana(
        asistente_id: str,
        marcas: Sequence[MarcaTrabajada],
        anio: int,
        mes: int,
        recargo: Recargo,
        acumulados: dict[str, _Acumulado],
    ) -> None:
        ordenadas = sorted(marcas, key=lambda m: (m.entrada, m.inicio_turno))
        # El tope vigente es el de la marca más reciente de la semana.
        tope = ordenadas[-1].tope_semanal
        contadas = _CERO
        for marca in ordenadas:
            horas = marca.horas_trabajadas
            pagables = min(horas, max(tope - contadas, _CERO))
            contadas += horas
            if not es_del_mes(marca, anio, mes):
                continue  # del mes anterior: ya cerrada, solo cuenta contra el tope
            total = acumulados.setdefault(asistente_id, _Acumulado())
            total.categoria = marca.categoria
            if recargo.aplica_a(marca.inicio_turno):
                total.con_recargo += pagables
            else:
                total.normales += pagables
            total.sobre_tope += horas - pagables
