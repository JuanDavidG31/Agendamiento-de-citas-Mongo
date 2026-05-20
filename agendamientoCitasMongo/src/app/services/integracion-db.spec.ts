import { TestBed } from '@angular/core/testing';

import { IntegracionDb } from './integracion-db';

describe('IntegracionDb', () => {
  let service: IntegracionDb;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(IntegracionDb);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
