import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

const ENERGY_STORAGES = {
  "integrate": "true",
  "exist": "true",
  "cap": 3,
  "power": 1,
  "min": 0.15,
  "eta_stor": 0.995,
  "eta_char": 0.995,
  "eta_dis": 0.995,
  "invest_fix": 1000,
  "invest_cap": 1000,
  "invest_power": 500
};

@Component({
  selector: 'app-energy-storages',
  templateUrl: './energy-storages.component.html',
  styleUrls: ['./energy-storages.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => EnergyStoragesComponent),
      multi: true
  }]
})
export class EnergyStoragesComponent implements ControlValueAccessor {

  form: FormGroup;

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      "integrate": ENERGY_STORAGES.integrate,
      "exist": ENERGY_STORAGES.exist,
      "cap": ENERGY_STORAGES.cap,
      "power": ENERGY_STORAGES.power,
      "min": ENERGY_STORAGES.min,
      "eta_stor": ENERGY_STORAGES.eta_stor,
      "eta_char": ENERGY_STORAGES.eta_char,
      "eta_dis": ENERGY_STORAGES.eta_dis,
      "invest_fix": ENERGY_STORAGES.invest_fix,
      "invest_cap": ENERGY_STORAGES.invest_cap,
      "invest_power": ENERGY_STORAGES.invest_power,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
    });
  }

  writeValue(obj: any): void {
    console.log(obj);
    const params = obj.Param[0];

    this.form.patchValue({
      "integrate": ENERGY_STORAGES.integrate,
      "exist": ENERGY_STORAGES.exist,
      "cap": ENERGY_STORAGES.cap,
      "power": ENERGY_STORAGES.power,
      "min": ENERGY_STORAGES.min,
      "eta_stor": ENERGY_STORAGES.eta_stor,
      "eta_char": ENERGY_STORAGES.eta_char,
      "eta_dis": ENERGY_STORAGES.eta_dis,
      "invest_fix": ENERGY_STORAGES.invest_fix,
      "invest_cap": ENERGY_STORAGES.invest_cap,
      "invest_power": ENERGY_STORAGES.invest_power,
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
