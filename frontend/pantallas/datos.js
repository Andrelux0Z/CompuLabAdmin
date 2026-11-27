// Datos fijos de demostración: el front no se conecta a la base de datos.
const DATOS = {
  semana: { lunes: "2026-11-23", etiqueta: "Semana del 23 al 29 de noviembre de 2026" },
  dias: ["Lun 23", "Mar 24", "Mié 25", "Jue 26", "Vie 27", "Sáb 28", "Dom 29"],
  laboratorios: [
    { id: "LAB1", nombre: "Laboratorio 1", campus: "Cartago" },
    { id: "LAB2", nombre: "Laboratorio 2", campus: "Cartago" },
    { id: "LAB3", nombre: "Laboratorio 3", campus: "San José" },
  ],
  asistentes: [
    { id: "A1", nombre: "Ana Mora", categoria: "A", tope: 20,
      disponibilidad: { 0: [7, 13], 1: [7, 13], 2: [7, 13], 3: [7, 13], 4: [7, 13] } },
    { id: "A2", nombre: "Luis Vargas", categoria: "B", tope: 20,
      disponibilidad: { 0: [13, 21], 1: [13, 21], 2: [13, 21], 5: [8, 14] } },
    { id: "A3", nombre: "Sofía Rojas", categoria: "A", tope: 28,
      disponibilidad: { 2: [13, 21], 3: [13, 21], 4: [13, 21], 6: [8, 14] } },
    { id: "A4", nombre: "Diego Solís", categoria: "B", tope: 16,
      disponibilidad: { 0: [7, 12], 3: [7, 12], 4: [7, 12] } },
  ],
  // dia: 0 = lunes. Horas enteras. estado: cubierto | ofrecido | sin-asignar | no-cubierto
  turnos: [
    { lab: "LAB1", dia: 0, inicio: 7, fin: 13, asistente: "A1", estado: "cubierto" },
    { lab: "LAB1", dia: 0, inicio: 13, fin: 18, asistente: "A2", estado: "cubierto" },
    { lab: "LAB1", dia: 1, inicio: 7, fin: 13, asistente: "A1", estado: "no-cubierto" },
    { lab: "LAB1", dia: 1, inicio: 13, fin: 21, asistente: "A2", estado: "ofrecido" },
    { lab: "LAB1", dia: 2, inicio: 7, fin: 13, asistente: "A1", estado: "cubierto" },
    { lab: "LAB1", dia: 2, inicio: 13, fin: 21, asistente: "A3", estado: "cubierto" },
    { lab: "LAB1", dia: 3, inicio: 7, fin: 12, asistente: "A4", estado: "cubierto" },
    { lab: "LAB1", dia: 3, inicio: 13, fin: 21, asistente: null, estado: "sin-asignar" },
    { lab: "LAB1", dia: 4, inicio: 7, fin: 12, asistente: "A4", estado: "cubierto" },
    { lab: "LAB1", dia: 4, inicio: 13, fin: 21, asistente: "A3", estado: "cubierto" },
    { lab: "LAB1", dia: 5, inicio: 8, fin: 14, asistente: "A2", estado: "cubierto" },
    { lab: "LAB2", dia: 0, inicio: 7, fin: 12, asistente: "A4", estado: "cubierto" },
    { lab: "LAB3", dia: 6, inicio: 8, fin: 12, asistente: "A3", estado: "cubierto" },
  ],
  maquinas: {
    LAB1: Array.from({ length: 12 }, (_, i) => ({ id: `PC-${String(i + 1).padStart(2, "0")}`,
      enServicio: ![4, 9].includes(i + 1) })),
  },
  // Reservas ya existentes en LAB1 (dia, inicio y fin en horas decimales)
  reservas: [
    { maquina: "PC-01", dia: 1, inicio: 14, fin: 16 }, { maquina: "PC-02", dia: 1, inicio: 15, fin: 17 },
    { maquina: "PC-03", dia: 2, inicio: 8, fin: 10 }, { maquina: "PC-06", dia: 2, inicio: 9, fin: 11 },
    { maquina: "PC-07", dia: 4, inicio: 16, fin: 18 },
  ],
  estudiante: { nombre: "María Pérez", horasSemana: 4, reservaActiva: null },
  cierre: {
    anio: 2026, mes: 10, etiqueta: "Octubre 2026", cerradoEn: "1 de noviembre de 2026, 00:05",
    tarifas: { A: 2500, B: 2000 }, recargo: 0.25,
    lineas: [
      { id: "A1", nombre: "Ana Mora", categoria: "A", normales: 72, recargo: 0, sobreTope: 0 },
      { id: "A2", nombre: "Luis Vargas", categoria: "B", normales: 30, recargo: 18, sobreTope: 2 },
      { id: "A3", nombre: "Sofía Rojas", categoria: "A", normales: 40, recargo: 22, sobreTope: 0 },
      { id: "A4", nombre: "Diego Solís", categoria: "B", normales: 38, recargo: 0, sobreTope: 0 },
    ],
    constancias: [
      { fecha: "5 nov 2026", autor: "Coord. de soporte", texto: "Ajuste de 1 h a Diego Solís pagado por fuera del sistema (marca de salida olvidada el 14 oct)." },
    ],
  },
};
const ESTADOS = {
  "cubierto": { texto: "Cubierto", icono: "✓" },
  "ofrecido": { texto: "Ofrecido", icono: "⇄" },
  "sin-asignar": { texto: "Sin asignar", icono: "!" },
  "no-cubierto": { texto: "No cubierto", icono: "✕" },
};
const hora = h => `${String(Math.floor(h)).padStart(2, "0")}:${String(Math.round((h % 1) * 60)).padStart(2, "0")}`;
const colones = n => "₡" + n.toLocaleString("es-CR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
