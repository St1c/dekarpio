import { CommonModule } from '@angular/common';
import { Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, UntypedFormBuilder, UntypedFormControl, UntypedFormGroup, NG_VALUE_ACCESSOR, ReactiveFormsModule } from '@angular/forms';

import { ConfigFormControlComponent } from '../config-form-control/config-form-control.component';

@Component({
  selector: 'app-config-form',
  templateUrl: './config-form.component.html',
  styleUrls: ['./config-form.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ConfigFormControlComponent
],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => ConfigFormComponent),
      multi: true
  }]
})
export class ConfigFormComponent implements ControlValueAccessor {

  form: UntypedFormGroup;
  keys!: string[];

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(private fb: UntypedFormBuilder) {
    this.form = this.fb.group({
      "integrate": false,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.getRawValue());
      this.onTouch();
    });

    this.form.get('integrate')?.valueChanges.subscribe(value => {
      if (!value) {
        // disable all other controls
        this.keys.map(key => {
          if (key == 'integrate') return;
          this.form.get(key)?.disable({emitEvent: false});
        });
      } else {
        // enable all other controls
        this.keys.map(key => {
          if (key == 'integrate') return;
          this.form.get(key)?.enable({emitEvent: false});
        });
      }
    });
  }

  writeValue(obj: any): void {
    const params = obj;
    this.keys = Object.keys(params).filter(key => key != 'description');
    this.keys.map(key => {
      this.form.addControl(key, new UntypedFormControl(params[key]));
    });

    this.form.patchValue({
      "integrate": Boolean(params.integrate)
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
