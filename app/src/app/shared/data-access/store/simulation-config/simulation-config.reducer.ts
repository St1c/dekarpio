import { createReducer, on } from '@ngrx/store';
import {
  SimulationDefaultConfigActions,
  SimulationSetupPageActions
} from './simulation-config.actions';

export interface SimulationConfigState {
  value: { [key: string]: any; };
  loading: boolean;
  loaded: boolean;
}

export interface SimulationSetupState {
  defaultConfig: SimulationConfigState;
  configurableShapes: string[];
  svgLoaded: boolean;
}

export const initialSimulationConfigState: SimulationSetupState = {
  defaultConfig: {
    value: {},
    loading: false,
    loaded: false,
  },
  configurableShapes: [''],
  svgLoaded: false,
};


export const simulationConfigReducer = createReducer(
  initialSimulationConfigState,

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

  on(SimulationSetupPageActions.svgLoaded, (state) => (
    {
      ...state,
      svgLoaded: true
    }
  )),

);
