import { Component, ElementRef, ViewChild } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { InlineSVGModule } from 'ng-inline-svg';
import { Subscription } from 'rxjs';
import { Store } from '@ngrx/store';

import { SimulationSetupDialogComponent } from '../simulation-setup-dialog/simulation-setup-dialog.component';
import { SvgElementToolsService } from '../shared/utils/svg-element-tools.service';
import { SvgElementsHoverListenerDirective } from '../shared/ui/svg-elements-hover-listener/svg-elements-hover-listener.directive';
import { SimulationDefaultConfigActions, SimulationSetupAPIActions, SimulationSetupPageActions } from '../shared/data-access/store/simulation-config';
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
  unit_meta: any;
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
  configConnections!: any;
  configurableShapes$: Observable<string[]> = this.simulationConfigSelectorService.configurableShapeNames$;

  private subs = new Subscription();

  constructor(
    public dialog: MatDialog,
    private svgTools: SvgElementToolsService,
    private store: Store<{simulationConfig: any}>,
    private simulationConfigSelectorService: SimulationConfigSelectorService
  ) {}

  ngOnInit() {
    this.store.dispatch(SimulationSetupPageActions.opened());
    this.simulationConfigSelectorService.simulationConfigConnections$.subscribe((res: any) => {
      this.configConnections = res;
    });
  }

  svgLoaded() {
    this.store.dispatch(SimulationSetupPageActions.svgLoaded());
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  processConfig() {
    this.store.dispatch(SimulationSetupAPIActions.createConfig());
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
        const unit_meta = { unit_type, unit_id };
        unit_meta ?? new Error('Missing config for given unit');
        if (contextMenu) {
          this.openDialog(title, desc, element, unit_meta, 'context-menu');
          break;
        }
        this.openDialog(title, desc, element, unit_meta);
        break;
      }
    }
  }

  private openDialog(title: any, desc: any, element: any, unit_meta: any, dialog_type = 'dialog') {
    let dialogComponent: any = (dialog_type === 'context-menu') ? 
      SimulationContextMenuDialogComponent : 
      SimulationSetupDialogComponent;

    const ref = this.dialog.open(dialogComponent, {
      data: { title, desc, element, unit_meta },
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
    this.store.dispatch(SimulationDefaultConfigActions.updateConfig({unit_type: type, unit_id: id, config: params}));
  }

  private applyElementSettings(result: { element: any, state: boolean, params: any; }) {
    const matchingConnections = this.disableConnectionsByInOutIds(result.params.ID);
    this.svgTools.findConnecstionLinesById([result.params.ID, ...matchingConnections], result.state, this.svgLayout);

    const title = result.element.getElementsByTagName('title')[0]?.innerHTML;
    const siblings = this.svgTools.findAllElementsContainingTitle(title, this.svgLayout.nativeElement);

    for (let i = 0; i < siblings.snapshotLength; i++) {
      const item = siblings.snapshotItem(i) as HTMLElement;
      result.state ? item.classList.remove('inactive') : item.classList.add('inactive');
    }
  }

  private disableConnectionsByInOutIds(id: string): string[] {
    const connections = Object.keys(this.configConnections);
    let matching_IDs: string[] = [];
    connections.map(key => {
      if (this.configConnections[key]['in'] === id || this.configConnections[key]['out'] === id) {
        matching_IDs.push(this.configConnections[key]['ID']);
      }
    });

    return [...matching_IDs];
  }

}
