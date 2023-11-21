import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { CampfireComponent } from './campfire.component';

describe('CampfireComponent', () => {
  let component: CampfireComponent;
  let fixture: ComponentFixture<CampfireComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CampfireComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CampfireComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
