"""Caso de uso CU-18 Cerrar mes."""

from __future__ import annotations

from datetime import date

from compulab.aplicacion.puertos_pago import ExportadorPago
from compulab.dominio.compartido import Franja, Semana
from compulab.dominio.compartido.reloj import Reloj
from compulab.dominio.pagos import (
    MesNoTerminado,
    MesYaCerrado,
    Recargo,
    Tarifa,
    TarifaNoConfigurada,
)
from compulab.dominio.pagos.calculadora import CalculadoraEstandar, CalculadoraPago, es_del_mes
from compulab.dominio.pagos.cierre import CierreMensual, franja_del_mes
from compulab.dominio.pagos.puertos import (
    ConfiguracionTarifas,
    ConsultaMarcas,
    Notificador,
    RepositorioCierres,
)

COORDINACION_DE_SOPORTE = "coordinacion-soporte"


class CerrarMes:
    def __init__(
        self,
        reloj: Reloj,
        cierres: RepositorioCierres,
        marcas: ConsultaMarcas,
        configuracion: ConfiguracionTarifas,
        exportador: ExportadorPago,
        notificador: Notificador,
        calculadora: CalculadoraPago | None = None,
    ) -> None:
        self._reloj = reloj
        self._cierres = cierres
        self._marcas = marcas
        self._configuracion = configuracion
        self._exportador = exportador
        self._notificador = notificador
        self._calculadora = calculadora or CalculadoraEstandar()

    def ejecutar(self, anio: int, mes: int) -> CierreMensual:
        mes_completo = franja_del_mes(anio, mes)
        if self._reloj.ahora() < mes_completo.fin:                         # E2
            raise MesNoTerminado(f"{anio}-{mes:02d} todavía no ha terminado")
        if self._cierres.existe(anio, mes):                                # E1
            raise MesYaCerrado(f"{anio}-{mes:02d} ya está cerrado; agregue una constancia")

        # Las tarifas y el recargo que valen para el mes son los vigentes el día 1.
        vigencia = mes_completo.inicio.date()
        recargo = self._recargo_vigente(vigencia)                          # E6

        # Paso 2: marcas del mes y, de la primera semana, los días del mes anterior (E8).
        primera_semana = Semana.de_momento(mes_completo.inicio)
        marcas = self._marcas.de_franja(Franja(primera_semana.franja.inicio, mes_completo.fin))
        del_mes = [marca for marca in marcas if es_del_mes(marca, anio, mes)]
        tarifas = {c: self._tarifa_vigente(c, vigencia)                     # E6
                   for c in sorted({marca.categoria for marca in del_mes})}

        lineas = self._calculadora.calcular(                               # pasos 3 a 5
            anio, mes, marcas, tarifas.__getitem__, recargo)
        cierre = CierreMensual(anio, mes, lineas)                          # P1, P2, P5

        self._cierres.guardar(cierre)
        self._exportador.exportar(anio, mes, cierre.lineas)                # P4
        self._notificar_horas_sobre_tope(cierre)                           # P3, E5
        self._notificar_marcas_sin_salida(del_mes)                         # E4
        return cierre

    def _recargo_vigente(self, fecha: date) -> Recargo:
        recargo = self._configuracion.recargo_vigente(fecha)
        if recargo is None:
            raise TarifaNoConfigurada(f"no hay recargo vigente el {fecha}")
        return recargo

    def _tarifa_vigente(self, categoria: str, fecha: date) -> Tarifa:
        tarifa = self._configuracion.tarifa_vigente(categoria, fecha)
        if tarifa is None:
            raise TarifaNoConfigurada(f"no hay tarifa vigente para {categoria} el {fecha}")
        return tarifa

    def _notificar_horas_sobre_tope(self, cierre: CierreMensual) -> None:
        for linea in cierre.lineas_con_horas_sobre_tope():
            self._notificador.notificar(
                COORDINACION_DE_SOPORTE,
                f"{cierre.anio}-{cierre.mes:02d}: {linea.asistente_id} trabajó "
                f"{linea.horas_sobre_tope.normalize():f} h sobre su tope; "
                "quedan registradas sin pagar.",
            )

    def _notificar_marcas_sin_salida(self, marcas) -> None:
        for marca in marcas:
            if marca.sin_salida:
                self._notificador.notificar(
                    COORDINACION_DE_SOPORTE,
                    f"{marca.asistente_id} no marcó salida en el turno del "
                    f"{marca.inicio_turno:%Y-%m-%d %H:%M}; se pagó hasta el fin programado.",
                )
