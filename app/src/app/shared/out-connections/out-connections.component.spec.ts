import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OutConnectionsComponent } from './out-connections.component';

describe('OutConnectionsComponent', () => {
  let component: OutConnectionsComponent;
  let fixture: ComponentFixture<OutConnectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ OutConnectionsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(OutConnectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
