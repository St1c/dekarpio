import { Component, Inject } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DialogData } from './simulation-setup.component';

@Component({
  selector: 'svg-element-dialog',
  templateUrl: 'svg-element-dialog.html',
})
export class SvgElementDialogComponent {
  title = '';
  desc = '';
  element: any;
  config: any;

  params = new FormControl();

  constructor(
    public dialogRef: MatDialogRef<SvgElementDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {
    this.title = data.title?.innerHTML || '';
    this.desc = data.desc?.innerHTML || '';
    this.element = data.element;
    this.config = data.config;

    if ('Param' in this.config) {
      this.params.setValue(this.config.Param[0]);
    }

    if ('param' in this.config) {
      this.params.setValue(this.config.param[0]);
    }
  }

  closeDialog() {
    console.log(this.config)
    this.dialogRef.close({
      element: this.element,
      params: {...this.config, Param: [{...this.params.value}]},
      state: this.params.value.integrate
    });
  }
}
