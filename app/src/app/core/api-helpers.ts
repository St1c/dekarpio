import { Observable, throwError } from 'rxjs';
import { HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';

export const postHeaders = new HttpHeaders({
  'Content-Type': 'application/x-www-form-urlencoded'
});

export function handleError(error: any): Observable<string> {
  let message = (error instanceof HttpErrorResponse) ? error.error.error : error.message;

  return throwError(message);
}

@Injectable({
  providedIn: 'root'
})
export class ErrorHandlerService {
  constructor(
  ) { }

  handle(error: any) {
    let message;

    if (error instanceof HttpErrorResponse && typeof error.error.error != 'undefined') {
      message = error.error.error;
    } else {
      message = error.message;
    }

    return throwError(message);
  }
}
