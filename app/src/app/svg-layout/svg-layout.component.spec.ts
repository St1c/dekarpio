import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SvgLayoutComponent } from './svg-layout.component';

describe('SvgLayoutComponent', () => {
  let component: SvgLayoutComponent;
  let fixture: ComponentFixture<SvgLayoutComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SvgLayoutComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SvgLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
