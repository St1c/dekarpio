import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfigsManagementComponent } from './configs-management.component';

describe('ConfigsManagementComponent', () => {
  let component: ConfigsManagementComponent;
  let fixture: ComponentFixture<ConfigsManagementComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ ConfigsManagementComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ConfigsManagementComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
