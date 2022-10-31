import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';

import { MaterialModule } from '../material/material.module';

import { ConfigFormComponent } from './config-form/config-form.component';
import { ConfigFormControlComponent } from './config-form-control/config-form-control.component';

@NgModule({
  declarations: [
    ConfigFormComponent,
    ConfigFormControlComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MaterialModule
  ],
  exports: [
    ConfigFormComponent,
    ConfigFormControlComponent,
    MaterialModule
  ]
})
export class SharedModule { }
