import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectmodelComponent } from './selectmodel.component';

describe('SelectmodelComponent', () => {
  let component: SelectmodelComponent;
  let fixture: ComponentFixture<SelectmodelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SelectmodelComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SelectmodelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
