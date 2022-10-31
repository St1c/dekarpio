import { NgModule, Optional, SkipSelf } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';

import { Ng2UiAuthModule } from 'ng2-ui-auth';

import { AuthConfig } from './auth/auth.service';
import { AuthInterceptor } from './auth/auth.interceptor';
import { EffectsModule } from '../effects/effects.module';
import { MetadataEffects } from '../effects/meta-data.effect';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    HttpClientModule,
    Ng2UiAuthModule.forRoot(AuthConfig),
    EffectsModule.register([
      MetadataEffects
    ])
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
})
export class CoreModule {
  constructor(@Optional() @SkipSelf() parentModule: CoreModule) {
    if (parentModule) {
      throw new Error(
        'CoreModule is already loaded. Import it in the AppModule only');
    }
  }
}
