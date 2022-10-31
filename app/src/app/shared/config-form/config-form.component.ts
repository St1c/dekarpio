import { Component, forwardRef, Input, OnInit } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormControl, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-config-form',
  templateUrl: './config-form.component.html',
  styleUrls: ['./config-form.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => ConfigFormComponent),
      multi: true
  }]
})
export class ConfigFormComponent implements ControlValueAccessor {

  form: FormGroup;
  keys!: string[];

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(private fb: FormBuilder) {
    this.form = this.fb.group({
      "integrate": false,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
      this.onTouch();
    });
  }

  writeValue(obj: any): void {
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
