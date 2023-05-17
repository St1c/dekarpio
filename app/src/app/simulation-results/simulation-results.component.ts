import { DOCUMENT } from '@angular/common';
import { Component, Inject, OnInit, Renderer2 } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { AuthService } from 'ng2-ui-auth';

import { environment } from 'src/environments/environment';
import { ConfigEntitySelectorService } from '../shared/data-access/store/simulation-config/config-entity.selectors';

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
    private configEntitySelectors: ConfigEntitySelectorService,
  ) {
    const userId = this.auth.getPayload().id;
    
    this.dashUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
      `${this.dashBaseUrl}/${userId}?jwt=${this.auth.getToken()}&configId=0`
    );

    this.configEntitySelectors.simulationActiveConfig$.subscribe((config) => {
      if (config) {
        this.dashUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
          `${this.dashBaseUrl}/${userId}?jwt=${this.auth.getToken()}&configId=${config.id}`
        );
      }
    });
  }

  ngOnInit(): void {
    this.renderer.addClass(this.document.body, 'simulation-results');
  }

  ngOnDestroy(): void {
    this.renderer.removeClass(this.document.body, 'simulation-results');
  }

}
