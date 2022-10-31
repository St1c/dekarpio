import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EnergySourcesComponent } from './energy-sources.component';

describe('EnergySourcesComponent', () => {
  let component: EnergySourcesComponent;
  let fixture: ComponentFixture<EnergySourcesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EnergySourcesComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EnergySourcesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
