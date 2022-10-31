import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InConnectionsComponent } from './in-connections.component';

describe('InConnectionsComponent', () => {
  let component: InConnectionsComponent;
  let fixture: ComponentFixture<InConnectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ InConnectionsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InConnectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
