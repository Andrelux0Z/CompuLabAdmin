"""Caso de uso CU-13 Reservar máquina."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from compulab.dominio.compartido.excepciones import FranjaInvalida
from compulab.dominio.compartido.franja import Franja
from compulab.dominio.compartido.reloj import Reloj
from compulab.dominio.maquinas.politica import PoliticaReservas
from compulab.dominio.maquinas.puertos import (
    ConsultaFranjasCubiertas, ProgramadorLiberaciones, RepositorioMaquinas,
    RepositorioReservas)
from compulab.dominio.maquinas.reserva import Reserva


@dataclass(frozen=True)
class SolicitudReserva:
    estudiante_id: str
    maquina_id: str
    inicio: datetime
    fin: datetime


class ReservarMaquina:
    def __init__(self, reloj: Reloj, maquinas: RepositorioMaquinas,
                 reservas: RepositorioReservas, franjas: ConsultaFranjasCubiertas,
                 programador: ProgramadorLiberaciones,
                 politica: PoliticaReservas | None = None,
                 nuevo_id: Callable[[], str] = lambda: str(uuid.uuid4())) -> None:
        self._reloj = reloj
        self._maquinas = maquinas
        self._reservas = reservas
        self._franjas = franjas
        self._programador = programador
        self._politica = politica or PoliticaReservas()
        self._nuevo_id = nuevo_id

    def ejecutar(self, solicitud: SolicitudReserva) -> Reserva:
        franja = Franja(solicitud.inicio, solicitud.fin)                     # E7 inicio >= fin
        if franja.inicio <= self._reloj.ahora():
            raise FranjaInvalida("No se puede reservar en el pasado")       # E7 pasado
        reserva = Reserva(self._nuevo_id(), solicitud.estudiante_id,
                          solicitud.maquina_id, franja)                      # E1 > 2 h
        maquina = self._maquinas.obtener(solicitud.maquina_id)
        self._politica.verificar(                                            # E2 a E6
            reserva,
            maquina,
            laboratorio_abierto=self._franjas.cubre(maquina.laboratorio_id, franja),
            reservas_de_la_maquina=self._reservas.de_maquina(maquina.id, franja),
            reservas_del_estudiante=self._reservas.del_estudiante(solicitud.estudiante_id),
        )
        self._reservas.guardar(reserva)                                      # P1, P2, P3
        self._programador.programar_liberacion(reserva.id, reserva.limite_para_presentarse)  # P4
        return reserva
