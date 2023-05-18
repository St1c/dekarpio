import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { EMPTY } from 'rxjs';
import { catchError, filter, map, switchMap } from 'rxjs/operators';
import * as routerActions from '@ngrx/router-store';

import { SimulationsService } from 'src/app/core/simulations/simulations.service';
import { ConfigEntity } from 'src/app/shared/types/config-entity';
import { ConfigsManagementActions } from './config-management.actions';
// import { Router } from '@angular/router';

@Injectable()
export class ConfigsManagementEffects {

  loadConfigs$ = createEffect(() => this.actions$.pipe(
    ofType(routerActions.routerNavigatedAction),
    filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/configs-management'),
    switchMap(() => this.simulationService.getAllSimulations()),
    map((configs: ConfigEntity[]) => {
      if (configs.length == 0) {
        return ConfigsManagementActions.loadingConfigsSuccessButEmpty();
      }
      return ConfigsManagementActions.loadingConfigsSuccess({ configs });
    }),
    catchError(() => EMPTY)
  ));

  deleteConfig$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigsManagementActions.deleteConfig),
    switchMap(({ id }) => this.simulationService.deleteSimulation(id)),
    map((id) => ConfigsManagementActions.deleteConfigSuccess({ id })),
    catchError(() => EMPTY)
  ));

  constructor(
    private actions$: Actions,
    private simulationService: SimulationsService
  ) { }

}
