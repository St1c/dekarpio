import { Component, forwardRef, OnInit } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormControl, FormGroup, NG_VALUE_ACCESSOR } from '@angular/forms';

const CONNECTIONS = {
  "in": 10,
  "out": "EUR/MW",
};

@Component({
  selector: 'app-collectors',
  templateUrl: './collectors.component.html',
  styleUrls: ['./collectors.component.scss'],
  providers: [{
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CollectorsComponent),
      multi: true
  }]
})
export class CollectorsComponent implements ControlValueAccessor {

  form: FormGroup;

  private onChange: any = () => {}
  private onTouch: any = () => {}

  constructor(
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      "in": CONNECTIONS.in,
      "out": CONNECTIONS.out,
    });

    this.form.valueChanges.subscribe(changes => {
      this.onChange(this.form.value);
    });
  }

  writeValue(obj: any): void {
    console.log(obj);
    const params = obj.Param[0];

    this.form.patchValue({
      "in": params.in,
      "out": params.out,
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
