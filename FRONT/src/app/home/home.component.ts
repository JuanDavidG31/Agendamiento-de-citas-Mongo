import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-home',
  standalone:false,
  templateUrl: './home.html',
  styleUrls: ['./home.scss'] // o .css según tu config
})
export class HomeComponent implements OnInit {

  // 1. Declaramos la propiedad para que el HTML la reconozca
  public estadisticas = {
    citasHoy: 0,
    pacientesActivos: 0,
    historiasClinicas: 0
  };

  constructor() { }

  ngOnInit(): void {
    // 2. Aquí simularías traer los datos de un servicio de la clínica.
    // Por ahora, le asignamos valores de prueba para que los veas en pantalla:
    this.estadisticas = {
      citasHoy: 12,              // Aparecerá en {{ estadisticas.citasHoy }}
      pacientesActivos: 145,     // Aparecerá en {{ estadisticas.pacientesActivos }}
      historiasClinicas: 1204    // Aparecerá en {{ estadisticas.historiasClinicas }}
    };
  }

}
