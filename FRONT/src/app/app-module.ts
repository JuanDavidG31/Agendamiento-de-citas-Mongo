import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing-module';
import { App } from './app';

import { HomeComponent } from './home/home.component';
import { HistoriasClinicasComponent } from './historias-clinicas/historias-clinicas';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AgendamientoCitasComponent } from './agendamiento-citas/agendamiento-citas';
import { Pacientes } from './pacientes/pacientes';
import { Footer } from './core/footer/footer';
import { Header } from './core/header/header';
import { Login } from './login/login';
import { Register } from './register/register';

@NgModule({
  declarations: [
    App,
    HomeComponent,
    HistoriasClinicasComponent,
    AgendamientoCitasComponent,
    Pacientes,
    Footer,
    Header,
    Login,
    Register,
  ],
  imports: [BrowserModule, AppRoutingModule, ReactiveFormsModule, FormsModule, CommonModule],
  providers: [provideBrowserGlobalErrorListeners()],
  bootstrap: [App],
})
export class AppModule {}
