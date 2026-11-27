"""Cada función de aptitud se prueba dos veces: sobre el código real (debe estar
limpio) y sobre un paquete falso con una violación plantada (debe encontrarla)."""
from pathlib import Path

from reglas_aptitud import efectos_en_dominio, imports_entre_capas


def _paquete_falso(tmp_path: Path, archivos: dict[str, str]) -> Path:
    paquete = tmp_path / "compulab"
    for ruta, codigo in archivos.items():
        destino = paquete / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(codigo, encoding="utf-8")
    return paquete


# --- Función de aptitud 1: regla de dependencia entre capas -----------------

def test_dominio_no_importa_aplicacion_ni_infraestructura():
    violaciones = imports_entre_capas()
    assert violaciones == [], "\n".join(map(str, violaciones))


def test_detecta_import_prohibido_plantado(tmp_path):
    paquete = _paquete_falso(tmp_path, {
        "dominio/turno.py": "from compulab.infraestructura.bd import Sesion\n",
        "dominio/reserva.py": "from ..aplicacion import reservar\n",
        "aplicacion/caso.py": "import sqlalchemy\n",
        "dominio/limpio.py": "from compulab.dominio.comun.tiempo import Franja\n",
    })
    encontradas = {(v.archivo, v.linea) for v in imports_entre_capas(paquete)}
    assert encontradas == {
        ("compulab/dominio/turno.py", 1),
        ("compulab/dominio/reserva.py", 1),
        ("compulab/aplicacion/caso.py", 1),
    }


# --- Función de aptitud 2: dominio sin red, archivos ni reloj real ----------

def test_dominio_no_usa_reloj_red_ni_archivos():
    violaciones = efectos_en_dominio()
    assert violaciones == [], "\n".join(map(str, violaciones))


def test_detecta_datetime_now_plantado(tmp_path):
    paquete = _paquete_falso(tmp_path, {
        "dominio/reloj.py": "from datetime import datetime\n\ndef hoy():\n    return datetime.now()\n",
        "dominio/red.py": "import requests\n",
        "dominio/archivo.py": "def leer():\n    return open('x.txt').read()\n",
        "dominio/tiempo.py": "import time\n\ndef t():\n    return time.time()\n",
        "dominio/limpio.py": "from datetime import timedelta\nDOS_HORAS = timedelta(hours=2)\n",
    })
    encontradas = {(v.archivo, v.linea) for v in efectos_en_dominio(paquete)}
    assert encontradas == {
        ("compulab/dominio/reloj.py", 4),
        ("compulab/dominio/red.py", 1),
        ("compulab/dominio/archivo.py", 2),
        ("compulab/dominio/tiempo.py", 4),
    }
