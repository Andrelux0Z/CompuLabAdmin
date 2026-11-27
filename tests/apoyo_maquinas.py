"""Fábricas de datos y dobles en memoria para las pruebas del módulo de máquinas."""
from __future__ import annotations

from datetime import datetime, timedelta

from compulab.dominio.compartido.franja import Franja
from compulab.dominio.compartido.semana import ZONA_COSTA_RICA
from compulab.dominio.maquinas.laboratorio import Laboratorio
from compulab.dominio.maquinas.maquina import Maquina
from compulab.dominio.maquinas.reserva import EstadoReserva, Reserva


def h(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre 2026 en hora de Costa Rica. El 23 es lunes."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


# --- Fábricas ---------------------------------------------------------------

def maquina(id="M1", lab="LAB1", identificador=None, en_servicio=True) -> Maquina:
    return Maquina(id, lab, identificador or f"PC-{id}", en_servicio)


def laboratorio(id="LAB1", n=3) -> Laboratorio:
    return Laboratorio(id, "Laboratorio 1", "Cartago",
                       [maquina(f"M{i}", id) for i in range(1, n + 1)])


def reserva(id="R1", estudiante="E1", maq="M1", inicio=None, fin=None,
            estado=EstadoReserva.ACTIVA) -> Reserva:
    inicio = inicio or h(24, 8)
    fin = fin or inicio + timedelta(hours=1)
    return Reserva(id, estudiante, maq, Franja(inicio, fin), estado)


# --- Dobles en memoria de los puertos ---------------------------------------

class MaquinasEnMemoria:
    def __init__(self, *maquinas: Maquina) -> None:
        self._maquinas = {m.id: m for m in maquinas}

    def obtener(self, maquina_id: str) -> Maquina:
        return self._maquinas[maquina_id]


class ReservasEnMemoria:
    def __init__(self, *reservas: Reserva) -> None:
        self.todas: list[Reserva] = list(reservas)

    def de_maquina(self, maquina_id: str, franja: Franja) -> list[Reserva]:
        return [r for r in self.todas if r.maquina_id == maquina_id and r.franja.traslapa(franja)]

    def del_estudiante(self, estudiante_id: str) -> list[Reserva]:
        return [r for r in self.todas if r.estudiante_id == estudiante_id]

    def guardar(self, reserva: Reserva) -> None:
        self.todas = [r for r in self.todas if r.id != reserva.id] + [reserva]


class FranjasCubiertasFijas:
    """Laboratorio abierto solo dentro de las franjas dadas."""

    def __init__(self, laboratorio_id: str, *abiertas: Franja) -> None:
        self._laboratorio_id = laboratorio_id
        self._abiertas = abiertas

    def cubre(self, laboratorio_id: str, franja: Franja) -> bool:
        return laboratorio_id == self._laboratorio_id and any(a.contiene(franja) for a in self._abiertas)


class ProgramadorEspia:
    def __init__(self) -> None:
        self.programadas: list[tuple[str, datetime]] = []

    def programar_liberacion(self, reserva_id: str, momento: datetime) -> None:
        self.programadas.append((reserva_id, momento))
