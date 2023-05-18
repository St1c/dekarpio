import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AuthService } from './core/auth/auth.service';
import { LoginComponent } from './login/login.component';
import { SimulationResultsComponent } from './simulation-results/simulation-results.component';
import { SimulationSetupComponent } from './simulation-setup/simulation-setup.component';
import { ConfigsManagementComponent } from './configs-management/configs-management.component';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'simulation-setup',
    pathMatch: 'full'
  },
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: 'simulation-setup',
    component: SimulationSetupComponent,
    canActivate: [AuthService]
  },
  {
    path: 'simulation-results',
    component: SimulationResultsComponent,
    canActivate: [AuthService]
  },
  {
    path: 'configs-management',
    component: ConfigsManagementComponent,
    canActivate: [AuthService]
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
