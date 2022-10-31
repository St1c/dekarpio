import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

const IN_CONNECTIONS = {
  "con": 10,
  "active": "EUR/MW",
};

@Component({
  selector: 'app-in-connections',
  templateUrl: './in-connections.component.html',
  styleUrls: ['./in-connections.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => InConnectionsComponent),
      multi: true
  }]
})
export class InConnectionsComponent implements ControlValueAccessor {

  form: FormGroup;

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      "con": IN_CONNECTIONS.con,
      "active": IN_CONNECTIONS.active,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
    });
  }

  writeValue(obj: any): void {
    console.log(obj);
    const params = obj.Param[0];

    this.form.patchValue({
      "con": params.con,
      "active": params.active,
    });
  }

  registerOnTouched(fn: any): void {
    this.onTouch = fn;
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  setDisabledState(isDisabled: boolean): void {

  }

}
