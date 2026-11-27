"""Funciones de aptitud: verifican propiedades del diseño leyendo el código
fuente (AST), sin importarlo. Si encuentran violaciones, las pruebas de
tests/aptitud/ fallan y con ellas el build. Complementan el contrato de capas
de import-linter (pyproject.toml) con pruebas que plantan una violación."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PAQUETE = RAIZ / "src" / "compulab"

# Regla de dependencia entre capas: cada capa solo puede importar hacia adentro.
PROHIBIDOS_POR_CAPA = {
    "dominio": ("compulab.aplicacion", "compulab.infraestructura",
                "fastapi", "sqlalchemy", "psycopg"),
    "aplicacion": ("compulab.infraestructura", "fastapi", "sqlalchemy", "psycopg"),
}

# Efectos que el dominio no puede tener: red, archivos, sistema operativo, reloj real.
MODULOS_CON_EFECTOS = ("socket", "requests", "urllib", "http", "os", "pathlib",
                       "shutil", "subprocess", "sqlite3")
METODOS_DE_RELOJ = ("now", "utcnow", "today")
FUNCIONES_DE_TIEMPO = ("time", "monotonic", "perf_counter")


@dataclass(frozen=True)
class Violacion:
    archivo: str
    linea: int
    detalle: str

    def __str__(self) -> str:
        return f"{self.archivo}:{self.linea}: {self.detalle}"


def _archivos(carpeta: Path):
    return sorted(p for p in carpeta.rglob("*.py") if "__pycache__" not in p.parts)


def _modulo_de(archivo: Path, raiz: Path) -> list[str]:
    return list(archivo.relative_to(raiz).with_suffix("").parts)


def _importados(arbol: ast.AST, partes_modulo: list[str]):
    """(línea, nombre absoluto) de cada import, resolviendo imports relativos."""
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield nodo.lineno, alias.name
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                base = partes_modulo[:-nodo.level]
                nombre = ".".join(base + ([nodo.module] if nodo.module else []))
            else:
                nombre = nodo.module or ""
            yield nodo.lineno, nombre


def _coincide(nombre: str, prefijo: str) -> bool:
    return nombre == prefijo or nombre.startswith(prefijo + ".")


def imports_entre_capas(paquete: Path = PAQUETE) -> list[Violacion]:
    """Función de aptitud 1: regla de dependencia entre capas."""
    violaciones = []
    raiz = paquete.parent
    for capa, prohibidos in PROHIBIDOS_POR_CAPA.items():
        carpeta = paquete / capa
        if not carpeta.exists():
            continue
        for archivo in _archivos(carpeta):
            arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
            for linea, nombre in _importados(arbol, _modulo_de(archivo, raiz)):
                for prefijo in prohibidos:
                    if _coincide(nombre, prefijo):
                        violaciones.append(Violacion(
                            archivo.relative_to(raiz).as_posix(), linea,
                            f"la capa '{capa}' no puede importar '{nombre}'"))
    return violaciones


def efectos_en_dominio(paquete: Path = PAQUETE) -> list[Violacion]:
    """Función de aptitud 2: el dominio no usa red, archivos ni reloj real."""
    violaciones = []
    raiz = paquete.parent
    carpeta = paquete / "dominio"
    for archivo in _archivos(carpeta):
        ruta = archivo.relative_to(raiz).as_posix()
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        for linea, nombre in _importados(arbol, _modulo_de(archivo, raiz)):
            if any(_coincide(nombre, m) for m in MODULOS_CON_EFECTOS):
                violaciones.append(Violacion(ruta, linea, f"importa '{nombre}' (efecto externo)"))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            funcion = nodo.func
            if isinstance(funcion, ast.Name) and funcion.id == "open":
                violaciones.append(Violacion(ruta, nodo.lineno, "abre archivos con open()"))
            elif isinstance(funcion, ast.Attribute):
                if funcion.attr in METODOS_DE_RELOJ:
                    violaciones.append(Violacion(
                        ruta, nodo.lineno, f"lee el reloj real con .{funcion.attr}(); use el puerto Reloj"))
                elif (funcion.attr in FUNCIONES_DE_TIEMPO and isinstance(funcion.value, ast.Name)
                      and funcion.value.id == "time"):
                    violaciones.append(Violacion(
                        ruta, nodo.lineno, f"lee el reloj real con time.{funcion.attr}()"))
    return violaciones
