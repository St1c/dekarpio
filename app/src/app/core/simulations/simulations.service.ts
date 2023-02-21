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
  private userId: number;

  constructor(
    private http: HttpClient,
    private auth: AuthService,
  ) {
    this.userId = this.auth.getAuthPayload().id;
  }

  createSimulation(settings: string): Observable<any> {
    return this.http.post<Simulation>(`${this.apiUrl}/simulation-setup`, {
      settings,
    });
  }

  getSimulation(): Observable<Simulation> {
    return this.http.get(`${this.apiUrl}/simulation-results/${this.userId}`).pipe(
      map((res: any) => res.data[0]),
    );
  }

  validateSimulation(): Observable<any> {  
    return this.http.post(`${this.flaskUrl}/validate`, {
      user_id: this.userId,
    });
  }
}
