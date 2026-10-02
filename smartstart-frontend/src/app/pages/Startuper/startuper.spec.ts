import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Startuper } from './startuper';

describe('Startuper', () => {
  let component: Startuper;
  let fixture: ComponentFixture<Startuper>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Startuper],
    }).compileComponents();

    fixture = TestBed.createComponent(Startuper);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
