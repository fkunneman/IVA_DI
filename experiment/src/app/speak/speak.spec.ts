import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Speak } from './speak';

describe('Speak', () => {
  let component: Speak;
  let fixture: ComponentFixture<Speak>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Speak]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Speak);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
