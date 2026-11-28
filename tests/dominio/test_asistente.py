"""Pruebas de Asistente y BloqueDisponible."""

from dataclasses import FrozenInstanceError
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest

from compulab.dominio.compartido import ZONA_COSTA_RICA, Franja
from compulab.dominio.horario import (
    Asistente,
    AsistenteInvalido,
    BloqueDisponible,
    EstadoAsistente,
)

LUNES = 0
MARTES = 1


def cr(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Momento de noviembre de 2026 en hora de Costa Rica. El 23 es lunes."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=ZONA_COSTA_RICA)


def bloque_lunes_manana() -> BloqueDisponible:
    return BloqueDisponible(LUNES, time(8, 0), time(12, 0))


def asistente(**cambios) -> Asistente:
    datos = {
        "id": "a-1",
        "categoria": "horas-asistente",
        "tope_semanal_horas": Decimal("20"),
        "bloques": [bloque_lunes_manana()],
    }
    datos.update(cambios)
    return Asistente(**datos)


# --- BloqueDisponible ---


@pytest.mark.parametrize("dia", [-1, 7])
def test_bloque_rechaza_dia_fuera_de_rango(dia):
    with pytest.raises(AsistenteInvalido):
        BloqueDisponible(dia, time(8, 0), time(12, 0))


def test_bloque_rechaza_dia_que_no_es_entero():
    with pytest.raises(AsistenteInvalido):
        BloqueDisponible(True, time(8, 0), time(12, 0))


@pytest.mark.parametrize("inicio, fin", [(time(12, 0), time(8, 0)), (time(8, 0), time(8, 0))])
def test_bloque_rechaza_inicio_no_anterior_al_fin(inicio, fin):
    with pytest.raises(AsistenteInvalido):
        BloqueDisponible(LUNES, inicio, fin)


def test_bloque_rechaza_horas_con_zona_horaria():
    with pytest.raises(AsistenteInvalido):
        BloqueDisponible(LUNES, time(8, 0, tzinfo=timezone.utc), time(12, 0))


def test_bloque_es_inmutable():
    with pytest.raises(FrozenInstanceError):
        bloque_lunes_manana()._inicio = time(7, 0)


def test_bloques_con_los_mismos_datos_son_iguales():
    assert bloque_lunes_manana() == bloque_lunes_manana()


def test_bloque_cubre_franja_dentro_del_bloque():
    assert bloque_lunes_manana().cubre(Franja(cr(23, 9), cr(23, 11)))


def test_bloque_cubre_franja_igual_al_bloque():
    assert bloque_lunes_manana().cubre(Franja(cr(23, 8), cr(23, 12)))


def test_bloque_no_cubre_franja_que_se_sale_por_el_fin():
    assert not bloque_lunes_manana().cubre(Franja(cr(23, 11), cr(23, 13)))


def test_bloque_no_cubre_franja_que_empieza_antes():
    assert not bloque_lunes_manana().cubre(Franja(cr(23, 7), cr(23, 9)))


def test_bloque_no_cubre_franja_de_otro_dia():
    assert not bloque_lunes_manana().cubre(Franja(cr(24, 9), cr(24, 11)))


def test_bloque_lee_la_franja_en_hora_de_costa_rica():
    # 15:00 UTC es 09:00 en Costa Rica.
    inicio = datetime(2026, 11, 23, 15, 0, tzinfo=timezone.utc)
    assert bloque_lunes_manana().cubre(Franja(inicio, inicio + timedelta(hours=2)))


def test_bloque_no_cubre_franja_que_termina_a_medianoche():
    bloque = BloqueDisponible(LUNES, time(18, 0), time(23, 59))
    assert not bloque.cubre(Franja(cr(23, 20), cr(24, 0)))


# --- Asistente: invariantes ---


def test_asistente_valido_expone_sus_datos():
    a = asistente()
    assert a.id == "a-1"
    assert a.categoria == "horas-asistente"
    assert a.tope_semanal_horas == Decimal("20")
    assert a.bloques == (bloque_lunes_manana(),)
    assert a.estado is EstadoAsistente.ACTIVO


def test_asistente_acepta_tope_entero_y_lo_guarda_como_decimal():
    a = asistente(tope_semanal_horas=10)
    assert a.tope_semanal_horas == Decimal("10")
    assert isinstance(a.tope_semanal_horas, Decimal)


@pytest.mark.parametrize("tope", [Decimal("0"), Decimal("-5"), 0, Decimal("NaN"), Decimal("Infinity")])
def test_asistente_rechaza_tope_no_positivo_o_no_finito(tope):
    with pytest.raises(AsistenteInvalido):
        asistente(tope_semanal_horas=tope)


@pytest.mark.parametrize("tope", [20.0, "20", True, None])
def test_asistente_rechaza_tope_que_no_es_decimal_ni_entero(tope):
    with pytest.raises(AsistenteInvalido):
        asistente(tope_semanal_horas=tope)


@pytest.mark.parametrize("categoria", ["", "   ", None])
def test_asistente_rechaza_categoria_vacia(categoria):
    with pytest.raises(AsistenteInvalido):
        asistente(categoria=categoria)


@pytest.mark.parametrize("id_", ["", "  ", None])
def test_asistente_rechaza_id_vacio(id_):
    with pytest.raises(AsistenteInvalido):
        asistente(id=id_)


def test_asistente_rechaza_sin_bloques_disponibles():
    with pytest.raises(AsistenteInvalido):
        asistente(bloques=[])


def test_asistente_rechaza_bloques_de_otro_tipo():
    with pytest.raises(AsistenteInvalido):
        asistente(bloques=[(LUNES, time(8, 0), time(12, 0))])


def test_asistente_rechaza_estado_desconocido():
    with pytest.raises(AsistenteInvalido):
        asistente(estado="Activo")


# --- Asistente: comportamiento ---


def test_asistente_activo_esta_activo():
    assert asistente().esta_activo


@pytest.mark.parametrize(
    "estado",
    [EstadoAsistente.RENUNCIADO, EstadoAsistente.DADO_DE_BAJA, EstadoAsistente.FINALIZADO],
)
def test_asistente_en_otro_estado_no_esta_activo(estado):
    assert not asistente(estado=estado).esta_activo


def test_asistente_tiene_disponible_si_algun_bloque_cubre_la_franja():
    a = asistente(bloques=[bloque_lunes_manana(), BloqueDisponible(MARTES, time(14, 0), time(18, 0))])
    assert a.tiene_disponible(Franja(cr(24, 15), cr(24, 17)))


def test_asistente_no_tiene_disponible_si_ningun_bloque_cubre_la_franja():
    assert not asistente().tiene_disponible(Franja(cr(24, 15), cr(24, 17)))


def test_bloques_no_cambian_si_se_modifica_la_lista_original():
    bloques = [bloque_lunes_manana()]
    a = asistente(bloques=bloques)
    bloques.append(BloqueDisponible(MARTES, time(8, 0), time(10, 0)))
    assert len(a.bloques) == 1


def test_atributos_son_de_solo_lectura():
    with pytest.raises(AttributeError):
        asistente().tope_semanal_horas = Decimal("40")


def test_asistentes_con_el_mismo_id_son_iguales():
    assert asistente() == asistente(categoria="otra", tope_semanal_horas=5)
    assert hash(asistente()) == hash(asistente(categoria="otra"))


def test_asistentes_con_distinto_id_son_distintos():
    assert asistente() != asistente(id="a-2")
