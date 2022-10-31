import { Component, forwardRef, OnInit } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormControl, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

const ENERGY_STORAGE = {
  "integrate": "true",
  "exist": "true",
  "cap_max": 10,
  "cap_min": 0.25,
  "min_operation": 0.1,
  "eff_fullload": 0.9,
  "eff_minload": 0.8,
  "ramp": 4,
  "min_on": 1,
  "min_off": 2,
  "start_dur": 0,
  "down_dur": 0,
  "inv_fix": 100000,
  "inv_cap": 1000,
  "opex_main": 0.01,
  "opex_fix": 10,
  "opex_start": 500
};

@Component({
  selector: 'app-energy-conversion-units',
  templateUrl: './energy-conversion-units.component.html',
  styleUrls: ['./energy-conversion-units.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => EnergyConversionUnitsComponent),
      multi: true
  }]
})
export class EnergyConversionUnitsComponent implements ControlValueAccessor {

  form: FormGroup;

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      "integrate": ENERGY_STORAGE.integrate,
      "exist": ENERGY_STORAGE.exist,
      "cap_max": ENERGY_STORAGE.cap_max,
      "cap_min": ENERGY_STORAGE.cap_min,
      "min_operation": ENERGY_STORAGE.min_operation,
      "eff_fullload": ENERGY_STORAGE.eff_fullload,
      "eff_minload": ENERGY_STORAGE.eff_minload,
      "ramp": ENERGY_STORAGE.ramp,
      "min_on": ENERGY_STORAGE.min_on,
      "min_off": ENERGY_STORAGE.min_off,
      "start_dur": ENERGY_STORAGE.start_dur,
      "down_dur": ENERGY_STORAGE.down_dur,
      "inv_fix": ENERGY_STORAGE.inv_fix,
      "inv_cap": ENERGY_STORAGE.inv_cap,
      "opex_main": ENERGY_STORAGE.opex_main,
      "opex_fix": ENERGY_STORAGE.opex_fix,
      "opex_start": ENERGY_STORAGE.opex_start,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
    });
  }

  writeValue(obj: any): void {
    console.log(obj);
    const params = obj.Param[0];

    this.form.patchValue({
      "integrate": params.integrate,
      "exist": params.exist,
      "cap_max": params.cap_max,
      "cap_min": params.cap_min,
      "min_operation": params.min_operation,
      "eff_fullload": params.eff_fullload,
      "eff_minload": params.eff_minload,
      "ramp": params.ramp,
      "min_on": params.min_on,
      "min_off": params.min_off,
      "start_dur": params.start_dur,
      "down_dur": params.down_dur,
      "inv_fix": params.inv_fix,
      "inv_cap": params.inv_cap,
      "opex_main": params.opex_main,
      "opex_fix": params.opex_fix,
      "opex_start": params.opex_start,
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
