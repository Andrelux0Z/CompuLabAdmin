"""Pruebas del contrato CU-13: una por poscondición (P) y una por extensión (E)."""
from datetime import datetime, timedelta

import pytest

from compulab.aplicacion.reservar_maquina import ReservarMaquina, SolicitudReserva
from compulab.dominio.compartido.excepciones import FranjaInvalida
from compulab.dominio.compartido.franja import Franja
from compulab.dominio.maquinas.excepciones import (
    DuracionExcedida, LaboratorioCerrado, LimiteSemanalExcedido,
    MaquinaFueraDeServicio, MaquinaOcupada, ReservaActivaExistente)
from compulab.dominio.maquinas.reserva import EstadoReserva
from apoyo_maquinas import (
    FranjasCubiertasFijas, MaquinasEnMemoria, ProgramadorEspia, ReservasEnMemoria, h, maquina,
    reserva)
from compulab.dominio.compartido.reloj import RelojFijo

AHORA = h(23, 7)                                   # lunes 23 nov, 7:00
ABIERTO_MARTES = Franja(h(24, 7), h(24, 21))      # turnos cubren el martes 7:00-21:00
ABIERTO_MIERCOLES = Franja(h(25, 7), h(25, 21))


class Escenario:
    def __init__(self, maquinas=None, reservas=()):
        self.reloj = RelojFijo(AHORA)
        self.reservas = ReservasEnMemoria(*reservas)
        self.programador = ProgramadorEspia()
        ids = iter(["NUEVA", "OTRA", "TERCERA"])
        self.caso = ReservarMaquina(
            reloj=self.reloj,
            maquinas=MaquinasEnMemoria(*(maquinas or [maquina("M1"), maquina("M2")])),
            reservas=self.reservas,
            franjas=FranjasCubiertasFijas("LAB1", ABIERTO_MARTES, ABIERTO_MIERCOLES),
            programador=self.programador,
            nuevo_id=lambda: next(ids),
        )

    def reservar(self, inicio: datetime, fin: datetime, estudiante="E1", maq="M1"):
        return self.caso.ejecutar(SolicitudReserva(estudiante, maq, inicio, fin))


# --- Poscondiciones ---------------------------------------------------------

def test_reservar_crea_reserva_activa_y_ocupa_maquina():  # P1, P2
    esc = Escenario()
    r = esc.reservar(h(24, 8), h(24, 10))
    assert r.estado is EstadoReserva.ACTIVA
    assert (r.estudiante_id, r.maquina_id, r.franja) == ("E1", "M1", Franja(h(24, 8), h(24, 10)))
    assert esc.reservas.todas == [r]
    with pytest.raises(MaquinaOcupada):                     # P2: ya no está disponible
        esc.reservar(h(24, 9), h(24, 10), estudiante="E2")


def test_reservar_suma_horas_semanales_del_estudiante():  # P3
    esc = Escenario()
    esc.reservar(h(24, 8), h(24, 10))
    horas = sum(r.horas() for r in esc.reservas.del_estudiante("E1"))
    assert horas == 2


def test_reserva_se_libera_a_los_15_minutos_sin_presentarse():  # P4
    esc = Escenario()
    r = esc.reservar(h(24, 8), h(24, 10))
    assert esc.programador.programadas == [("NUEVA", h(24, 8, 15))]
    assert r.liberar_si_no_se_presento(h(24, 8, 15))
    # la máquina vuelve a estar disponible para quien llegue
    assert esc.reservar(h(24, 8, 30), h(24, 10), estudiante="E2").id == "OTRA"


# --- Extensiones ------------------------------------------------------------

def test_reserva_de_mas_de_2_horas_es_rechazada():  # E1
    with pytest.raises(DuracionExcedida):
        Escenario().reservar(h(24, 8), h(24, 10, 30))


def test_reserva_en_franja_sin_turno_es_rechazada():  # E2
    with pytest.raises(LaboratorioCerrado):
        Escenario().reservar(h(24, 20), h(24, 22))     # el turno termina a las 21:00


def test_maquina_fuera_de_servicio_es_rechazada():  # E3
    with pytest.raises(MaquinaFueraDeServicio):
        Escenario(maquinas=[maquina("M1", en_servicio=False)]).reservar(h(24, 8), h(24, 9))


def test_maquina_ocupada_es_rechazada():  # E4
    otra = reserva("R0", "E9", "M1", h(24, 9), h(24, 11))
    with pytest.raises(MaquinaOcupada):
        Escenario(reservas=[otra]).reservar(h(24, 8), h(24, 10))


def test_segunda_reserva_activa_es_rechazada():  # E5
    previa = reserva("R0", "E1", "M2", h(25, 8), h(25, 9))
    with pytest.raises(ReservaActivaExistente):
        Escenario(reservas=[previa]).reservar(h(24, 8), h(24, 9))


def test_superar_6_horas_semanales_es_rechazado():  # E6
    previas = [reserva("R0", "E1", "M2", h(23, 8), h(23, 10), EstadoReserva.FINALIZADA),
               reserva("R1", "E1", "M2", h(23, 12), h(23, 14), EstadoReserva.FINALIZADA),
               reserva("R2", "E1", "M2", h(23, 15), h(23, 16), EstadoReserva.FINALIZADA)]  # 5 h
    with pytest.raises(LimiteSemanalExcedido):
        Escenario(reservas=previas).reservar(h(24, 8), h(24, 10))


def test_reserva_en_el_pasado_es_rechazada():  # E7
    esc = Escenario()
    with pytest.raises(FranjaInvalida):
        esc.reservar(AHORA - timedelta(hours=1), AHORA)
    with pytest.raises(FranjaInvalida):
        esc.reservar(h(24, 10), h(24, 8))


def test_reserva_rechazada_no_deja_rastro():
    esc = Escenario(maquinas=[maquina("M1", en_servicio=False)])
    with pytest.raises(MaquinaFueraDeServicio):
        esc.reservar(h(24, 8), h(24, 9))
    assert esc.reservas.todas == [] and esc.programador.programadas == []
