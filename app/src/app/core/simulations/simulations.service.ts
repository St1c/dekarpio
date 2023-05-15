import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
import { AuthService } from '../auth/auth.service';
import { ConfigEntity } from 'src/app/shared/types/config-entity';

export interface Simulation {
  id?: number;
  user_id?: number;
  name?: string;
  settings?: string;
  results?: string;
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

  createSimulation(config: ConfigEntity): Observable<any> {
    console.log('create simulation', config);

    return this.http.post<Simulation>(`${this.apiUrl}/simulation-setup`, {
      name: config.name,
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
      tap((res: any) => console.log('get last X', res)),
      map((res: any) => res.data),
      map((simulations: Simulation[]) => simulations.map((simulation: Simulation) => {
        return {
          id: simulation.id || 0,
          user_id: simulation.user_id || 0,
          name: simulation.name || '',
          settings: JSON.parse(simulation.settings || '{}'),
        };
      }))
    );
  }

  validateSimulation(): Observable<any> {
    const userId = this.auth.getAuthPayload().id;
    return this.http.post(`${this.flaskUrl}/validate`, {
      user_id: userId,
    });
  }
}
