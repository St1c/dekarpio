import { Component, ElementRef, ViewChild } from '@angular/core';
import { AsyncPipe, CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatMenuModule, MatMenuTrigger } from '@angular/material/menu';

import { Observable, Subscription } from 'rxjs';
import { Store } from '@ngrx/store';
import { InlineSVGModule } from 'ng-inline-svg';

import { SimulationSetupDialogComponent } from '../simulation-setup-dialog/simulation-setup-dialog.component';
import {
  SvgElementsHoverListenerDirective
} from '../shared/ui/svg-elements-hover-listener/svg-elements-hover-listener.directive';
import {
  SimulationDefaultConfigActions,
  SimulationSetupAPIActions,
  SimulationSetupPageActions
} from '../shared/data-access/store/simulation-config';
import {
  SimulationConfigSelectorService
} from '../shared/data-access/store/simulation-config/simulation-config.selectors';
import {
  SvgElementsClickListenerDirective
} from '../shared/ui/svg-elements-click-listener/svg-elements-click-listener.directive';
import {
  SimulationContextMenuDialogComponent
} from '../simulation-context-menu-dialog/simulation-context-menu-dialog.component';
import {
  SvgElementsRightClickListenerDirective
} from '../shared/ui/svg-elements-right-click-listener/svg-elements-right-click-listener.directive';
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatSelectModule } from "@angular/material/select";
import { MatIconModule } from "@angular/material/icon";

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
    CommonModule,
    InlineSVGModule,
    ReactiveFormsModule,

    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatMenuModule,
    MatSelectModule,

    SvgElementsHoverListenerDirective,
    SvgElementsClickListenerDirective,
    SvgElementsRightClickListenerDirective
  ],
})
export class SimulationSetupComponent {

  @ViewChild('layout', { static: false }) svgLayout!: ElementRef;
  @ViewChild(MatMenuTrigger, { static: true }) matMenuTrigger!: MatMenuTrigger;

  clickedSvgElement: string = '';
  configurableShapes$: Observable<string[]> = this.simulationConfigSelectorService.configurableShapeNames$;
  simulationConfigLoaded$: Observable<boolean> = this.simulationConfigSelectorService.simulationConfigLoaded$;

  selectedConfig: FormControl<string | null> = new FormControl<string>('latest');
  menuTopLeftPosition = { x: '0', y: '0' };

  private subs = new Subscription();

  constructor(
    public dialog: MatDialog,
    private store: Store<{ simulationConfig: any; }>,
    private simulationConfigSelectorService: SimulationConfigSelectorService
  ) {
    this.selectedConfig.valueChanges
      .subscribe((value: string | null) => {
        if (value === null) return;
        this.store.dispatch(SimulationSetupPageActions.setActiveConfig({ id: value }));
        this.store.dispatch(SimulationSetupPageActions.svgUpdateOnConfigChange({ svgElement: this.svgLayout }));
      });
  }

  ngOnInit() {
    this.store.dispatch(SimulationSetupPageActions.opened());
  }

  svgLoaded() {
    this.store.dispatch(SimulationSetupPageActions.svgLoaded());
    this.store.dispatch(SimulationSetupPageActions.svgUpdateOnConfigChange({ svgElement: this.svgLayout }));
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
          // this.openDialog(title, desc, element, unit_meta, 'context-menu');
          this.onRightClick(event, unit_type, unit_id);
          break;
        }
        this.openDialog(title, desc, element, unit_meta);
        break;
      }
    }
  }

  enable(unit_type:string, unit_id: string) {
    this.store.dispatch(SimulationDefaultConfigActions.enableConfigurableShape({ unit_type, unit_id}));
    this.store.dispatch(SimulationSetupPageActions.svgUpdateOnConfigChange({ svgElement: this.svgLayout }));
  }

  disable(unit_type:string, unit_id: string) {
    this.store.dispatch(SimulationDefaultConfigActions.disableConfigurableShape({ unit_type, unit_id}));
    this.store.dispatch(SimulationSetupPageActions.svgUpdateOnConfigChange({ svgElement: this.svgLayout }));
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
        this.store.dispatch(SimulationSetupPageActions.svgUpdateOnConfigChange({ svgElement: this.svgLayout }));
      }
    }));
  }

  private updateConfig(result: any) {
    const params_id = result.ID;
    let [type, id] = params_id.split('_');
    const { unit_type = '', unit_id = '', ...params } = { ...result };
    this.store.dispatch(SimulationDefaultConfigActions.updateConfig({ unit_type: type, unit_id: id, config: params }));
  }

  /** 
   * Method called when the user click with the right button 
   * @param event MouseEvent, it contains the coordinates 
   * @param item Our data contained in the row of the table 
   */
  private onRightClick(event: MouseEvent, unit_type: string, unit_id: string) {

    // we record the mouse position in our object 
    this.menuTopLeftPosition.x = event.clientX + 'px';
    this.menuTopLeftPosition.y = event.clientY + 'px';

    // we open the menu 
    // we pass to the menu the information about our object 
    this.matMenuTrigger.menuData = { unit_type, unit_id };

    // we open the menu 
    this.matMenuTrigger.openMenu();

  }
}
