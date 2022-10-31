import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfigFormControlComponent } from './config-form-control.component';

describe('ConfigFormControlComponent', () => {
  let component: ConfigFormControlComponent;
  let fixture: ComponentFixture<ConfigFormControlComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ConfigFormControlComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfigFormControlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
