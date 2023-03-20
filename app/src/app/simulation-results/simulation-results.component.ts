import { DOCUMENT } from '@angular/common';
import { Component, Inject, OnInit, Renderer2 } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { AuthService } from 'ng2-ui-auth';

import { environment } from 'src/environments/environment';

@Component({
    selector: 'app-simulation-results',
    templateUrl: './simulation-results.component.html',
    styleUrls: ['./simulation-results.component.scss'],
    standalone: true
})
export class SimulationResultsComponent implements OnInit {

  dashUrl: SafeResourceUrl;
  dashBaseUrl = environment.dashUrl;

  constructor(
    private auth: AuthService,
    private sanitizer: DomSanitizer,
    @Inject(DOCUMENT) private document: Document,
    private renderer: Renderer2,
  ) {
    const userId = this.auth.getPayload().id;

    this.dashUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
      `${this.dashBaseUrl}/${userId}?jwt=${this.auth.getToken()}`
    );
  }

  ngOnInit(): void {
    this.renderer.addClass(this.document.body, 'simulation-results');
  }

  ngOnDestroy(): void {
    this.renderer.removeClass(this.document.body, 'simulation-results');
  }

}
