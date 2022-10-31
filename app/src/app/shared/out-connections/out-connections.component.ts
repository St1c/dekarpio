import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

const OUT_CONNECTIONS = {
  "con": 10,
  "active": "EUR/MW",
};

@Component({
  selector: 'app-out-connections',
  templateUrl: './out-connections.component.html',
  styleUrls: ['./out-connections.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => OutConnectionsComponent),
      multi: true
  }]
})
export class OutConnectionsComponent implements ControlValueAccessor {

  form: FormGroup;

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      "con": OUT_CONNECTIONS.con,
      "active": OUT_CONNECTIONS.active,
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
