import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

const ENERGY_DEMANDS = {
  "exists": "true",
  "temp": 400,
  "pres": 4500000,
  "days_off": 15
};

@Component({
  selector: 'app-energy-demands',
  templateUrl: './energy-demands.component.html',
  styleUrls: ['./energy-demands.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => EnergyDemandsComponent),
      multi: true
  }]
})
export class EnergyDemandsComponent implements ControlValueAccessor {

  form: FormGroup;

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      "exists": ENERGY_DEMANDS.exists,
      "temp": ENERGY_DEMANDS.temp,
      "pres": ENERGY_DEMANDS.pres,
      "days_off": ENERGY_DEMANDS.days_off
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
    });
  }

  writeValue(obj: any): void {
    console.log(obj);
    const params = obj.Param[0];

    this.form.patchValue({
      "exists": params.exists,
      "temp": params.temp,
      "pres": params.pres,
      "days_off": params.days_off
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
