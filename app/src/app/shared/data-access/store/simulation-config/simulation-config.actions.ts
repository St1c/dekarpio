import { ElementRef } from '@angular/core';
import { createActionGroup, emptyProps, props } from '@ngrx/store';

import { SimulationJson } from 'src/app/shared/types/simulation-json';

// export const loadDefaultConfig = createAction('[API] Load default config');

export const SimulationDefaultConfigActions = createActionGroup({
  source: 'Simulation Config Defaults',
  events: {
    'Load config': emptyProps(),
    'Loading config success': props<{ config: SimulationJson }>(),
    'Update config': props<{ unit_type: string, unit_id: string, config: any }>(),
    'Set configurable shapes': props<{ configurableShapes: string[] }>(),
    'Enable configurable shape': props<{ unit_type: string, unit_id: string }>(),
    'Disable configurable shape': props<{ unit_type: string, unit_id: string }>(),
  }
});

export const SimulationSetupPageActions = createActionGroup({
  source: 'Simulation Setup Page',
  events: {
    // defining an event without payload using the `emptyProps` function
    'Opened': emptyProps(),
    'Set active config': props<{ id: number }>(),
    'Set active config Done': emptyProps(),
    'SVG Loaded': emptyProps(),
    'SVG update on config change': props<{svgElement: ElementRef}>(),
    'Go to simulation results': props<{currentNameFieldValue: string}>(),

    // defining an event with payload using the `props` function
    // 'Pagination Changed': props<{ page: number; offset: number }>(),

    // defining an event with payload using the props factory
    // 'Query Changed': (query: string) => ({ query }),
  }
});
