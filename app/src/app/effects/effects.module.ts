import { Inject, InjectionToken, Injector, NgModule, Type } from '@angular/core';
import { isObservable, Observable } from 'rxjs';

const EFFECT = Symbol('EFFECT');

export function createEffect<T>(source: () => Observable<T> | void) {
  Object.defineProperty(source, EFFECT, { value: true });

  return source;
}

function isEffect(effect: any): any {
  return effect[EFFECT];
}

const EFFECTS_PROVIDERS = new InjectionToken('EFFECTS_PROVIDERS');

@NgModule({})
export class EffectsModule {
  constructor(
    @Inject(EFFECTS_PROVIDERS) providers: Type<any>[],
    injector: Injector
  ) {
    for (const provider of providers) {
      const currentProvider = injector.get(provider);

      for (const effectFactory of Object.values(currentProvider) as any)
        if (isEffect(effectFactory)) {
          const factory = effectFactory();

          if (isObservable(factory)) {
            factory.subscribe();
          }
        }
    }
  }

  static register(providers: Type<any>[]) {
    return {
      ngModule: EffectsModule,
      providers: [
        {
          provide: EFFECTS_PROVIDERS,
          useValue: providers,
        },
      ],
    };
  }
}
