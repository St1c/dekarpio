import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigProvider } from '../core/config.provider';
import { createEffect } from './effects.module';

@Injectable({ providedIn: 'root' })
export class MetadataEffects {

  metadata$ = createEffect(() =>
    this.configProvider.getParamsConfig().pipe()
  );

  constructor(private configProvider: ConfigProvider) {}
}
