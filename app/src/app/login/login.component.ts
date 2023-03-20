import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators, ReactiveFormsModule } from '@angular/forms';

import { AuthService } from '../core/auth/auth.service';
import { MatButtonModule } from '@angular/material/button';
import { NgIf } from '@angular/common';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';

@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss'],
    standalone: true,
    imports: [MatCardModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule, NgIf, MatButtonModule]
})
export class LoginComponent implements OnInit {

  public loginForm: UntypedFormGroup;

  constructor(
    private fb: UntypedFormBuilder,
    private authService: AuthService
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  ngOnInit() { }

  onSubmit() {
    console.log('submit');
    this.authService.login(this.loginForm.value).subscribe(_ => console.log(_));
  }

  get emailRequiredError() {
    return this.loginForm.get('email')?.hasError('required');
  }

  get emailFormatError() {
    return this.loginForm.get('email')?.hasError('email');
  }

  get passwordRequiredError() {
    return this.loginForm.get('password')?.hasError('required');
  }
}
