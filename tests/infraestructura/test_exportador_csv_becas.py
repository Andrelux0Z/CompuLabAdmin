import csv
from decimal import Decimal

import pytest

from compulab.dominio.pagos import LineaPago
from compulab.infraestructura.exportador_csv_becas import COLUMNAS, ExportadorCsvBecas

LINEAS = [
    LineaPago("A2", Decimal("10"), Decimal("4.5"), Decimal("0"), Decimal("33187.5")),
    LineaPago("A1", Decimal("12.25"), Decimal("0"), Decimal("2"), Decimal("24500.004")),
]


def test_cierre_genera_archivo_csv_para_becas(tmp_path):
    ruta = ExportadorCsvBecas(tmp_path).exportar(2026, 11, LINEAS)

    assert ruta.endswith("becas_2026_11.csv")
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.reader(f))
    assert filas[0] == COLUMNAS
    assert filas[1:] == [
        ["2026", "11", "A1", "12.25", "0.00", "2.00", "24500.00"],
        ["2026", "11", "A2", "10.00", "4.50", "0.00", "33187.50"],
    ]


def test_no_sobrescribe_un_mes_ya_exportado(tmp_path):
    exportador = ExportadorCsvBecas(tmp_path)
    exportador.exportar(2026, 11, LINEAS)
    with pytest.raises(FileExistsError):
        exportador.exportar(2026, 11, LINEAS)


def test_cierre_sin_lineas_solo_tiene_encabezado():
    assert ExportadorCsvBecas.contenido(2026, 1, []) == ",".join(COLUMNAS) + "\n"
