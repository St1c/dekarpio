import { BrowserModule, bootstrapApplication } from '@angular/platform-browser';
import { enableProdMode, importProvidersFrom } from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
import { withInterceptorsFromDi, provideHttpClient } from '@angular/common/http';

import { provideStore } from '@ngrx/store';
import { provideRouterStore, routerReducer } from '@ngrx/router-store';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { provideEffects } from '@ngrx/effects';

import { InlineSVGModule } from 'ng-inline-svg';
import { environment } from './environments/environment';

import { AppComponent } from './app/app.component';
import { AppRoutingModule } from './app/app-routing.module';
import { CoreModule } from './app/core/core.module';

import { configEntityReducer, ConfigEntityEffects } from './app/shared/data-access/store/config-entity';
import { configsManagementReducer, ConfigsManagementEffects } from './app/shared/data-access/store/config-management';
import { simulationConfigReducer, SimulationSetupEffects } from './app/shared/data-access/store/simulation-config';

if (environment.production) {
  enableProdMode();
}

bootstrapApplication(AppComponent, {
  providers: [
    importProvidersFrom(
      BrowserModule,
      ReactiveFormsModule,
      AppRoutingModule,
      CoreModule,
      InlineSVGModule
    ),
    provideAnimations(),
    provideHttpClient(withInterceptorsFromDi()),

    // configure NgRx modules
    provideStore({
      router: routerReducer,
      simulationSetup: simulationConfigReducer,
      configEntities: configEntityReducer,
      configsManagement: configsManagementReducer,
    }, {
      runtimeChecks: {
        strictStateImmutability: false,
        strictActionImmutability: false,
        strictStateSerializability: true,
        strictActionSerializability: false,
      }
    }),
    provideRouterStore(),
    provideEffects(
      ConfigEntityEffects,
      ConfigsManagementEffects,
      SimulationSetupEffects,
    ),
    provideStoreDevtools({
      trace: true,
    }),
  ]
})
  .catch(err => console.error(err));
