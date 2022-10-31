import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EnergyStoragesComponent } from './energy-storages.component';

describe('EnergyStoragesComponent', () => {
  let component: EnergyStoragesComponent;
  let fixture: ComponentFixture<EnergyStoragesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EnergyStoragesComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EnergyStoragesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
