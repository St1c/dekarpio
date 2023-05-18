import { Store, createFeatureSelector, createSelector } from '@ngrx/store';
import { Injectable } from '@angular/core';

import * as fromConfigsManagement from './config-management.reducer';

export const selectConfigsManagementState = createFeatureSelector<fromConfigsManagement.ConfigsManagementState>('configsManagement');

const selectConfigIds = createSelector(
    selectConfigsManagementState,
    fromConfigsManagement.selectIds
);

const selectConfigEntitites = createSelector(
    selectConfigsManagementState,
    fromConfigsManagement.selectEntities
);

const selectAllConfigs = createSelector(
    selectConfigsManagementState,
    fromConfigsManagement.selectAll
);


@Injectable({providedIn: 'root'})
export class ConfigsManagementSelectorsService {

    configIds$ = this.store.select(selectConfigIds);
    configEntities$ = this.store.select(selectConfigEntitites);
    allConfigs$ = this.store.select(selectAllConfigs);

    constructor(private store: Store<fromConfigsManagement.ConfigsManagementState>) { }
}