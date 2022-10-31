import { Component, forwardRef, Input, OnInit } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormControl, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';
import { ConfigProvider } from 'src/app/core/config.provider';

@Component({
  selector: 'app-energy-sources',
  templateUrl: './energy-sources.component.html',
  styleUrls: ['./energy-sources.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => EnergySourcesComponent),
      multi: true
  }]
})
export class EnergySourcesComponent implements ControlValueAccessor {

  form: FormGroup;

  keys!: string[];

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder,
    private configProvider: ConfigProvider
  ) {
    this.form = this.fb.group({
      "integrate": false,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
      this.onTouch();
    });
  }

  writeValue(obj: any): void {
    console.log(obj);
    const params = obj;

    this.keys = Object.keys(params).filter(key => key != 'description');

    this.keys.map(key => {
      this.form.addControl(key, new FormControl(params[key]));
    });

    this.form.patchValue({
      "integrate": params.integrate
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
