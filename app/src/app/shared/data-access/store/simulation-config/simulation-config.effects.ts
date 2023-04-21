import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { EMPTY } from 'rxjs';
import { map, catchError, switchMap, filter, withLatestFrom } from 'rxjs/operators';
import * as routerActions from '@ngrx/router-store';

import { ConfigProvider } from 'src/app/core/config.provider';
import { Simulation, SimulationsService } from 'src/app/core/simulations/simulations.service';
import { SimulationDefaultConfigActions, SimulationSetupAPIActions, SimulationSetupPageActions } from './simulation-config.actions';
import { SvgElementToolsService } from 'src/app/shared/utils/svg-element-tools.service';
import { SimulationDefault } from './simulation-config.reducer';
import { SimulationConfigSelectorService } from './simulation-config.selectors';
import { Router } from '@angular/router';

@Injectable()
export class SimulationSetupEffects {

  // loadDefaultConfig$ = createEffect(() => this.actions$.pipe(
  //   ofType(routerActions.routerNavigatedAction),
  //   filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/simulation-setup'),
  //   switchMap(() => this.configProvider.getConfigFromAssets()),
  //   map( (defaultConfig: Object) => SimulationDefaultConfigActions.loadingConfigSuccess({ config: defaultConfig })),
  //   catchError(() => EMPTY)
  // ));


  // loadAPIConfig$ = createEffect(() => this.actions$.pipe(
  //   ofType(routerActions.routerNavigatedAction),
  //   filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/simulation-setup'),
  //   switchMap( () => this.simulationService.getSimulation()),
  //   map( (config: Simulation) => {
  //     let configToUse = config?.settings ? JSON.parse(config.settings) : {};
  //     return SimulationSetupAPIActions.loadingConfigSuccess({ config: configToUse }) 
  //   }),
  //   catchError(() => EMPTY)
  // ));

  loadDefaultConfig$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupPageActions.svgLoaded),
    switchMap(() => this.configProvider.getConfigFromAssets()),
    map((defaultConfig: SimulationDefault) => {
      const configurableShapes = this.svgTools.getConfigurableShapeNames(defaultConfig);
      return SimulationDefaultConfigActions.loadingConfigSuccess({ config: defaultConfig, configurableShapes });
    }),
    catchError(() => EMPTY)
  ));

  loadAPIConfig$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupPageActions.svgLoaded),
    switchMap(() => this.simulationService.getSimulation()),
    map((config: Simulation) => {
      let configToUse = config?.settings ? JSON.parse(config.settings) : {};
      return SimulationSetupAPIActions.loadingConfigSuccess({ config: configToUse });
    }),
    catchError(() => EMPTY)
  ));

  createConfig$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupAPIActions.createConfig),
    withLatestFrom(this.simulationConfigSelectorService.simulationConfigValue$),
    switchMap(([action, config]) => this.simulationService.createSimulation(JSON.stringify(config))),
    map((simulation: Simulation) => SimulationSetupAPIActions.creatingConfigSuccess()),
    catchError(() => EMPTY)
  ));

  validateConfig$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupAPIActions.creatingConfigSuccess),
    switchMap(() => this.simulationService.validateSimulation()),
    map(() => SimulationSetupAPIActions.validatingConfigSuccess()),
    catchError(() => EMPTY)
  ));

  validateConfigSuccess$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupAPIActions.validatingConfigSuccess),
    switchMap(() => this.router.navigate(['/simulation-results'] ))
  ), { dispatch: false });

  // this.subs.add(
  //   this.simulationService.createSimulation(JSON.stringify(this.config))
  //     .pipe(
  //       switchMap((res: any) => this.simulationService.validateSimulation()
  //       ))
  //     .subscribe((res: any) => {
  //       this.router.navigate(['/simulation-results']);
  //     })
  // );

  constructor(
    private actions$: Actions,
    private configProvider: ConfigProvider,
    private simulationService: SimulationsService,
    private simulationConfigSelectorService: SimulationConfigSelectorService,
    private router: Router,
    private svgTools: SvgElementToolsService
  ) { }
}