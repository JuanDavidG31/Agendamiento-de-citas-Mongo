import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {HomeComponent} from './home/home.component';
import {AgendamientoCitasComponent} from './agendamiento-citas/agendamiento-citas';
import {Pacientes} from './pacientes/pacientes';
import {HistoriasClinicasComponent} from './historias-clinicas/historias-clinicas';

const routes: Routes = [
  {path: '', component: HomeComponent},
  {path:'agendamiento', component:AgendamientoCitasComponent},
  {path:'paciente',component:Pacientes},
  {path:'historia-clinica',component:HistoriasClinicasComponent}

];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {  }
