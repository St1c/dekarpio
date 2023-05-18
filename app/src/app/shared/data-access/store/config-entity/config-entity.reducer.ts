
import { EntityAdapter, EntityState, createEntityAdapter } from '@ngrx/entity';
import { createReducer, on } from '@ngrx/store';

import { ConfigEntity } from 'src/app/shared/types/config-entity';
import { SimulationJson } from 'src/app/shared/types/simulation-json';
import { ConfigEntityActions } from './config-entity.actions';
import { SimulationDefaultConfigActions, SimulationSetupPageActions } from '../simulation-config';

export interface ConfigEntityState extends EntityState<ConfigEntity> {
  // additional entities state properties
  selectedConfigId: number;
  activeConfig: { [key: string]: any; };
  configValid: boolean;
}

export const adapter: EntityAdapter<ConfigEntity> = createEntityAdapter<ConfigEntity>({
  // selectId: selectByConfigName,
});

export const initialConfigIdsState: ConfigEntityState = adapter.getInitialState({
  // additional entity state properties
  selectedConfigId: 1,
  activeConfig: {},
  configValid: true,
});

export const configEntityReducer = createReducer(
  initialConfigIdsState,

  on(SimulationDefaultConfigActions.loadingConfigSuccess, (state, { config }) => {
    const simEntity = {
      id: 0,
      user_id: 0,
      name: 'Default',
      settings: config,
      created_at: ''
    };
    return adapter.setOne(simEntity, state);
  }),

  on(
    ConfigEntityActions.loadingConfigsSuccess,
    ConfigEntityActions.processingConfigSuccess,
    (state, { configs }) => {
    return adapter.setMany(configs, state);
  }),

  on(ConfigEntityActions.configTouched, (state) => {
    return {
      ...state,
      configValid: false
    }
  }),

  on(ConfigEntityActions.validatingConfigSuccess, (state) => {
    return {
      ...state,
      configValid: true
    }
  }),

  on(
    SimulationSetupPageActions.setActiveConfig, 
    ConfigEntityActions.setActiveConfigAfterApiCall,
    (state, { id }) => {
    console.log('setActiveConfig', id);
    return {
      ...state,
      selectedConfigId: +id,
      activeConfig: {
        ...state.entities[+id],
      },
    };
  }),

  on(SimulationDefaultConfigActions.updateConfig, (state, { unit_type, unit_id, config }) => ({
    ...state,
    activeConfig: {
      ...state.activeConfig,
      settings: {
        ...state.activeConfig.settings,
        [unit_type]: {
          ...state.activeConfig.settings[unit_type as keyof SimulationJson],
          [unit_id]: {
            ...config
          }
        }
      }
    }
  })),

  on(SimulationDefaultConfigActions.enableConfigurableShape, (state, { unit_type, unit_id }) => {
    console.log(state)
    return {
    ...state,
    activeConfig: {
      ...state.activeConfig,
      settings: {
        ...state.activeConfig.settings,
        [unit_type]: {
          ...state.activeConfig.settings[unit_type as keyof SimulationJson],
          [unit_id]: {
            ...state.activeConfig.settings[unit_type as keyof SimulationJson][unit_id],
            param: [{
              ...state.activeConfig.settings[unit_type as keyof SimulationJson][unit_id].param[0],
              integrate: true
            }],
          }
        }
      }
    }
  }}),

  on(SimulationDefaultConfigActions.disableConfigurableShape, (state, { unit_type, unit_id }) => ({
    ...state,
    activeConfig: {
      ...state.activeConfig,
      settings: {
        ...state.activeConfig.settings,
        [unit_type]: {
          ...state.activeConfig.settings[unit_type as keyof SimulationJson],
          [unit_id]: {
            ...state.activeConfig.settings[unit_type as keyof SimulationJson][unit_id],
            param: [{
              ...state.activeConfig.settings[unit_type as keyof SimulationJson][unit_id].param[0],
              integrate: false
            }],
          }
        }
      }
    }
  })),

);

// get the selectors
export const {
  selectIds,
  selectEntities,
  selectAll,
  selectTotal,
} = adapter.getSelectors();