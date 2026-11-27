from __future__ import annotations

from compulab.dominio.maquinas.excepciones import MaquinaInvalida, TransicionInvalida


class Maquina:
    """Máquina de un laboratorio. Solo sabe si está o no en servicio."""

    def __init__(self, id: str, laboratorio_id: str, identificador: str,
                 en_servicio: bool = True) -> None:
        if not id or not laboratorio_id:
            raise MaquinaInvalida("La máquina necesita id y laboratorio")
        if not identificador or not identificador.strip():
            raise MaquinaInvalida("La máquina necesita un identificador")
        self._id = id
        self._laboratorio_id = laboratorio_id
        self._identificador = identificador.strip()
        self._en_servicio = en_servicio

    @property
    def id(self) -> str:
        return self._id

    @property
    def laboratorio_id(self) -> str:
        return self._laboratorio_id

    @property
    def identificador(self) -> str:
        return self._identificador

    @property
    def en_servicio(self) -> bool:
        return self._en_servicio

    def marcar_fuera_de_servicio(self) -> None:
        if not self._en_servicio:
            raise TransicionInvalida("La máquina ya está fuera de servicio")
        self._en_servicio = False

    def marcar_reparada(self) -> None:
        if self._en_servicio:
            raise TransicionInvalida("La máquina ya está en servicio")
        self._en_servicio = True
