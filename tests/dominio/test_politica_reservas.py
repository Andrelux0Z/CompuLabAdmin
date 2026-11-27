from datetime import timedelta

import pytest

from compulab.dominio.maquinas.excepciones import (
    LaboratorioCerrado, LimiteSemanalExcedido, MaquinaFueraDeServicio,
    MaquinaOcupada, ReservaActivaExistente)
from compulab.dominio.maquinas.politica import PoliticaReservas
from compulab.dominio.maquinas.reserva import EstadoReserva
from apoyo_maquinas import h, maquina, reserva

politica = PoliticaReservas()


def verificar(nueva, maq=None, abierto=True, de_maquina=(), del_estudiante=()):
    politica.verificar(nueva, maq or maquina(), abierto, de_maquina, del_estudiante)


def test_reserva_valida_pasa():
    verificar(reserva())


def test_laboratorio_cerrado():
    with pytest.raises(LaboratorioCerrado):
        verificar(reserva(), abierto=False)


def test_maquina_fuera_de_servicio():
    with pytest.raises(MaquinaFueraDeServicio):
        verificar(reserva(), maq=maquina(en_servicio=False))


def test_maquina_ocupada_por_reserva_que_se_traslapa():
    otra = reserva("R0", "E9", inicio=h(24, 7, 30))
    with pytest.raises(MaquinaOcupada):
        verificar(reserva(inicio=h(24, 8)), de_maquina=[otra])


def test_reserva_cancelada_no_ocupa_la_maquina():
    otra = reserva("R0", "E9", inicio=h(24, 8), estado=EstadoReserva.CANCELADA)
    verificar(reserva(inicio=h(24, 8)), de_maquina=[otra])


def test_segunda_reserva_activa():
    with pytest.raises(ReservaActivaExistente):
        verificar(reserva(inicio=h(25, 8)), del_estudiante=[reserva("R0", inicio=h(24, 8))])


def test_limite_semanal_cuenta_finalizadas_y_no_liberadas():
    hechas = [reserva(f"R{i}", inicio=h(23 + i, 8), fin=h(23 + i, 10),
                      estado=EstadoReserva.FINALIZADA) for i in range(2)]  # 4 h
    liberada = reserva("RL", inicio=h(25, 8), fin=h(25, 10), estado=EstadoReserva.LIBERADA)
    verificar(reserva(inicio=h(26, 8), fin=h(26, 10)), del_estudiante=hechas + [liberada])  # 6 h justas
    otra_hora = reserva("R9", inicio=h(25, 14), fin=h(25, 15), estado=EstadoReserva.FINALIZADA)
    with pytest.raises(LimiteSemanalExcedido):  # 5 h + 2 h = 7 h
        verificar(reserva(inicio=h(26, 8), fin=h(26, 10)), del_estudiante=hechas + [otra_hora])


def test_limite_semanal_ignora_otras_semanas():
    semana_pasada = [reserva(f"R{i}", inicio=h(16 + i, 8), fin=h(16 + i, 10),
                             estado=EstadoReserva.FINALIZADA) for i in range(3)]
    verificar(reserva(inicio=h(24, 8), fin=h(24, 10)), del_estudiante=semana_pasada)
