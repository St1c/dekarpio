import { BehaviorSubject, Observable } from 'rxjs';
import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

import { AuthService as ngAuthService } from 'ng2-ui-auth';
import { catchError, map } from 'rxjs/operators';

import { handleError } from '../api-helpers';
import { environment } from 'src/environments/environment';


export const AuthConfig = {
  baseUrl: environment.apiUrl,
  tokenPrefix: 'dekarpio',
};

export interface AuthPayload {
  admin: number;
  id?: number;
  iat?: number;
  exp?: number;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService implements CanActivate {

  isAuthenticated$: Observable<boolean>;
  private isAuthenticatedSubject: BehaviorSubject<boolean>;

  constructor(
    private auth: ngAuthService,
    private router: Router
  ) {
    this.isAuthenticatedSubject = new BehaviorSubject<boolean>(false);
    this.isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

    if (!this.auth.isAuthenticated()) return;

    const authPayload = this.getAuthPayload();

    // If user authentication is valid on app start, dispatch event
    this.isAuthenticatedSubject.next(true);
  }

  canActivate() {
    let canActivate = this.redirectUnauthenticatedUser();
    if (canActivate) this.isAuthenticatedSubject.next(true);

    return canActivate;
  }

  login(loginData: { username: string, password: string; }) {
    return this.auth.login(loginData).pipe(
      map(this.grantAccess.bind(this)),
      catchError(this.denyAccess.bind(this))
    );
  }

  logoutUser() {
    this.auth.logout().subscribe(() => {
      this.redirectUnauthenticatedUser();
    });
  }

  redirectUnauthenticatedUser() {
    if (!this.auth.isAuthenticated()) {
      this.router.navigate(['login']);
      return false;
    }

    return true;
  }

  grantAccess(response: Response | any) {
    this.router.navigate(['simulation-setup']);
    return this.auth.getPayload();
  }

  denyAccess(error: Response | any): Observable<string> {
    return handleError(error);
  }

  getAuthPayload() {
    return this.auth.getPayload();
  }
}
