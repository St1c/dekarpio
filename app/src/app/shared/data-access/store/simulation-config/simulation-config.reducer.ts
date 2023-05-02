import { createReducer, on } from '@ngrx/store';
import { SimulationDefaultConfigActions, SimulationSetupAPIActions, SimulationSetupPageActions } from './simulation-config.actions';
import {createEntityAdapter, EntityAdapter, EntityState} from "@ngrx/entity";

export interface AppState {
  simulationSetup: SimulationSetup;
}

export interface ConfigEntity {
  id: number;
  user_id: number;
  settings: string;
}

export interface SimulationDefault {
  eso: {},
  par: {},
  eco: {},
  con: {},
  col: {},
  ecu: {},
  esu: {},
  dem: {},
}
export interface SimulationConfigState {
  value: {[key: string]: any};
  loading: boolean;
  loaded: boolean;
}

export interface SimulationSetup {
  activeConfig: {[key: string]: any};
  defaultConfig: SimulationConfigState;
  config: SimulationConfigState;
  configurableShapes: string[];
  svgLoaded: boolean;
}

export const initialSimulationConfigState: SimulationSetup = {
  activeConfig: {},
  defaultConfig: {
    value: {},
    loading: false,
    loaded: false,
  },
  config: {
    value: {},
    loading: false,
    loaded: false,
  },
  configurableShapes: [''],
  svgLoaded: false,
};

export interface State extends EntityState<ConfigEntity> {
  // additional entities state properties
  selectedConfigId: number | 0;
}

export const configEntitydapter: EntityAdapter<ConfigEntity> = createEntityAdapter<ConfigEntity>();

export const initialConfigIdsState: State = configEntitydapter.getInitialState({
  // additional entity state properties
  selectedConfigId: 0,
});

export const configEntityReducer = createReducer(
  initialConfigIdsState,
  on(SimulationSetupAPIActions.loadingConfigIdsSuccess, (state, {configs }) => {
    return configEntitydapter.setAll(configs, state);
  }),
);

export const simulationConfigReducer = createReducer(
  initialSimulationConfigState,

  // on(SimulationSetupPageActions.opened, (state) => (
  //   {
  //     ...state,
  //     defaultConfig: {
  //       ...state.defaultConfig,
  //       loading: true,
  //     },
  //     config: {
  //       ...state.config,
  //       loading: true,
  //     }
  //   }
  // )),

  on(SimulationDefaultConfigActions.loadConfig, (state) => (
    {
      ...state,
      defaultConfig: {
        ...state.defaultConfig,
        loading: true,
      }
    }
  )),

  on(SimulationDefaultConfigActions.loadingConfigSuccess, (state, { config }) => (
    {
      ...state,
      defaultConfig: {
        value: { ...config },
        loading: false,
        loaded: true,
      }
    }
  )),

  on(SimulationDefaultConfigActions.setConfigurableShapes, (state, { configurableShapes }) => (
    {
      ...state,
      configurableShapes: [...configurableShapes],
    }
  )),

  on(SimulationDefaultConfigActions.updateConfig, (state, { unit_type, unit_id, config }) => ({
    ...state,
    defaultConfig: {
      value: {
        ...state.defaultConfig.value,
        [unit_type]: {
          ...state.defaultConfig.value[unit_type as keyof SimulationDefault],
          [unit_id]: {
            ...config
          }
        }
      },
      loading: false,
      loaded: true,
    }
  })),

  on(SimulationSetupAPIActions.loadConfig, (state) => (
    {
      ...state,
      config: {
        ...state.config,
        loading: true,
      }
    }
  )),

  on(SimulationSetupAPIActions.loadingConfigSuccess, (state, action) => (
    {
      ...state,
      config: {
        value: { ...action.config },
        loading: false,
        loaded: true,
      },
    }
  )),

  on(SimulationSetupAPIActions.updateConfig, (state) => ({ ...state })),

  on(SimulationSetupPageActions.svgLoaded, (state) => (
    {
      ...state,
      svgLoaded: true
    }
  )),


  on(SimulationSetupPageActions.setActiveConfig, (state, { id }) => {
    if (id === 'latest') {
      return {
        ...state,
        activeConfig: {
          ...state.config.value,
        },
      };
    } else {
      return {
        ...state,
        activeConfig: {
          ...state.defaultConfig.value,
        },
      };
    }
  })
);
