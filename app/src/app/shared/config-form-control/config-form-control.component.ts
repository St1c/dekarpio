import { Component, Input, OnInit } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormControl, NG_VALUE_ACCESSOR } from '@angular/forms';
import { ConfigProvider } from 'src/app/core/config.provider';

export class ConfigFormControl<T> {
  name: T;
  unit: string | undefined;
  type: 'text' | 'select' | 'slider' | 'textarea' | 'toggle' | 'checkbox';
  options: any;
  description: string;
  displayName: string;

  constructor(options: {
    name: T,
    displayname: string,
    type: string,
    options?: any[]
    unit?: string,
    description?: string,
  }) {
    // console.log(options);
    this.name = options.name;
    this.options = undefined;
    this.displayName = options.displayname;
    this.description = options.description || '';

    this.unit = options.unit || undefined;
    if (options.unit === 'none') this.unit = undefined;

    switch (options.type) {
      case 'select':
        this.type = 'select';
        this.options = options.options;
        break;
      case 'boolean':
        this.type = 'checkbox';
        break;
      case 'slide toggle':
        this.type = 'toggle';
        break;
      default:
        this.type = 'text';
        break;
    }
  }
}

@Component({
  selector: 'app-config-form-control',
  templateUrl: './config-form-control.component.html',
  styleUrls: ['./config-form-control.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: ConfigFormControlComponent,
      multi: true
    }
  ]
})
export class ConfigFormControlComponent implements OnInit, ControlValueAccessor {

  @Input('formControlName') name!: string;

  controlValue: FormControl;
  config!: ConfigFormControl<any>;

  private metaData: any;
  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder,
    private configService: ConfigProvider
  ) {
    this.metaData = this.configService.metaDataConfig?.meta;
    this.controlValue = new FormControl('');
  }

  ngOnInit(): void {
    this.controlValue.valueChanges.subscribe((val: any) => this.onChange(val));
    this.config = new ConfigFormControl<any>(this.metaData[this.name]);
  }

  writeValue(value: any): void {
    this.controlValue.setValue(value);
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouch = fn;
  }

  setDisabledState?(isDisabled: boolean): void {
    throw new Error('Method not implemented.');
  }

}
