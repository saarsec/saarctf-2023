import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { PagePartyComponent } from './page-party.component';

describe('PagePartyComponent', () => {
  let component: PagePartyComponent;
  let fixture: ComponentFixture<PagePartyComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ PagePartyComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PagePartyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
