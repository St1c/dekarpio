import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { SimulationDefault } from './simulation-config.reducer';

// export const loadDefaultConfig = createAction('[API] Load default config');

export const SimulationDefaultConfigActions = createActionGroup({
  source: 'Simulation Config Defaults',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: SimulationDefault, configurableShapes: string[] }>(),
    'Update config': props<{ unit_type: string, unit_id: string, config: any }>(),
  }
});

export const SimulationSetupAPIActions = createActionGroup({
  source: 'Simulation API',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: SimulationDefault }>(),
    'Update config': props<{ config: any }>(),
    'Updating config success': emptyProps(),
    'Create config': emptyProps(),
    'Creating config success': emptyProps(),
    'Validate config': emptyProps(),
    'Validating config success': emptyProps(),
  }
});

export const SimulationSetupPageActions = createActionGroup({
  source: 'Simulation Setup',
  events: {
    // defining an event without payload using the `emptyProps` function
    'Opened': emptyProps(),
    'SVG Loaded': emptyProps(),
    
    // defining an event with payload using the `props` function
    // 'Pagination Changed': props<{ page: number; offset: number }>(),
    
    // defining an event with payload using the props factory
    // 'Query Changed': (query: string) => ({ query }),
  }
});