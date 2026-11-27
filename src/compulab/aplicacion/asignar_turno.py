"""Caso de uso CU-07 Asignar turno."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja
from compulab.dominio.horario import (
    REGLAS_DE_ASIGNACION,
    AgendaSemanal,
    ConsultaAsistentes,
    ConsultaCoordinaciones,
    LaboratorioNoAutorizado,
    ReglaTurno,
    RepositorioTurnos,
    Turno,
)


@dataclass(frozen=True)
class SolicitudAsignacion:
    """Datos de asignar_turno(coordinador, laboratorio, asistente, dia, inicio, fin, aceptado).

    El día y las horas se leen en hora de Costa Rica.
    """

    coordinador_id: str
    laboratorio_id: str
    asistente_id: str
    dia: date
    inicio: time
    fin: time
    aceptado_por_asistente: bool = False


class AsignarTurno:
    def __init__(
        self,
        turnos: RepositorioTurnos,
        asistentes: ConsultaAsistentes,
        coordinaciones: ConsultaCoordinaciones,
        reglas: Sequence[ReglaTurno] = REGLAS_DE_ASIGNACION,
        nuevo_id: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._turnos = turnos
        self._asistentes = asistentes
        self._coordinaciones = coordinaciones
        self._reglas = tuple(reglas)
        self._nuevo_id = nuevo_id

    def ejecutar(self, solicitud: SolicitudAsignacion) -> Turno:
        # Paso 2: el coordinador puede modificar ese laboratorio.            E1
        if not self._coordinaciones.puede_modificar(solicitud.coordinador_id, solicitud.laboratorio_id):
            raise LaboratorioNoAutorizado(
                f"el coordinador {solicitud.coordinador_id} no puede modificar "
                f"el laboratorio {solicitud.laboratorio_id}"
            )

        franja = Franja(                                                    # E7 inicio >= fin
            datetime.combine(solicitud.dia, solicitud.inicio, tzinfo=ZONA_COSTA_RICA),
            datetime.combine(solicitud.dia, solicitud.fin, tzinfo=ZONA_COSTA_RICA),
        )
        turno = Turno(                                                      # P1, P2
            self._nuevo_id(),
            solicitud.laboratorio_id,
            solicitud.asistente_id,
            franja,
            aceptado_fuera_de_disponibilidad=solicitud.aceptado_por_asistente,
        )

        asistente = self._asistentes.obtener(solicitud.asistente_id)
        agenda = AgendaSemanal(
            asistente,
            turno.semana,
            self._turnos.turnos_de_asistente(asistente.id, turno.semana),
        )
        # Pasos 3 a 6: activo, sin traslape, dentro del tope y disponibilidad.  E2 a E5
        for regla in self._reglas:
            regla.verificar(agenda, turno)

        agenda.agregar(turno)                                               # P3
        self._turnos.guardar(turno)                                         # P4 / E6
        return turno
