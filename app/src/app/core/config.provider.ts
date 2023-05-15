import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { SimulationJson } from '../shared/types/simulation-json';


@Injectable({
  providedIn: 'root'
})
export class ConfigProvider {

  private metaDataConfig_: any;

  constructor(
    private http: HttpClient
  ) { }

  get metaDataConfig() {
    return this.metaDataConfig_;
  }

  getParamsConfig(): Observable<Object> {
    return this.http.get('/assets/metadata_nov.json').pipe(
      tap((config: any) => this.metaDataConfig_ = config)
    );
  }

  getConfigFromAssets(): Observable<SimulationJson> {
    return this.http.get<SimulationJson>('/assets/tool_dekarpio_nov.json');
  }
}
