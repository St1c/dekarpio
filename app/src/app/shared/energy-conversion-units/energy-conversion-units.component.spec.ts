import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EnergyConversionUnitsComponent } from './energy-conversion-units.component';

describe('EnergyConversionUnitsComponent', () => {
  let component: EnergyConversionUnitsComponent;
  let fixture: ComponentFixture<EnergyConversionUnitsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EnergyConversionUnitsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EnergyConversionUnitsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
