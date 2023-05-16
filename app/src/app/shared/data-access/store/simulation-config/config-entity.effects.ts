import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { EMPTY } from 'rxjs';
import { catchError, filter, map, switchMap, withLatestFrom } from 'rxjs/operators';
import * as routerActions from '@ngrx/router-store';

import { SimulationsService } from 'src/app/core/simulations/simulations.service';
import { SimulationSetupPageActions } from './simulation-config.actions';
import { ConfigEntity } from 'src/app/shared/types/config-entity';
import { ConfigEntitySelectorService } from './config-entity.selectors';
import { ConfigEntityActions } from './config-entity.actions';
import { Router } from '@angular/router';

@Injectable()
export class ConfigEntityEffects {

  loadAPIConfigs$ = createEffect(() => this.actions$.pipe(
    ofType(routerActions.routerNavigatedAction),
    filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/simulation-setup'),
    switchMap(() => this.simulationService.getSimulations(10)),
    map((configs: ConfigEntity[]) => {
      console.log('loadAPIConfigs$', configs);
      if (configs.length == 0) {
        return ConfigEntityActions.loadingConfigsSuccessButEmpty();
      }
      return ConfigEntityActions.loadingConfigsSuccess({ configs, id: configs[configs.length - 1].id });
    }),
    catchError(() => EMPTY)
  ));

  loadAPIConfigsSuccessButEmpty$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigEntityActions.loadingConfigsSuccessButEmpty),
    map(() => SimulationSetupPageActions.setActiveConfig({ id: 0 })),
    catchError(() => EMPTY)
  ));

  loadAPIConfigsSuccess$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigEntityActions.loadingConfigsSuccess),
    map(({ id }) => SimulationSetupPageActions.setActiveConfig({ id })),
    catchError(() => EMPTY)
  ));

  createConfig$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigEntityActions.createConfig),
    withLatestFrom(this.configEntitySelectorService.simulationActiveConfig$),
    switchMap(([{ name }, config]) => this.simulationService.createSimulation(name, config as ConfigEntity)),
    map(() => ConfigEntityActions.creatingConfigSuccess()),
    catchError(() => EMPTY)
  ));

  updateConfig$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigEntityActions.updateConfig),
    withLatestFrom(this.configEntitySelectorService.simulationActiveConfig$),
    switchMap(([{ name }, config]) => this.simulationService.updateSimulation(name, config as ConfigEntity)),
    map(() => ConfigEntityActions.creatingConfigSuccess()),
    catchError(() => EMPTY)
  ));

  processConfigBeforeRedirectToResults$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupPageActions.goToSimulationResults),
    withLatestFrom(this.configEntitySelectorService.simulationActiveConfig$),
    switchMap(([{ currentNameFieldValue }, config]) => {
      if (config.id === 0) {
        return this.simulationService.createSimulation(currentNameFieldValue, config as ConfigEntity);
      }
      return this.simulationService.updateSimulation(currentNameFieldValue, config as ConfigEntity);
    }),
    map(() => ConfigEntityActions.processingConfigSuccess()),
    catchError(() => EMPTY)
  ));
    
  validateConfig$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigEntityActions.processingConfigSuccess),
    switchMap(() => this.simulationService.validateSimulation()),
    map(() => ConfigEntityActions.validatingConfigSuccess()),
    catchError(() => EMPTY)
  ));

  validateConfigSuccess$ = createEffect(() => this.actions$.pipe(
    ofType(ConfigEntityActions.validatingConfigSuccess),
    switchMap(() => this.router.navigate(['/simulation-results']))
  ), {dispatch: false});

  constructor(
    private actions$: Actions,
    private simulationService: SimulationsService,
    private configEntitySelectorService: ConfigEntitySelectorService,
    private router: Router
  ) { }

}
