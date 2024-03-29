import { CommonModule } from '@angular/common';
import { Component, Inject, OnDestroy } from '@angular/core';
import { ReactiveFormsModule, UntypedFormControl } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { Subscription } from 'rxjs';

import { ConfigFormComponent } from '../shared/ui/config-form/config-form.component';
import { toBoolean } from '../shared/utils/type-coercion';
import { DialogData } from '../simulation-setup/simulation-setup.component';
import { ConfigEntitySelectorService } from '../shared/data-access/store/config-entity/config-entity.selectors';

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
export class SimulationContextMenuDialogComponent implements OnDestroy {
  title = '';
  desc = '';
  element: any;
  config: any;

  params = new UntypedFormControl();

  private subs = new Subscription();

  constructor(
    public dialogRef: MatDialogRef<SimulationContextMenuDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData,
    private configEntitySelectorService: ConfigEntitySelectorService
  ) {
    this.title = data.title?.innerHTML || '';
    this.desc = data.desc?.innerHTML || '';
    this.element = data.element;
    const unit_type = data.unit_meta?.unit_type;
    const unit_id = data.unit_meta?.unit_id;

    this.subs.add(this.configEntitySelectorService.simulationActiveConfigSettings$
      .subscribe((defaultConfig: any) => {
        this.config = { unit_type, unit_id, ...defaultConfig[unit_type][unit_id] };

        let integrate = toBoolean(this.config.param[0].integrate);

        if ('param' in this.config) {
          console.log(integrate);
          this.params.setValue(integrate);
        }
      })
    );
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  closeDialog() {
    this.dialogRef.close({
      ...this.config,
      param: [{
        ...this.config.param[0],
        integrate: toBoolean(this.params.value)
      }]
    });
  }
}
