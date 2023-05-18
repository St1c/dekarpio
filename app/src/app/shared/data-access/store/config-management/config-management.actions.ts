import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { ConfigEntity } from 'src/app/shared/types/config-entity';

export const ConfigsManagementActions = createActionGroup({
    source: 'Configs Management Page',
    events: {
      'Load configs': emptyProps(),
      'Loading configs success': props<{ configs: ConfigEntity[] }>(),
      'Loading configs success but empty': emptyProps(),
      'Update config': props<{ name: string | null }>(),
      'Updating config success': emptyProps(),
      'Validate config': emptyProps(),
      'Validating config success': emptyProps(),
      'Validating config failed': props<{errors: any}>(),
      'Delete config': props<{ id: number }>(),
      'Delete config success': props<{id: number}>(),
      'Delete config failed': props<{errors: any}>(),
    }
  });