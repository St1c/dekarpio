import { createActionGroup, emptyProps, props } from '@ngrx/store';
import {ConfigEntity, SimulationDefault} from './simulation-config.reducer';
import { ElementRef } from '@angular/core';

// export const loadDefaultConfig = createAction('[API] Load default config');

export const SimulationDefaultConfigActions = createActionGroup({
  source: 'Simulation Config Defaults',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: SimulationDefault }>(),
    'Update config': props<{ unit_type: string, unit_id: string, config: any }>(),
    'Set configurable shapes': props<{ configurableShapes: string[] }>(),
  }
});

export const SimulationSetupAPIActions = createActionGroup({
  source: 'Simulation API',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: SimulationDefault }>(),
    'Loading config IDs success': props<{ configs: ConfigEntity[] }>(),
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
    'Set active config': props<{ id: string }>(),
    'Set active config Done': emptyProps(),
    'SVG Loaded': emptyProps(),
    'SVG update on config change': props<{svgElement: ElementRef}>(),

    // defining an event with payload using the `props` function
    // 'Pagination Changed': props<{ page: number; offset: number }>(),

    // defining an event with payload using the props factory
    // 'Query Changed': (query: string) => ({ query }),
  }
});
