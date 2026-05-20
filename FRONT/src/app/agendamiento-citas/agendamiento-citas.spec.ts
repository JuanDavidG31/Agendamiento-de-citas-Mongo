import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgendamientoCitas } from './agendamiento-citas';

describe('AgendamientoCitas', () => {
  let component: AgendamientoCitas;
  let fixture: ComponentFixture<AgendamientoCitas>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgendamientoCitas],
    }).compileComponents();

    fixture = TestBed.createComponent(AgendamientoCitas);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
