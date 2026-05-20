import { Component, OnInit } from '@angular/core';


interface HistoriaClinica {
  _id: string;
  id_paciente_sql: number;
  id_cita_sql: number; // <-- NUEVO: El puente directo con el agendamiento
  fecha_registro: string;
  medico_tratante: string;
  motivo_consulta: string;
  signos_vitales: {
    presion: string;
    ritmo_cardiaco: number;
  };
  notas_evolucion: string;
  archivos_adjuntos?: string[];
  diagnostico_codigo?: string; // Campo variable para demostrar esquema flexible
}

@Component({
  selector: 'app-historias-clinicas',
  standalone: false,
  templateUrl: './historias-clinicas.html',
  styleUrls: ['./historias-clinicas.scss']
})
export class HistoriasClinicasComponent implements OnInit {
  // Colección principal con datos de prueba (Simulación de 50-100 docs en MongoDB)
  historiasCompletas: HistoriaClinica[] = [
    {
      _id: '65dfa112b3c4d5e6f7000001',
      id_paciente_sql: 101,
      id_cita_sql: 5001, // <-- La cita programada en Postgres
      fecha_registro: '2026-05-15T11:00:00Z',
      medico_tratante: 'Dr. Diego Bonza',
      motivo_consulta: 'Dolor torácico agudo',
      signos_vitales: { presion: '120/80', ritmo_cardiaco: 75 },
      notas_evolucion: 'Paciente estable, se recomienda electrocardiograma de control urgente.',
      archivos_adjuntos: ['radiografia_torax.png', 'electrocardiograma.pdf']
    },
    {
      _id: '65dfa223c4d5e6f7a8000002',
      id_paciente_sql: 102,
      id_cita_sql: 5001, // <-- La cita programada en Postgres
      fecha_registro: '2026-05-16T09:30:00Z',
      medico_tratante: 'Dr. Juan Camilo Beltrán',
      motivo_consulta: 'Control de hipertensión',
      signos_vitales: { presion: '145/95', ritmo_cardiaco: 94 },
      notas_evolucion: 'Se evidencia presión arterial elevada. Se realiza ajuste en la dosis de los medicamentos.',
      diagnostico_codigo: 'I10 - Hipertensión esencial' // Esquema flexible (no todos lo tienen)
    },
    {
      _id: '65dfa334d5e6f7a8b9000003',
      id_paciente_sql: 101,
      id_cita_sql: 5001, // <-- La cita programada en Postgres
      fecha_registro: '2026-05-18T14:15:00Z',
      medico_tratante: 'Dr. Diego Bonza',
      motivo_consulta: 'Revisión de exámenes',
      signos_vitales: { presion: '118/75', ritmo_cardiaco: 68 },
      notas_evolucion: 'Resultados de radiografía normales. Paciente evoluciona favorablemente sin dolor.',
      archivos_adjuntos: ['laboratorio_sangre.pdf']
    }
  ];

  historiasFiltradas: any[] = [];
  consultaSeleccionada: string = 'todos';
  filtroPacienteId: number | null = null;

  ngOnInit() {
    this.ejecutarConsulta();
  }

  ejecutarConsulta() {
    switch (this.consultaSeleccionada) {
      case 'todos':
        // Muestra los documentos completos
        this.historiasFiltradas = JSON.parse(JSON.stringify(this.historiasCompletas));
        break;

      case 'filtro_paciente':
        // Consulta 1: Filtro por llave de referencia cruzada con PostgreSQL (id_paciente_sql)
        if (this.filtroPacienteId) {
          this.historiasFiltradas = this.historiasCompletas.filter(
            h => h.id_paciente_sql === this.filtroPacienteId
          );
        } else {
          this.historiasFiltradas = [];
        }
        break;

      case 'signos_criticos':
        // Consulta 2: Filtro/Agregación por subdocumento interno (Ritmo cardiaco elevado > 90)
        this.historiasFiltradas = this.historiasCompletas.filter(
          h => h.signos_vitales.ritmo_cardiaco > 90
        );
        break;

      case 'proyeccion_archivos':
        // Consulta 3: Proyección (Muestra únicamente _id, fecha, paciente y el arreglo de archivos_adjuntos)
        this.historiasFiltradas = this.historiasCompletas.map(h => ({
          _id: h._id,
          id_paciente_sql: h.id_paciente_sql,
          fecha_registro: h.fecha_registro,
          archivos_adjuntos: h.archivos_adjuntos || ['Ninguno']
        }));
        break;
    }
  }
}
