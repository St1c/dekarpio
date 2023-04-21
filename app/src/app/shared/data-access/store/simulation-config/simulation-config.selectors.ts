import { Injectable } from '@angular/core';
import { createSelector,  Store } from '@ngrx/store';

import { Observable } from 'rxjs';

import { AppState, SimulationConfigState, SimulationDefault, SimulationSetup } from './simulation-config.reducer';
import { Simulation } from 'src/app/core/simulations/simulations.service';

const getAppState = (state: AppState) => state;

const getSimulationSetup = createSelector(
    getAppState,
    (state: AppState) => state.simulationSetup
);

const getSimulationConfig = createSelector(
    getAppState,
    (state: AppState) => state.simulationSetup.config
);

const getSimulationDefaultConfig = createSelector(
    getAppState,
    (state: AppState) => state.simulationSetup.defaultConfig
);

const getConfigurableShapeNames = createSelector(
    getAppState,
    (state: AppState) => state.simulationSetup.configurableShapes
);

const getSimulationConfigValue = createSelector(
    getSimulationConfig,
    (state: SimulationConfigState) => state.value
);

const getSimulationConfigLoading = createSelector(
    getSimulationConfig,
    (state: SimulationConfigState) => state.loading
);

const getSimulationConfigLoaded = createSelector(
    getSimulationConfig,
    (state: SimulationConfigState) => state.loaded
);

const getSimulationDefaultConfigValue = createSelector(
    getSimulationDefaultConfig,
    (state: SimulationConfigState) => state.value
);

const getSimulationConfigConnections = createSelector(
    getSimulationDefaultConfigValue, 
    (state: SimulationDefault) => state.con
);

const getSimulationDefaultConfigLoading = createSelector(
    getSimulationDefaultConfig,
    (state: SimulationConfigState) => state.loading
);

const getSimulationDefaultConfigLoaded = createSelector(
    getSimulationDefaultConfig,
    (state: SimulationConfigState) => state.loaded
);

const getSimulationConfigSVGLoaded = createSelector(
    getSimulationSetup,
    (state: SimulationSetup) => state.svgLoaded
);

@Injectable({providedIn: 'root'})
export class SimulationConfigSelectorService {

    simulationConfig$: Observable<SimulationConfigState> = this.store.select(getSimulationConfig);
    simulationConfigValue$: Observable<SimulationDefault> = this.store.select(getSimulationConfigValue);
    simulationConfigLoading$: Observable<boolean> = this.store.select(getSimulationConfigLoading);
    simulationConfigLoaded$: Observable<boolean> = this.store.select(getSimulationConfigLoaded);

    simulationDefaultConfig$: Observable<SimulationConfigState> = this.store.select(getSimulationDefaultConfig);
    simulationDefaultConfigValue$: Observable<SimulationDefault> = this.store.select(getSimulationDefaultConfigValue);
    simulationDefaultConfigLoading$: Observable<boolean> = this.store.select(getSimulationDefaultConfigLoading);
    simulationDefaultConfigLoaded$: Observable<boolean> = this.store.select(getSimulationDefaultConfigLoaded);


    simulationConfigConnections$: Observable<any> = this.store.select(getSimulationConfigConnections);
    configurableShapeNames$: Observable<string[]> = this.store.select(getConfigurableShapeNames);

    simulationConfigSVGLoaded$: Observable<boolean> = this.store.select(getSimulationConfigSVGLoaded);

    constructor(private store: Store<AppState>) { }
}
