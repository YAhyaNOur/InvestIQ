import { TestBed } from '@angular/core/testing';

import { Investor } from './investor';

describe('Investor', () => {
  let service: Investor;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Investor);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
