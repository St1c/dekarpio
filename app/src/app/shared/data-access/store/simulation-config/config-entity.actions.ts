import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { ConfigEntity } from 'src/app/shared/types/config-entity';

export const ConfigEntityActions = createActionGroup({
    source: 'Simulations API',
    events: {
      'Load configs': emptyProps(),
      'Loading configs success': props<{ configs: ConfigEntity[], id: number }>(),
      'Loading configs success but empty': emptyProps(),
      'Update config': props<{ id: number, config: any }>(),
      'Updating config success': emptyProps(),
      'Create config': props<{ name: any }>(),
      'Creating config success': emptyProps(),
      'Validate config': emptyProps(),
      'Validating config success': emptyProps(),
    }
  });