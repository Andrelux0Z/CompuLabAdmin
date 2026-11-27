from datetime import timedelta

import pytest

from compulab.dominio.maquinas.excepciones import TransicionInvalida
from compulab.dominio.maquinas.excepciones import DuracionExcedida
from compulab.dominio.maquinas.reserva import EstadoReserva
from apoyo_maquinas import h, reserva


def test_reserva_de_exactamente_2_horas_es_valida():
    assert reserva(inicio=h(24, 8), fin=h(24, 10)).horas() == 2


def test_reserva_de_mas_de_2_horas_es_invalida():
    with pytest.raises(DuracionExcedida):
        reserva(inicio=h(24, 8), fin=h(24, 10, 1))


def test_presentarse_dentro_de_la_tolerancia_la_pone_en_uso():
    r = reserva(inicio=h(24, 8))
    r.presentarse(h(24, 8, 15))
    assert r.estado is EstadoReserva.EN_USO


def test_presentarse_tarde_no_se_permite():
    r = reserva(inicio=h(24, 8))
    with pytest.raises(TransicionInvalida):
        r.presentarse(h(24, 8, 16))


def test_liberar_si_no_se_presento_a_los_15_minutos():
    r = reserva(inicio=h(24, 8))
    assert r.liberar_si_no_se_presento(h(24, 8, 14)) is False
    assert r.estado is EstadoReserva.ACTIVA
    assert r.liberar_si_no_se_presento(h(24, 8, 15)) is True
    assert r.estado is EstadoReserva.LIBERADA
    assert not r.esta_vigente()


def test_no_libera_una_reserva_en_uso():
    r = reserva(inicio=h(24, 8))
    r.presentarse(h(24, 8, 5))
    assert r.liberar_si_no_se_presento(h(24, 9)) is False
    assert r.estado is EstadoReserva.EN_USO


def test_cancelar_guarda_el_motivo():
    r = reserva()
    r.cancelar("Máquina fuera de servicio")
    assert r.estado is EstadoReserva.CANCELADA
    assert r.motivo_cancelacion == "Máquina fuera de servicio"
    with pytest.raises(TransicionInvalida):
        r.cancelar("otra vez")
