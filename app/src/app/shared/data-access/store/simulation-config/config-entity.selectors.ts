import { Store, createFeatureSelector, createSelector } from '@ngrx/store';
import * as fromConfigEntity from './config-entity.reducer';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export const selectConfigsState = createFeatureSelector<fromConfigEntity.ConfigEntityState>('configEntities');

const selectedConfigId = (state: fromConfigEntity.ConfigEntityState) => state.selectedConfigId;

const selectConfigIds = createSelector(
    selectConfigsState,
    fromConfigEntity.selectIds
);

const selectConfigEntitites = createSelector(
    selectConfigsState,
    fromConfigEntity.selectEntities
);

const selectAllConfigs = createSelector(
    selectConfigsState,
    fromConfigEntity.selectAll
);

const selectSelectedConfigId = createSelector(
    selectConfigsState,
    selectedConfigId
);

const selectCurrentConfig = createSelector(
    selectConfigEntitites,
    selectSelectedConfigId,
    (configEntities, configId) => configEntities[configId]
);

const selectSimulationActiveConfig = createSelector(
    selectConfigsState,
    simulationSetup => simulationSetup.activeConfig
);

const selectSimulationActiveConfigSettings = createSelector(
    selectSimulationActiveConfig,
    simulationSetup => simulationSetup.settings
);

@Injectable({providedIn: 'root'})
export class ConfigEntitySelectorService {

    configIds$ = this.store.select(selectConfigIds);
    configEntities$ = this.store.select(selectConfigEntitites);
    allConfigs$ = this.store.select(selectAllConfigs);
    selectedConfigId$: Observable<number> = this.store.select(selectSelectedConfigId);
    selectCurrentConfig$ = this.store.select(selectCurrentConfig);
    simulationActiveConfig$: Observable<{[key: string]: any}> = this.store.select(selectSimulationActiveConfig);
    simulationActiveConfigSettings$: Observable< {[key: string]: any}> = this.store.select(selectSimulationActiveConfigSettings);

    constructor(private store: Store<fromConfigEntity.ConfigEntityState>) { }
}