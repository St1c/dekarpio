import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor
} from '@angular/common/http';

import { Observable } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor() { }

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Remove Authorization header from calls to google api - it causes 401 Error
    if (request.url.includes('googleapis')) {

      request = request.clone({
        setHeaders: {
          Authorization: ''
        }
      });
    }

    return next.handle(request);
  }
}
