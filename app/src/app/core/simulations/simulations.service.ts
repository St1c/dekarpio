import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from '../auth/auth.service';

export interface Simulation {
  id?: number;
  user_id?: number;
  settings?: string;
  results?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SimulationsService {

  private userId: number;

  constructor(
    private http: HttpClient,
    private auth: AuthService,
  ) {
    this.userId = this.auth.getAuthPayload().id;
  }

  createSimulation(settings: string): Observable<any> {
    return this.http.post<Simulation>('/api/simulation-setup', {
      settings,
    });
  }

  getSimulation(): Observable<Simulation> {
    return this.http.get(`/api/simulation-results/${this.userId}`).pipe(
      map((res: any) => res.data[0]),
    );
  }

  validateSimulation(): Observable<any> {  
    return this.http.post('/dash/validate', {
      user_id: this.userId,
    });
  }
}
