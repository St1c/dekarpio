import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

import { AuthService } from './core/auth/auth.service';
@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.scss'],
    standalone: true,
    imports: [
      MatButtonModule,
      MatIconModule,
      MatToolbarModule,
      RouterLink, 
      RouterOutlet
    ]
})
export class AppComponent {

  constructor(
    private authService: AuthService,
  ) { }

  logout() {
    this.authService.logoutUser();
  }

}
