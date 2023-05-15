import { Injectable } from '@angular/core';
import { createFeatureSelector, createSelector,  Store } from '@ngrx/store';

import { Observable } from 'rxjs';

import { SimulationConfigState, SimulationSetupState } from './simulation-config.reducer';

export const selectSimulationSetup = createFeatureSelector<SimulationSetupState>("simulationSetup");

const selectSimulationDefaultConfig = createSelector(
    selectSimulationSetup,
    simulationSetup => simulationSetup.defaultConfig
);

const getConfigurableShapeNames = createSelector(
    selectSimulationSetup,
    simulationSetup => simulationSetup.configurableShapes
);

const selectSimulationDefaultConfigValue = createSelector(
    selectSimulationDefaultConfig,
    (state: SimulationConfigState) => state.value
);

const selectSimulationConfigSVGLoaded = createSelector(
    selectSimulationSetup,
    (state: SimulationSetupState) => state.svgLoaded
);

const selectSimulationConfigConnections = createSelector(
    selectSimulationDefaultConfigValue,
    (state: any) => state.con
);

const selectSimulationDefaultConfigLoaded = createSelector(
    selectSimulationDefaultConfig,
    (state: SimulationConfigState) => state.loaded
);

@Injectable({providedIn: 'root'})
export class SimulationConfigSelectorService {

    simulationDefaultConfigValue$: Observable<any> = this.store.select(selectSimulationDefaultConfigValue);
    simulationDefaultConfigLoaded$: Observable<boolean> = this.store.select(selectSimulationDefaultConfigLoaded);
    simulationConfigConnections$: Observable<any> = this.store.select(selectSimulationConfigConnections);
    configurableShapeNames$: Observable<string[]> = this.store.select(getConfigurableShapeNames);

    simulationConfigSVGLoaded$: Observable<boolean> = this.store.select(selectSimulationConfigSVGLoaded);

    constructor(private store: Store<SimulationSetupState>) { }
}
