import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { ConfigEntity } from 'src/app/shared/types/config-entity';

export const ConfigEntityActions = createActionGroup({
    source: 'Simulations API',
    events: {
      'Load configs': emptyProps(),
      'Loading configs success': props<{ configs: ConfigEntity[], id: number }>(),
      'Loading configs success but empty': emptyProps(),
      'Config touched': emptyProps(),
      'Create config': props<{ name: string | null}>(),
      'Creating config success': emptyProps(),
      'Update config': props<{ name: string | null }>(),
      'Updating config success': emptyProps(),
      'Processing config success': emptyProps(),
      'Validate config': emptyProps(),
      'Validating config success': emptyProps(),
      'Validating config failed': props<{errors: any}>(),
    }
  });