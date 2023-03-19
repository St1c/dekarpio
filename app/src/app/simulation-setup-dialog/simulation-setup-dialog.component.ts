import { Component, Inject } from '@angular/core';
import { UntypedFormControl } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DialogData } from '../simulation-setup/simulation-setup.component';

@Component({
  selector: 'simulation-setup-dialog',
  templateUrl: './simulation-setup-dialog.html',
})
export class SimulationSetupDialogComponent {
  title = '';
  desc = '';
  element: any;
  config: any;

  params = new UntypedFormControl();

  constructor(
    public dialogRef: MatDialogRef<SimulationSetupDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {
    this.title = data.title?.innerHTML || '';
    this.desc = data.desc?.innerHTML || '';
    this.element = data.element;
    this.config = data.config;

    // @TODO: This is a hack to get the params to work - probably not needed anymore
    if ('Param' in this.config) {
      this.params.setValue(this.config.Param[0]);
    }

    if ('param' in this.config) {
      this.params.setValue(this.config.param[0]);
    }
  }

  closeDialog() {
    this.dialogRef.close({
      element: this.element,
      params: {...this.config, param: [{...this.params.value}]},
      state: this.params.value.integrate
    });
  }
}
