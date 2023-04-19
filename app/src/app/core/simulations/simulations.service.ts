import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
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

  private apiUrl = environment.apiUrl;
  private flaskUrl = environment.flaskUrl;

  constructor(
    private http: HttpClient,
    private auth: AuthService,
  ) {}

  createSimulation(settings: string): Observable<any> {
    return this.http.post<Simulation>(`${this.apiUrl}/simulation-setup`, {
      settings,
    });
  }

  getSimulation(): Observable<Simulation> {
    const userId = this.auth.getAuthPayload().id;
    return this.http.get(`${this.apiUrl}/simulation-results/${userId}`).pipe(
      map((res: any) => res.data[0]),
    );
  }

  validateSimulation(): Observable<any> {  
    const userId = this.auth.getAuthPayload().id;
    return this.http.post(`${this.flaskUrl}/validate`, {
      user_id: userId,
    });
  }
}
