"""Fábricas de datos y dobles en memoria para las pruebas del módulo de pago."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja
from compulab.dominio.pagos import LineaPago, MarcaTrabajada, Recargo, Tarifa
from compulab.dominio.pagos.cierre import CierreMensual


def m(mes: int, dia: int, hora: int, minuto: int = 0, anio: int = 2026) -> datetime:
    """Momento en hora de Costa Rica. El 23 de noviembre de 2026 es lunes."""
    return datetime(anio, mes, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


# --- Fábricas ---------------------------------------------------------------


def marca(
    inicio: datetime,
    horas: int | Decimal = 4,
    asistente: str = "A1",
    categoria: str = "A",
    tope: int | Decimal = 20,
    sin_salida: bool = False,
) -> MarcaTrabajada:
    """Turno trabajado completo: entra a la hora de inicio y sale al fin programado."""
    fin = inicio + timedelta(hours=float(horas))
    return MarcaTrabajada(asistente, categoria, Decimal(tope), inicio, fin, inicio,
                          None if sin_salida else fin)


# --- Dobles en memoria de los puertos ---------------------------------------


class CierresEnMemoria:
    def __init__(self, *cierres: CierreMensual) -> None:
        self.todos: list[CierreMensual] = list(cierres)

    def existe(self, anio: int, mes: int) -> bool:
        return any((c.anio, c.mes) == (anio, mes) for c in self.todos)

    def guardar(self, cierre: CierreMensual) -> None:
        self.todos.append(cierre)


class MarcasEnMemoria:
    def __init__(self, *marcas: MarcaTrabajada) -> None:
        self.todas: list[MarcaTrabajada] = list(marcas)
        self.franjas_pedidas: list[Franja] = []

    def de_franja(self, franja: Franja) -> list[MarcaTrabajada]:
        self.franjas_pedidas.append(franja)
        return [marca for marca in self.todas if franja.contiene(marca.inicio_turno)]


class TarifasFijas:
    """Tarifas por categoría y recargo conocidos, vigentes siempre (o nunca si faltan)."""

    def __init__(self, tarifas: dict[str, int | Decimal] | None = None,
                 recargo: int | Decimal | None = 50) -> None:
        self._tarifas = {c: Tarifa(c, monto) for c, monto in (tarifas or {}).items()}
        self._recargo = None if recargo is None else Recargo(recargo)
        self.fechas_pedidas: list[date] = []

    def tarifa_vigente(self, categoria: str, fecha: date) -> Tarifa | None:
        self.fechas_pedidas.append(fecha)
        return self._tarifas.get(categoria)

    def recargo_vigente(self, fecha: date) -> Recargo | None:
        self.fechas_pedidas.append(fecha)
        return self._recargo


class NotificadorEspia:
    def __init__(self) -> None:
        self.enviados: list[tuple[str, str]] = []

    def notificar(self, destinatario: str, mensaje: str) -> None:
        self.enviados.append((destinatario, mensaje))

    def a(self, destinatario: str) -> list[str]:
        return [mensaje for d, mensaje in self.enviados if d == destinatario]


class ExportadorEspia:
    def __init__(self) -> None:
        self.exportados: list[tuple[int, int, tuple[LineaPago, ...]]] = []

    def exportar(self, anio: int, mes: int, lineas: Sequence[LineaPago]) -> str:
        self.exportados.append((anio, mes, tuple(lineas)))
        return f"becas_{anio}_{mes:02d}.csv"
