"""Fábricas de datos y dobles en memoria para las pruebas del módulo de horario."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja, Semana
from compulab.dominio.horario import (
    Asistente,
    BloqueDisponible,
    EstadoAsistente,
    EstadoTurno,
    Turno,
)

LUNES = 0


def h(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre de 2026 en hora de Costa Rica. El 23 es lunes."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


# --- Fábricas ---------------------------------------------------------------


def asistente(
    id: str = "A1",
    tope: Decimal | int = 10,
    estado: EstadoAsistente = EstadoAsistente.ACTIVO,
    bloques: tuple[BloqueDisponible, ...] = (BloqueDisponible(LUNES, time(8, 0), time(12, 0)),),
) -> Asistente:
    """Por omisión: activo, tope de 10 h y disponible los lunes de 8:00 a 12:00."""
    return Asistente(id, "horas-asistente", tope, bloques, estado)


def turno(
    id: str = "T1",
    asistente_id: str = "A1",
    laboratorio_id: str = "LAB1",
    inicio: datetime | None = None,
    fin: datetime | None = None,
    aceptado: bool = False,
    estado: EstadoTurno = EstadoTurno.ASIGNADO,
) -> Turno:
    """Por omisión: lunes 23 de noviembre de 8:00 a 12:00 en LAB1."""
    franja = Franja(inicio or h(23, 8), fin or h(23, 12))
    return Turno(id, laboratorio_id, asistente_id, franja, aceptado, estado)


# --- Dobles en memoria de los puertos ---------------------------------------


class TurnosEnMemoria:
    def __init__(self, *turnos: Turno) -> None:
        self.todos: list[Turno] = list(turnos)

    def turnos_de_asistente(self, asistente_id: str, semana: Semana) -> list[Turno]:
        return [t for t in self.todos if t.asistente_id == asistente_id and t.semana == semana]

    def turnos_de_laboratorio(self, laboratorio_id: str, franja: Franja) -> list[Turno]:
        return [t for t in self.todos
                if t.laboratorio_id == laboratorio_id and t.franja.traslapa(franja)]

    def guardar(self, turno: Turno) -> None:
        self.todos = [t for t in self.todos if t.id != turno.id] + [turno]


class AsistentesEnMemoria:
    def __init__(self, *asistentes: Asistente) -> None:
        self._asistentes = {a.id: a for a in asistentes}

    def obtener(self, asistente_id: str) -> Asistente:
        return self._asistentes[asistente_id]


class CoordinacionesFijas:
    """Coordinadores de soporte (todos los laboratorios) y de laboratorio (solo los suyos)."""

    def __init__(self, soporte: tuple[str, ...] = (), **laboratorios_por_coordinador: tuple[str, ...]) -> None:
        self._soporte = set(soporte)
        self._laboratorios = {c: set(labs) for c, labs in laboratorios_por_coordinador.items()}

    def puede_modificar(self, coordinador_id: str, laboratorio_id: str) -> bool:
        if coordinador_id in self._soporte:
            return True
        return laboratorio_id in self._laboratorios.get(coordinador_id, set())
