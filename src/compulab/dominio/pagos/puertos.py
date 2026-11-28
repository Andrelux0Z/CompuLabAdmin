"""Puertos del módulo de pago. Los adaptadores reales viven en infraestructura.

ExportadorPago (archivo para Becas) está en compulab.aplicacion.puertos_pago.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from compulab.dominio.compartido import Franja
from compulab.dominio.pagos.cierre import CierreMensual
from compulab.dominio.pagos.tarifas import Recargo, Tarifa
from compulab.dominio.pagos.tipos import MarcaTrabajada


class RepositorioCierres(Protocol):
    def existe(self, anio: int, mes: int) -> bool: ...

    def guardar(self, cierre: CierreMensual) -> None: ...


class ConsultaMarcas(Protocol):
    def de_franja(self, franja: Franja) -> list[MarcaTrabajada]:
        """Marcas de todos los asistentes cuyo turno empieza dentro de la franja."""
        ...


class ConfiguracionTarifas(Protocol):
    def tarifa_vigente(self, categoria: str, fecha: date) -> Tarifa | None:
        """Tarifa de la categoría vigente en esa fecha, o None si no hay."""
        ...

    def recargo_vigente(self, fecha: date) -> Recargo | None:
        """Recargo vigente en esa fecha, o None si no hay."""
        ...


class Notificador(Protocol):
    def notificar(self, destinatario: str, mensaje: str) -> None: ...
