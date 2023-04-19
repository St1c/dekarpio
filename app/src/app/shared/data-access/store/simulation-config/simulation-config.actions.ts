import { createActionGroup, emptyProps, props } from '@ngrx/store';

// export const loadDefaultConfig = createAction('[API] Load default config');

export const SimulationDefaultConfigActions = createActionGroup({
  source: 'Simulation Config Defaults',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: any, configurableShapes: string[] }>(),
  }
});

export const SimulationSetupAPIActions = createActionGroup({
  source: 'Simulation API',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: any }>(),
    'Update config': props<{ config: any }>(),
    'Updating config success': emptyProps()
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