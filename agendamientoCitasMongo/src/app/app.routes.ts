import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home';
import { AgendamientoCitasComponent } from './components/agendamiento-citas/agendamiento-citas';
import { HistoriasClinicasComponent } from './components/historias-clinicas/historias-clinicas';

export const routes: Routes = [
    {
        path: '',
        redirectTo: '/home',
        pathMatch: 'full'
    },
    {
        path: 'home',
        component: HomeComponent
    },
    {
        path: 'agendar',
        component: AgendamientoCitasComponent
    },
    {
        path: 'historias',
        component: HistoriasClinicasComponent
    }
];