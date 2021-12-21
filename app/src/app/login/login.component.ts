import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

import { AuthService } from '../core/auth/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {

  public loginForm: FormGroup;

  constructor(
    private fb: FormBuilder,
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
