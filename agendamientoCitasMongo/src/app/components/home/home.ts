import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.html',
  styleUrls: ['./home.css']
})
export class HomeComponent {
  // Datos e indicadores simulados del complejo hospitalario
  estadisticas = {
    citasHoy: 12,
    pacientesActivos: 85,
    historiasClinicas: 150
  };
}