import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { Observable } from 'rxjs';
import { map, tap } from 'rxjs/operators';

import { environment } from 'src/environments/environment';

import { AuthService } from '../auth/auth.service';
import { ConfigEntity } from 'src/app/shared/types/config-entity';

export interface Simulation {
  id?: number;
  user_id?: number;
  email?: string;
  name?: string;
  settings?: string;
  results?: string;
  created_at?: string;
  updated_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SimulationsService {

  private apiUrl = environment.apiUrl;
  private flaskUrl = environment.flaskUrl;

  constructor(
    private http: HttpClient,
    private auth: AuthService,
  ) { }

  createSimulation(name: string | null, config: ConfigEntity): Observable<any> {
    return this.http.post<Simulation>(`${this.apiUrl}/simulation-setup`, {
      name: name || 'Missing name',
      settings: JSON.stringify(config.settings),
    });
  }

  updateSimulation(name: string | null, config: ConfigEntity): Observable<any> {
    return this.http.put<Simulation>(`${this.apiUrl}/simulation-setup/${config.id}`, {
      name: name || 'Missing name',
      settings: JSON.stringify(config.settings),
    });
  }

  getSimulation(): Observable<Simulation> {
    const userId = this.auth.getAuthPayload().id;
    return this.http.get(`${this.apiUrl}/simulation-results/${userId}`).pipe(
      tap((res: any) => console.log('get simulation', res)),
      map((res: any) => res.data[0]),
    );
  }

  getSimulations(limit: number): Observable<ConfigEntity[]> {
    const userId = this.auth.getAuthPayload().id;
    return this.http.get(`${this.apiUrl}/simulation-results/last/${userId}/${limit}`).pipe(
      map((res: any) => res.data),
      map((simulations: Simulation[]) => simulations.map((simulation: Simulation) => this.mapSimulation(simulation)))
    );
  }

  getAllSimulations(): Observable<ConfigEntity[]> {
    const userId = this.auth.getAuthPayload().id;
    return this.http.get(`${this.apiUrl}/simulation-results/all/${userId}`).pipe(
      map((res: any) => res.data),
      map((simulations: Simulation[]) => simulations.map((simulation: Simulation) => this.mapSimulation(simulation)))
    );
  }

  validateSimulation(configId: string): Observable<any> {
    const userId = this.auth.getAuthPayload().id;
    return this.http.post(`${this.flaskUrl}/validate`, {
      user_id: userId,
      config_id: configId
    });
  }

  deleteSimulation(configId: number): Observable<number> {
    return this.http.delete(`${this.apiUrl}/simulation-setup/${configId}`).pipe(
      map((res: any) => res.data),
      map((data: {id: number, msg: string}) => +data.id),
    );
  }

  private mapSimulation(simulation: Simulation): ConfigEntity {
    return {
      id: simulation.id || 0,
      user_id: simulation.user_id || 0,
      email: simulation.email || '',
      name: simulation.name || '',
      created_at: simulation.created_at || '',
      updated_at: simulation.updated_at || '',
      settings: JSON.parse(simulation.settings || '{}'),
    };
  }
}
