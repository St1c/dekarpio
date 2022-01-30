import { Component, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { AuthService } from 'ng2-ui-auth';

@Component({
  selector: 'app-simulation-results',
  templateUrl: './simulation-results.component.html',
  styleUrls: ['./simulation-results.component.scss']
})
export class SimulationResultsComponent implements OnInit {

  dashUrl: SafeResourceUrl;

  constructor(
    private auth: AuthService,
    private sanitizer: DomSanitizer
  ) {
    this.dashUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
      `http://localhost/dash-server/?jwt=${this.auth.getToken()}`
    );
  }

  ngOnInit(): void {
  }

}
