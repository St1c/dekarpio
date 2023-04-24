import { ElementRef, Injectable } from '@angular/core';
import { Actions, concatLatestFrom, createEffect, ofType } from '@ngrx/effects';
import { EMPTY } from 'rxjs';
import { map, catchError, switchMap, filter, withLatestFrom, delay } from 'rxjs/operators';
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

  loadDefaultConfig$ = createEffect(() => this.actions$.pipe(
    // ofType(SimulationSetupPageActions.svgLoaded),
    ofType(routerActions.routerNavigatedAction),
    filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/simulation-setup'),
    switchMap(() => this.configProvider.getConfigFromAssets()),
    map((defaultConfig: SimulationDefault) => {
      return SimulationDefaultConfigActions.loadingConfigSuccess({ config: defaultConfig });
    }),
    catchError(() => EMPTY)
  ));

  loadAPIConfig$ = createEffect(() => this.actions$.pipe(
    // ofType(SimulationSetupPageActions.svgLoaded),
    ofType(routerActions.routerNavigatedAction),
    filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/simulation-setup'),
    switchMap(() => this.simulationService.getSimulation()),
    map((config: Simulation) => {
      let configToUse = config?.settings ? JSON.parse(config.settings) : {};
      return SimulationSetupAPIActions.loadingConfigSuccess({ config: configToUse });
    }),
    catchError(() => EMPTY)
  ));

  setConfigurableShapesAfterSvgLoad$ = createEffect(() => this.actions$.pipe(
    ofType(
      SimulationSetupPageActions.svgLoaded
    ),
    withLatestFrom(this.simulationConfigSelectorService.simulationDefaultConfigValue$),
    map(([notUsedAction, defaultConfig]) => {
      const configurableShapes = this.svgTools.getConfigurableShapeNames(defaultConfig);
      return SimulationDefaultConfigActions.setConfigurableShapes({ configurableShapes });
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
    switchMap(() => this.router.navigate(['/simulation-results']))
  ), { dispatch: false });

  updateSVGonConfigChange$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupPageActions.svgUpdateOnConfigChange),
    // delay(100),
    concatLatestFrom(() => [
      this.simulationConfigSelectorService.configurableShapeNames$,
      this.simulationConfigSelectorService.simulationDefaultConfigValue$,
      this.simulationConfigSelectorService.simulationConfigConnections$
    ]),
    map(([action, configurableShapes, config, configConnections]) => {
      const svgElement = action.svgElement;
      const configurableElements = this.svgTools.getConfigurableElements(svgElement, configurableShapes);

      // @TODO: loop through configurableElements and update the svg based on config
      configurableElements?.map((el: Node | null) => {
        let title = '';
        el?.childNodes.forEach((node: any) => node.nodeName === 'title' ? title = node.innerHTML : null );
        if (title.length > 0) {
          let [unit_type, unit_id, ...rest] = title.split('_');
          this.applyElementSettingsToSVG(title, config[unit_type][unit_id], configConnections, svgElement);
        }
      });
    }),
    catchError(() => EMPTY)
  ), { dispatch: false });

  constructor(
    private actions$: Actions,
    private configProvider: ConfigProvider,
    private simulationService: SimulationsService,
    private simulationConfigSelectorService: SimulationConfigSelectorService,
    private router: Router,
    private svgTools: SvgElementToolsService
  ) { }


  private applyElementSettingsToSVG(title: string, params: any, configConnections: any, svgLayout: ElementRef) {
    const state = params.param[0]?.integrate || false;
    const affectedConnections = this.svgTools.findAffectedConnectionsByInOutIds(title, configConnections);
    this.svgTools.findConnecstionLinesById([title, ...affectedConnections], state, svgLayout);

    const siblings = this.svgTools.findAllElementsContainingTitle(title, svgLayout.nativeElement);

    for (let i = 0; i < siblings.snapshotLength; i++) {
      const item = siblings.snapshotItem(i) as HTMLElement;
      state ? item.classList.remove('inactive') : item.classList.add('inactive');
    }
  }

}