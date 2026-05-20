import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-agendamiento-citas',
  standalone: false,
  templateUrl: './agendamiento-citas.html',
  styleUrls: ['./agendamiento-citas.scss']
})
export class AgendamientoCitasComponent {
  citaForm: FormGroup;
  mensajeExito: string = '';
  mensajeError: string = '';

  // Datos de prueba simulando lo que llegará de PostgreSQL
  medicos = [
    { id: 1, nombre: 'Dr. Diego Bonza', especialidad: 'Cardiología' },
    { id: 2, nombre: 'Dr. Juan Camilo Beltrán', especialidad: 'Medicina General' }
  ];

  pacientes = [
    { id: 101, documento: '10102020', nombre: 'Ana María Gómez' },
    { id: 102, documento: '20203030', nombre: 'Juan Pablo Cuervo' }
  ];

  constructor(private fb: FormBuilder) {
    this.citaForm = this.fb.group({
      id_paciente: ['', Validators.required],
      id_medico: ['', Validators.required],
      fecha_hora: ['', Validators.required],
      consultorio: ['A-201', Validators.required]
    });
  }

  agendarCita() {
    if (this.citaForm.valid) {
      const datosCita = this.citaForm.value;

      // Aquí simularemos la restricción UNIQUE(ID_Medico, Fecha_Hora) de su Avance 1
      console.log('Enviando al backend (PostgreSQL):', datosCita);

      // Simulación de respuesta del script de integración
      this.mensajeExito = '¡Transacción exitosa! Cita agendada y bloqueada en PostgreSQL.';
      this.mensajeError = '';
      this.citaForm.reset({ consultorio: 'A-201' });

      // Ocultar mensaje después de 3 segundos
      setTimeout(() => this.mensajeExito = '', 3000);
    } else {
      this.mensajeError = 'Por favor complete todos los campos para garantizar la integridad referencial.';
    }
  }
}
