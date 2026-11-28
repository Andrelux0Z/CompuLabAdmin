# CompuLabAdmin

Sistema para administrar los laboratorios de cómputo de la Escuela de Computación del TEC. Hoy el horario vive en una hoja compartida, los cambios de turno se acuerdan por mensajería y las máquinas se usan por orden de llegada; eso deja turnos sin cubrir, horas que no coinciden con las trabajadas, asistentes que pasan el tope de su beca sin enterarse y estudiantes que llegan y no encuentran máquina. CompuLabAdmin ordena cuatro procesos: reclutamiento de asistentes, horario de turnos, uso de máquinas y pago mensual.

Este repositorio contiene el **núcleo ejecutable**: el dominio, tres casos de uso completos, sus pruebas con dobles y las pantallas de demostración. El diseño completo (requerimientos, arquitectura, decisiones, base de datos y UX/UI) está en [`docs/CompuLabAdmin_documento_diseno.docx`](docs/CompuLabAdmin_documento_diseno.docx).

## Qué hace

| Caso de uso | Quién lo usa | Reglas que aplica |
|---|---|---|
| **Asignar turno** (CU-07) | Coordinador de laboratorio o de soporte | El coordinador solo modifica su laboratorio; el asistente debe estar activo; el turno no se traslapa con otro suyo en ningún laboratorio o campus; no se pasa del tope semanal; cae en un bloque que el asistente declaró, o él aceptó trabajarlo fuera. |
| **Reservar máquina** (CU-13) | Estudiante | Máximo 2 h por reserva; el laboratorio debe estar abierto (cubierto por turnos); la máquina debe estar libre y en servicio; una sola reserva activa por estudiante y máximo 6 h por semana. La reserva se libera si el estudiante no se presenta en 15 minutos. |
| **Cerrar mes** (CU-18) | Planificador (día 1) o coordinador de soporte | Calcula horas normales y con recargo (turnos que empiezan a las 18:00 o después, o en fin de semana; un solo recargo); las horas sobre el tope son las últimas de cada semana y se registran sin pagar; aplica la tarifa de la categoría; guarda un cierre inmutable y genera el archivo CSV para Becas. |

Todas las fechas se manejan en hora de Costa Rica (UTC−6) y las horas y el dinero con `Decimal`, sin redondeos intermedios.

## Requisitos

- Python 3.12
- Un navegador, para ver las pantallas

No hace falta base de datos ni servidor: el núcleo corre con dobles en memoria.

## Instalación y pruebas

Desde la carpeta del proyecto:

```
python -m venv .venv
.venv\Scripts\activate          # en Linux o macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest                          # corre todas las pruebas
lint-imports                    # verifica la regla de capas
```

`pytest` corre tres grupos de pruebas:

- **Dominio:** objetos valor, entidades, reglas y calculadora de pago.
- **Casos de uso:** una prueba por cada poscondición (P) y por cada extensión (E) de los contratos CU-07, CU-13 y CU-18, con los nombres de la sección 11.2 del documento de diseño.
- **Funciones de aptitud:** revisan que el dominio no importe las capas de afuera y que no use red, archivos ni el reloj del sistema. Cada una se prueba también contra una violación plantada a propósito.

Para correr solo un grupo: `pytest tests/dominio`, `pytest tests/aplicacion` o `pytest tests/aptitud`.

## Pantallas

Abrir `frontend/pantallas/index.html` en el navegador. Son pantallas de demostración con datos fijos, sin conexión a la base de datos:

- **Horario semanal:** el coordinador arma turnos y ve en vivo qué celdas rompen una regla.
- **Reservar máquina:** pensada para el celular del estudiante; solo muestra franjas abiertas y máquinas libres.
- **Cierre de mes:** pago por asistente, horas sin pagar y descarga del CSV para Becas.

## Estructura

```
src/compulab/
  dominio/              reglas del negocio, sin dependencias externas
    compartido/         Franja, Semana, Reloj y excepciones base
    horario/            Asistente, Turno, AgendaSemanal y reglas de turno
    maquinas/           Laboratorio, Maquina, Reserva y PoliticaReservas
    pagos/              Tarifa, Recargo, CalculadoraEstandar y CierreMensual
  aplicacion/           casos de uso: AsignarTurno, ReservarMaquina y CerrarMes
  infraestructura/      adaptadores reales (exportador CSV para Becas)
tests/
  dominio/  aplicacion/  aptitud/  infraestructura/
  apoyo_*.py            fábricas de datos y dobles en memoria
frontend/pantallas/     pantallas de demostración (HTML, CSS y JS)
docs/                   documento de diseño
```

## Arquitectura

Arquitectura hexagonal en tres capas: `infraestructura → aplicación → dominio`. Cada capa solo importa las que están debajo, y la regla la verifican `lint-imports` y las funciones de aptitud. El dominio habla con el exterior a través de puertos (`Protocol`) inyectados en los casos de uso: repositorios, reloj, notificador, configuración de tarifas y exportador. En las pruebas esos puertos se reemplazan por dobles (`RelojFijo`, repositorios en memoria y espías), así que todo corre en menos de un segundo y siempre da el mismo resultado.

La API, los repositorios sobre PostgreSQL, el outbox de eventos, la réplica de la base de datos y los demás casos de uso están diseñados en el documento, pero no forman parte de este núcleo.

## Equipo
Alina Rodriguez Wong y Andres Padilla Robles