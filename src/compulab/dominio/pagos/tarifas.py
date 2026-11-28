"""Tarifa y Recargo: objetos valor con lo que se paga por hora.

La vigencia por fecha la resuelve el puerto ConfiguracionTarifas; estos objetos son
solo el valor vigente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal

from compulab.dominio.compartido import ZONA_COSTA_RICA
from compulab.dominio.compartido.excepciones import exigir_zona_horaria
from compulab.dominio.pagos.excepciones import TarifaInvalida
from compulab.dominio.pagos.tipos import LineaPago

_CIEN = Decimal(100)


def _decimal(valor: object, nombre: str) -> Decimal:
    if isinstance(valor, bool) or not isinstance(valor, (Decimal, int)):
        raise TarifaInvalida(f"{nombre} debe ser Decimal o entero: {valor!r}")
    numero = Decimal(valor)
    if not numero.is_finite():
        raise TarifaInvalida(f"{nombre} debe ser un número finito: {valor!r}")
    return numero


@dataclass(frozen=True, init=False)
class Tarifa:
    """Monto por hora de una categoría de beca."""

    _categoria: str = field()
    _monto_por_hora: Decimal = field()

    def __init__(self, categoria: str, monto_por_hora: Decimal | int) -> None:
        if not isinstance(categoria, str) or not categoria.strip():
            raise TarifaInvalida("la tarifa debe tener una categoría")
        monto = _decimal(monto_por_hora, "el monto por hora")
        if monto <= 0:
            raise TarifaInvalida(f"el monto por hora debe ser mayor que 0: {monto}")
        object.__setattr__(self, "_categoria", categoria)
        object.__setattr__(self, "_monto_por_hora", monto)

    @property
    def categoria(self) -> str:
        return self._categoria

    @property
    def monto_por_hora(self) -> Decimal:
        return self._monto_por_hora


@dataclass(frozen=True, init=False)
class Recargo:
    """Recargo único, no acumulable, para turnos nocturnos o de fin de semana.

    Aplica a todas las horas de un turno que empieza a las 18:00 o después, o que cae
    en sábado o domingo, en hora de Costa Rica. El porcentaje se expresa sobre 100.
    """

    HORA_NOCTURNA = time(18, 0)

    _porcentaje: Decimal = field()

    def __init__(self, porcentaje: Decimal | int) -> None:
        valor = _decimal(porcentaje, "el porcentaje de recargo")
        if valor < 0:
            raise TarifaInvalida(f"el porcentaje de recargo no puede ser negativo: {valor}")
        object.__setattr__(self, "_porcentaje", valor)

    @property
    def porcentaje(self) -> Decimal:
        return self._porcentaje

    @property
    def factor(self) -> Decimal:
        """1 + recargo. Con 50 % es 1.5."""
        return 1 + self._porcentaje / _CIEN

    def aplica_a(self, inicio_turno: datetime) -> bool:
        """True si el turno que empieza en ese momento lleva recargo."""
        exigir_zona_horaria(inicio_turno, "inicio_turno")
        local = inicio_turno.astimezone(ZONA_COSTA_RICA)
        es_fin_de_semana = local.weekday() >= 5
        es_nocturno = local.time() >= self.HORA_NOCTURNA
        return es_fin_de_semana or es_nocturno


def linea_de_pago(
    asistente_id: str,
    horas_normales: Decimal,
    horas_con_recargo: Decimal,
    horas_sobre_tope: Decimal,
    tarifa: Tarifa,
    recargo: Recargo,
) -> LineaPago:
    """Línea con monto = normales × tarifa + con recargo × tarifa × (1 + recargo)."""
    por_hora = tarifa.monto_por_hora
    monto = horas_normales * por_hora + horas_con_recargo * por_hora * recargo.factor
    return LineaPago(
        asistente_id,
        horas_normales,
        horas_con_recargo,
        horas_sobre_tope,
        monto,
        por_hora,
        recargo.porcentaje,
    )
