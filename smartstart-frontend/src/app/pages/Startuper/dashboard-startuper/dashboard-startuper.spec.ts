import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardStartuper } from './dashboard-startuper';

describe('DashboardStartuper', () => {
  let component: DashboardStartuper;
  let fixture: ComponentFixture<DashboardStartuper>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardStartuper],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardStartuper);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
