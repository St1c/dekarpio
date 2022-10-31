import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { CollectorsComponent } from './collectors/collectors.component';
import { ConnectorsComponent } from './connectors/connectors.component';
import { EnergyConversionUnitsComponent } from './energy-conversion-units/energy-conversion-units.component';
import { EnergyDemandsComponent } from './energy-demands/energy-demands.component';
import { EnergySourcesComponent } from './energy-sources/energy-sources.component';
import { EnergyStoragesComponent } from './energy-storages/energy-storages.component';
import { ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { InConnectionsComponent } from './in-connections/in-connections.component';
import { OutConnectionsComponent } from './out-connections/out-connections.component';
import { ConfigFormControlComponent } from './config-form-control/config-form-control.component';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSelectModule } from '@angular/material/select';

@NgModule({
  declarations: [
    CollectorsComponent,
    ConnectorsComponent,
    EnergyConversionUnitsComponent,
    EnergyDemandsComponent,
    EnergySourcesComponent,
    EnergyStoragesComponent,
    InConnectionsComponent,
    OutConnectionsComponent,
    ConfigFormControlComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatInputModule,
    MatSlideToggleModule,
    MatSelectModule
  ],
  exports: [
    CollectorsComponent,
    ConnectorsComponent,
    EnergyConversionUnitsComponent,
    EnergyDemandsComponent,
    EnergySourcesComponent,
    EnergyStoragesComponent,
  ]
})
export class SharedModule { }
