from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from compulab.dominio.maquinas.excepciones import (
    LaboratorioCerrado, LimiteSemanalExcedido, MaquinaFueraDeServicio,
    MaquinaOcupada, ReservaActivaExistente)
from compulab.dominio.maquinas.maquina import Maquina
from compulab.dominio.maquinas.reserva import Reserva


class PoliticaReservas:
    """Reglas de la Coordinación de Soporte para aceptar una reserva nueva.
    Se verifican en el orden del contrato CU-13 (E2 a E6)."""

    MAX_ACTIVAS = 1
    MAX_HORAS_SEMANA = Decimal(6)

    def verificar(self, nueva: Reserva, maquina: Maquina, laboratorio_abierto: bool,
                  reservas_de_la_maquina: Iterable[Reserva],
                  reservas_del_estudiante: Iterable[Reserva]) -> None:
        reservas_de_la_maquina = list(reservas_de_la_maquina)
        reservas_del_estudiante = list(reservas_del_estudiante)

        if not laboratorio_abierto:
            raise LaboratorioCerrado("El laboratorio no tiene un turno que cubra esa franja")
        if not maquina.en_servicio:
            raise MaquinaFueraDeServicio(f"La máquina {maquina.identificador} está fuera de servicio")
        if any(r.esta_vigente() and r.franja.traslapa(nueva.franja)
               for r in reservas_de_la_maquina):
            raise MaquinaOcupada(f"La máquina {maquina.identificador} ya está reservada en esa franja")
        activas = [r for r in reservas_del_estudiante if r.esta_vigente()]
        if len(activas) >= self.MAX_ACTIVAS:
            raise ReservaActivaExistente("Ya tiene una reserva activa")
        semana = nueva.franja.semana
        horas = sum((r.horas() for r in reservas_del_estudiante
                     if r.cuenta_para_limite_semanal() and r.franja.semana == semana), Decimal(0))
        if horas + nueva.horas() > self.MAX_HORAS_SEMANA:
            raise LimiteSemanalExcedido(
                f"Superaría {self.MAX_HORAS_SEMANA} h en la semana "
                f"(lleva {horas:g} h, pide {nueva.horas():g} h)")
