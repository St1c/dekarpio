import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SimulationSetupComponent } from './simulation-setup.component';

describe('SimulationSetupComponent', () => {
  let component: SimulationSetupComponent;
  let fixture: ComponentFixture<SimulationSetupComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SimulationSetupComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SimulationSetupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
