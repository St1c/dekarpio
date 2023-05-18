
import { EntityAdapter, EntityState, createEntityAdapter } from '@ngrx/entity';
import { createReducer, on } from '@ngrx/store';

import { ConfigEntity } from 'src/app/shared/types/config-entity';
import { ConfigsManagementActions } from './config-management.actions';

export interface ConfigsManagementState extends EntityState<ConfigEntity> {
  // additional entities state properties
}

export const adapter: EntityAdapter<ConfigEntity> = createEntityAdapter<ConfigEntity>({
  selectId: (config: ConfigEntity) => config.id,
  sortComparer: false
});

export const initialConfigsState: ConfigsManagementState = adapter.getInitialState({
  // additional entity state properties
});

export const configsManagementReducer = createReducer(
  initialConfigsState,

  on(ConfigsManagementActions.loadingConfigsSuccess, (state, { configs }) => {
    return adapter.setMany(configs, state);
  }),

  on(ConfigsManagementActions.deleteConfigSuccess, (state, {id}) => {
    return adapter.removeOne(id, state);
  }),
);

// get the selectors
export const {
  selectIds,
  selectEntities,
  selectAll,
  selectTotal,
} = adapter.getSelectors();