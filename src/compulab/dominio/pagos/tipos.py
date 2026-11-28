"""Tipos de datos acordados para el cálculo de pagos."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from compulab.dominio.pagos.excepciones import LineaPagoInvalida


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
    """Resultado del pago de un asistente en un período.

    Guarda la tarifa por hora y el porcentaje de recargo con que se calculó, para que el
    cierre no cambie si después cambia la configuración (ADR-05).
    """

    asistente_id: str
    horas_normales: Decimal
    horas_con_recargo: Decimal
    horas_sobre_tope: Decimal
    monto: Decimal
    tarifa: Decimal  # colones por hora
    recargo: Decimal  # porcentaje; 50 significa 50 %

    def __post_init__(self) -> None:
        if not isinstance(self.asistente_id, str) or not self.asistente_id.strip():
            raise LineaPagoInvalida("la línea de pago debe tener un asistente")
        for nombre in ("horas_normales", "horas_con_recargo", "horas_sobre_tope", "monto", "recargo"):
            valor = getattr(self, nombre)
            if not isinstance(valor, Decimal) or not valor.is_finite() or valor < 0:
                raise LineaPagoInvalida(f"{nombre} debe ser un Decimal mayor o igual a 0: {valor!r}")
        if not isinstance(self.tarifa, Decimal) or not self.tarifa.is_finite() or self.tarifa <= 0:
            raise LineaPagoInvalida(f"la tarifa debe ser un Decimal mayor que 0: {self.tarifa!r}")
