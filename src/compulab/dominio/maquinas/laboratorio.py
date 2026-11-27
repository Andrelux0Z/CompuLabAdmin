from __future__ import annotations

from typing import Iterable

from compulab.dominio.maquinas.excepciones import LaboratorioInvalido
from compulab.dominio.maquinas.maquina import Maquina


class Laboratorio:
    """Laboratorio con un número fijo de máquinas, cada una con identificador único."""

    def __init__(self, id: str, nombre: str, campus: str, maquinas: Iterable[Maquina]) -> None:
        maquinas = tuple(maquinas)
        if not id or not nombre or not campus:
            raise LaboratorioInvalido("El laboratorio necesita id, nombre y campus")
        if not maquinas:
            raise LaboratorioInvalido("El laboratorio debe tener al menos una máquina")
        identificadores = [m.identificador for m in maquinas]
        if len(set(identificadores)) != len(identificadores):
            raise LaboratorioInvalido("Hay identificadores de máquina repetidos")
        if any(m.laboratorio_id != id for m in maquinas):
            raise LaboratorioInvalido("Todas las máquinas deben pertenecer a este laboratorio")
        self._id = id
        self._nombre = nombre
        self._campus = campus
        self._maquinas = maquinas

    @property
    def id(self) -> str:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def campus(self) -> str:
        return self._campus

    @property
    def maquinas(self) -> tuple[Maquina, ...]:
        return self._maquinas

    def maquina(self, maquina_id: str) -> Maquina:
        for m in self._maquinas:
            if m.id == maquina_id:
                return m
        raise LaboratorioInvalido(f"La máquina {maquina_id} no es de este laboratorio")

    def en_servicio(self) -> tuple[Maquina, ...]:
        return tuple(m for m in self._maquinas if m.en_servicio)
