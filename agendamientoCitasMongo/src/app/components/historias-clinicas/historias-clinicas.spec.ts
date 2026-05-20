import { ComponentFixture, TestBed } from '@angular/core/testing';

// 1. Corregimos la ruta del archivo y el nombre exacto de la clase
import { HistoriasClinicasComponent } from './historias-clinicas';

describe('HistoriasClinicasComponent', () => {
  let component: HistoriasClinicasComponent;
  let fixture: ComponentFixture<HistoriasClinicasComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      // 2. Actualizamos el import del módulo de pruebas
      imports: [HistoriasClinicasComponent],
    }).compileComponents();

    // 3. Actualizamos la creación del componente
    fixture = TestBed.createComponent(HistoriasClinicasComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});