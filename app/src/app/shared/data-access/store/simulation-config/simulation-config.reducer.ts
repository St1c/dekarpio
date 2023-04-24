import { createReducer, on } from '@ngrx/store';
import { Simulation } from 'src/app/core/simulations/simulations.service';
import { SimulationDefaultConfigActions, SimulationSetupAPIActions, SimulationSetupPageActions } from './simulation-config.actions';

export interface AppState {
  simulationSetup: SimulationSetup;
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
  defaultConfig: SimulationConfigState;
  config: SimulationConfigState;
  configurableShapes: string[];
  svgLoaded: boolean;
}

export const initialSimulationConfigState: SimulationSetup = {
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

);