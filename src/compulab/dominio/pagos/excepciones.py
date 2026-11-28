"""Excepciones del pago: las reglas que puede romper el cierre del mes."""

from compulab.dominio.compartido.excepciones import ErrorDeDominio


class MarcaInvalida(ErrorDeDominio):
    """La marca no cumple que la salida sea posterior a la entrada."""


class LineaPagoInvalida(ErrorDeDominio):
    """La línea de pago tiene horas negativas o una tarifa que no es mayor que 0."""


class CierreInmutable(ErrorDeDominio):
    """Se intentó construir un cierre inválido o cambiar uno ya cerrado."""


class MesYaCerrado(ErrorDeDominio):
    """El mes ya tiene un cierre; no se vuelve a calcular."""


class MesNoTerminado(ErrorDeDominio):
    """Se pidió cerrar un mes que todavía no ha terminado."""


class TarifaInvalida(ErrorDeDominio):
    """La tarifa no es mayor que 0, no tiene categoría o el recargo es negativo."""


class TarifaNoConfigurada(ErrorDeDominio):
    """No hay tarifa o recargo vigente para la categoría y la fecha pedidas."""
