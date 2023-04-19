import { Component, ElementRef, ViewChild } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Router } from '@angular/router';

import { InlineSVGModule } from 'ng-inline-svg';
import { Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { Store } from '@ngrx/store';

import { Simulation, SimulationsService } from '../core/simulations/simulations.service';
import { SimulationSetupDialogComponent } from '../simulation-setup-dialog/simulation-setup-dialog.component';
import { SvgElementToolsService } from '../shared/utils/svg-element-tools.service';
import { SvgElementsHoverListenerDirective } from '../shared/ui/svg-elements-hover-listener/svg-elements-hover-listener.directive';
import { SimulationSetupPageActions } from '../shared/data-access/store/simulation-config';
import { SimulationConfigSelectorService } from '../shared/data-access/store/simulation-config/simulation-config.selectors';
import { AsyncPipe } from '@angular/common';
import { SvgElementsClickListenerDirective } from '../shared/ui/svg-elements-click-listener/svg-elements-click-listener.directive';
import { Observable } from 'rxjs';
import { SimulationContextMenuDialogComponent } from '../simulation-context-menu-dialog/simulation-context-menu-dialog.component';
import { SvgElementsRightClickListenerDirective } from '../shared/ui/svg-elements-right-click-listener/svg-elements-right-click-listener.directive';

export interface DialogData {
  title: any;
  desc: any;
  element: any;
  config: any;
}

@Component({
  selector: 'app-simulation-setup',
  templateUrl: './simulation-setup.component.html',
  styleUrls: ['./simulation-setup.component.scss'],
  standalone: true,
  imports: [
    AsyncPipe,
    ReactiveFormsModule,
    InlineSVGModule,

    MatButtonModule,
    MatDialogModule,

    SvgElementsHoverListenerDirective,
    SvgElementsClickListenerDirective,
    SvgElementsRightClickListenerDirective
  ],
})
export class SimulationSetupComponent {

  @ViewChild('layout', { static: false }) svgLayout!: ElementRef;

  clickedSvgElement: string = '';
  config!: any;
  configurableShapes$: Observable<string[]> = this.simulationConfigSelectorService.configurableShapeNames$;

  private subs = new Subscription();

  constructor(
    public dialog: MatDialog,
    private simulationService: SimulationsService,
    private router: Router,
    private svgTools: SvgElementToolsService,
    private store: Store<{simulationConfig: any}>,
    private simulationConfigSelectorService: SimulationConfigSelectorService
  ) {}

  ngOnInit() {
    this.store.dispatch(SimulationSetupPageActions.opened());

    this.subs.add(this.simulationConfigSelectorService.simulationDefaultConfigValue$
      .subscribe((defaultConfig: Simulation) => {
        this.config = Object.assign({}, { ...defaultConfig });
      })
    );
  }

  svgLoaded() {
    this.store.dispatch(SimulationSetupPageActions.svgLoaded());
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  processConfig() {
    this.subs.add(
      this.simulationService.createSimulation(JSON.stringify(this.config))
        .pipe(
          switchMap((res: any) => this.simulationService.validateSimulation()
          ))
        .subscribe((res: any) => {
          this.router.navigate(['/simulation-results']);
        })
    );
  }

  svgClicked(event: any, contextMenu = false) {
    // API has changed, see: https://stackoverflow.com/questions/39245488/event-path-is-undefined-running-in-firefox/39245638#39245638
    const path = event.composedPath ? event.composedPath() : event.path;

    for (const element of path) {
      if (element.id) {
        const title = element.querySelector('title');
        const desc = element.querySelector('desc');

        if (!title) return; // @TODO: Probably not needed anymore since clickable elements come from json config

        this.clickedSvgElement = desc?.innerHTML;

        let unit_type: any, unit_id: any, rest;
        [unit_type, unit_id, ...rest] = title?.innerHTML?.split('_');
        const unit_config = { unit_type, unit_id, ...this.config[unit_type][unit_id] };

        console.log(unit_config);
        
        unit_config ?? new Error('Missing config for given unit');
        if (contextMenu) {
          this.openContextDialog(title, desc, element, unit_config);
          break;
        }
        this.openDialog(title, desc, element, unit_config);
        break;
      }
    }
  }

  private openDialog(title: any, desc: any, element: any, config: any) {
    const ref = this.dialog.open(SimulationSetupDialogComponent, {
      data: { title, desc, element, config },
    });

    this.subs.add(ref.afterClosed().subscribe(result => {
      if (result) {
        this.updateConfig(result);
        this.applyElementSettings(result);
      };
    }));
  }

  private openContextDialog(title: any, desc: any, element: any, config: any) {
    const ref = this.dialog.open(SimulationContextMenuDialogComponent, {
      data: { title, desc, element, config },
    });

    this.subs.add(ref.afterClosed().subscribe(result => {
      if (result) {
        this.updateConfig(result);
        this.applyElementSettings(result);
      };
    }));
  }


  private updateConfig(result: { element: any, state: boolean, params: any; }) {
    const params_id = result.params.ID;
    let [type, id, ...rest] = params_id.split('_');
    const { unit_type = '', unit_id = '', ...params } = { ...result.params };
    console.log(params)
    this.config[type][id] = { ...params };
  }

  private applyElementSettings(result: { element: any, state: boolean, params: any; }) {
    const matchingConnections = this.disableConnectionsByInOutIds(result.params.ID);
    this.findConnecstionLinesById([result.params.ID, ...matchingConnections], result.state);

    const title = result.element.getElementsByTagName('title')[0]?.innerHTML;
    const siblings = this.svgTools.findAllElementsContainingTitle(title, this.svgLayout.nativeElement);

    for (let i = 0; i < siblings.snapshotLength; i++) {
      const item = siblings.snapshotItem(i) as HTMLElement;
      result.state ? item.classList.remove('inactive') : item.classList.add('inactive');
    }
  }

  private disableConnectionsByInOutIds(id: string): string[] {
    const connections = Object.keys(this.config['con']);
    let matching_IDs: string[] = [];
    connections.map(key => {
      if (this.config['con'][key]['in'] === id || this.config['con'][key]['out'] === id) {
        matching_IDs.push(this.config['con'][key]['ID']);
      }
    });

    return [...matching_IDs];
  }

  private findConnecstionLinesById(ids: string[], state: boolean) {
    ids.map(id => {
      const item: HTMLElement | null = this.svgTools.findElementByName(id, this.svgLayout.nativeElement) as HTMLElement;
      state ? item?.classList.remove('inactive') : item?.classList.add('inactive');
    });
  }

}
