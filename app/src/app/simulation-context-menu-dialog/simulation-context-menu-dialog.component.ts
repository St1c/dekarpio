import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { ReactiveFormsModule, UntypedFormControl } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

// import { ConfigFormControlComponent } from '../shared/config-form-control/config-form-control.component';
import { ConfigFormComponent } from '../shared/ui/config-form/config-form.component';
import { DialogData } from '../simulation-setup/simulation-setup.component';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { toBoolean } from '../shared/utils/type-coercion';

@Component({
  selector: 'simulation-context-menu-dialog',
  templateUrl: './simulation-context-menu-dialog.html',
  standalone: true,
  imports: [
    CommonModule,
    ConfigFormComponent,
    MatDialogModule,
    MatButtonModule,
    MatSlideToggleModule,
    ReactiveFormsModule
]
})
export class SimulationContextMenuDialogComponent {
  title = '';
  desc = '';
  element: any;
  config: any;

  params = new UntypedFormControl();

  constructor(
    public dialogRef: MatDialogRef<SimulationContextMenuDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {
    this.title = data.title?.innerHTML || '';
    this.desc = data.desc?.innerHTML || '';
    this.element = data.element;
    this.config = data.config;
    
    let integrate = toBoolean(this.config.param[0].integrate);

    if ('param' in this.config) {
      console.log(integrate);
      this.params.setValue(integrate);
    }
  }

  closeDialog() {
    const res = {
      element: this.element,
      params: {
        ...this.config, 
        param: [{
          ...this.config.param[0],
          integrate: toBoolean(this.params.value)
        }]
      },
      state: this.params.value
    };

    this.dialogRef.close(res);
  }
}
