"""Tipos de datos acordados para el cálculo de pagos. Son datos puros, sin lógica."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MarcaTrabajada:
    """Un turno trabajado por un asistente, tal como se registró."""

    asistente_id: str
    categoria: str
    tope_semanal: Decimal  # horas pagables por semana
    inicio_turno: datetime
    entrada: datetime
    salida: datetime


@dataclass(frozen=True)
class LineaPago:
    """Resultado del pago de un asistente en un período."""

    asistente_id: str
    horas_normales: Decimal
    horas_con_recargo: Decimal
    horas_sobre_tope: Decimal
    monto: Decimal
