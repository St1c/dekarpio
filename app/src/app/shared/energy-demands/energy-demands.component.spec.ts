import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EnergyDemandsComponent } from './energy-demands.component';

describe('EnergyDemandsComponent', () => {
  let component: EnergyDemandsComponent;
  let fixture: ComponentFixture<EnergyDemandsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EnergyDemandsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EnergyDemandsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
