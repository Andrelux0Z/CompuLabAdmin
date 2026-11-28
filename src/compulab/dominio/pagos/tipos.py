"""Tipos de datos acordados para el cálculo de pagos."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from compulab.dominio.compartido.excepciones import exigir_zona_horaria
from compulab.dominio.pagos.excepciones import LineaPagoInvalida, MarcaInvalida

_SEGUNDOS_POR_HORA = Decimal(3600)


@dataclass(frozen=True)
class MarcaTrabajada:
    """Un turno trabajado por un asistente, tal como se registró.

    Lleva la categoría y el tope vigentes del asistente para no tener que consultarlos
    aparte. La salida puede faltar si el asistente no marcó al irse (E4 de CU-18).
    """

    asistente_id: str
    categoria: str
    tope_semanal: Decimal  # horas pagables por semana
    inicio_turno: datetime  # inicio programado del turno
    fin_turno: datetime  # fin programado del turno
    entrada: datetime
    salida: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.asistente_id, str) or not self.asistente_id.strip():
            raise MarcaInvalida("la marca debe tener un asistente")
        if not isinstance(self.categoria, str) or not self.categoria.strip():
            raise MarcaInvalida("la marca debe tener la categoría del asistente")
        if not isinstance(self.tope_semanal, Decimal) or not self.tope_semanal > 0:
            raise MarcaInvalida(f"el tope semanal debe ser un Decimal mayor que 0: {self.tope_semanal!r}")
        exigir_zona_horaria(self.inicio_turno, "inicio_turno")
        exigir_zona_horaria(self.fin_turno, "fin_turno")
        exigir_zona_horaria(self.entrada, "entrada")
        if not self.inicio_turno < self.fin_turno:
            raise MarcaInvalida("el inicio del turno debe ser anterior a su fin")
        if self.salida is not None:
            exigir_zona_horaria(self.salida, "salida")
            if not self.entrada < self.salida:
                raise MarcaInvalida(f"la salida ({self.salida}) debe ser posterior a la entrada ({self.entrada})")

    @property
    def sin_salida(self) -> bool:
        return self.salida is None

    @property
    def horas_trabajadas(self) -> Decimal:
        """Tiempo real entre entrada y salida. Sin salida, se paga hasta el fin programado."""
        fin = self.salida if self.salida is not None else self.fin_turno
        segundos = Decimal(str((fin - self.entrada).total_seconds()))
        return max(segundos / _SEGUNDOS_POR_HORA, Decimal(0))


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
