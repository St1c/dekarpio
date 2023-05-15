import { ElementRef, Injectable } from '@angular/core';
import { Actions, concatLatestFrom, createEffect, ofType } from '@ngrx/effects';
import { EMPTY } from 'rxjs';
import { catchError, delay, filter, map, switchMap, withLatestFrom } from 'rxjs/operators';
import * as routerActions from '@ngrx/router-store';

import { ConfigProvider } from 'src/app/core/config.provider';
import {
  SimulationDefaultConfigActions,
  SimulationSetupPageActions
} from './simulation-config.actions';
import { SvgElementToolsService } from 'src/app/shared/utils/svg-element-tools.service';
import { SimulationConfigSelectorService } from './simulation-config.selectors';
import { SimulationJson } from 'src/app/shared/types/simulation-json';
import { ConfigEntitySelectorService } from './config-entity.selectors';

@Injectable()
export class SimulationSetupEffects {

  loadDefaultConfig$ = createEffect(() => this.actions$.pipe(
    ofType(routerActions.routerNavigatedAction),
    filter(routeChangeAction => routeChangeAction.payload.routerState.url === '/simulation-setup'),
    switchMap(() => this.configProvider.getConfigFromAssets()),
    map((defaultConfig: SimulationJson) => {
      return SimulationDefaultConfigActions.loadingConfigSuccess({ config: defaultConfig });
    }),
    catchError(() => EMPTY)
  ));

  loadDefaultConfigSuccess$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationDefaultConfigActions.loadingConfigSuccess),
    map(() => SimulationSetupPageActions.setActiveConfig({ id: 0 })),
    catchError(() => EMPTY)
  ));

  setConfigurableShapesAfterSvgLoad$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupPageActions.svgLoaded),
    withLatestFrom(this.simulationConfigSelectorService.simulationDefaultConfigValue$),
    map(([, defaultConfig]) => {
      const configurableShapes = this.svgTools.getConfigurableShapeNames(defaultConfig);
      return SimulationDefaultConfigActions.setConfigurableShapes({ configurableShapes });
    }),
    catchError(() => EMPTY)
  ));

  updateSVGonConfigChange$ = createEffect(() => this.actions$.pipe(
    ofType(SimulationSetupPageActions.svgUpdateOnConfigChange),
    delay(100),
    concatLatestFrom(() => [
      this.simulationConfigSelectorService.configurableShapeNames$,
      this.configEntitySelectorService.simulationActiveConfigSettings$,
      this.simulationConfigSelectorService.simulationConfigConnections$
    ]),
    map(([action, configurableShapes, config, configConnections]) => {
      const svgElement = action.svgElement;
      const configurableElements = this.svgTools.getConfigurableElements(svgElement, configurableShapes);

      // @TODO: loop through configurableElements and update the svg based on config
      configurableElements?.map((el: Node | null) => {
        let title = '';
        el?.childNodes.forEach((node: any) => node.nodeName === 'title' ? title = node.innerHTML : null);
        if (title.length > 0) {
          let [unit_type, unit_id] = title.split('_');
          this.applyElementSettingsToSVG(title, config[unit_type][unit_id], configConnections, svgElement);
        }
      });
    }),
    catchError(() => EMPTY)
  ), { dispatch: false });

  constructor(
    private actions$: Actions,
    private configProvider: ConfigProvider,
    private simulationConfigSelectorService: SimulationConfigSelectorService,
    private configEntitySelectorService: ConfigEntitySelectorService,
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
