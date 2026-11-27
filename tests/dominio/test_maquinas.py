import pytest

from compulab.dominio.maquinas.excepciones import TransicionInvalida
from compulab.dominio.maquinas.excepciones import LaboratorioInvalido, MaquinaInvalida
from compulab.dominio.maquinas.laboratorio import Laboratorio
from compulab.dominio.maquinas.maquina import Maquina
from apoyo_maquinas import laboratorio, maquina


def test_maquina_sin_identificador_es_invalida():
    with pytest.raises(MaquinaInvalida):
        Maquina("M1", "LAB1", "  ")


def test_maquina_fuera_de_servicio_y_reparada():
    m = maquina()
    m.marcar_fuera_de_servicio()
    assert not m.en_servicio
    with pytest.raises(TransicionInvalida):
        m.marcar_fuera_de_servicio()
    m.marcar_reparada()
    assert m.en_servicio


def test_laboratorio_sin_maquinas_es_invalido():
    with pytest.raises(LaboratorioInvalido):
        Laboratorio("LAB1", "Lab", "Cartago", [])


def test_laboratorio_con_identificadores_repetidos_es_invalido():
    with pytest.raises(LaboratorioInvalido):
        Laboratorio("LAB1", "Lab", "Cartago",
                    [Maquina("M1", "LAB1", "PC-01"), Maquina("M2", "LAB1", "PC-01")])


def test_laboratorio_con_maquina_de_otro_laboratorio_es_invalido():
    with pytest.raises(LaboratorioInvalido):
        Laboratorio("LAB1", "Lab", "Cartago", [maquina("M1", "LAB2")])


def test_laboratorio_lista_maquinas_en_servicio():
    lab = laboratorio(n=3)
    lab.maquina("M2").marcar_fuera_de_servicio()
    assert [m.id for m in lab.en_servicio()] == ["M1", "M3"]
