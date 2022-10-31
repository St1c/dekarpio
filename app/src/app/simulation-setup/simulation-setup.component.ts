import { DOCUMENT } from '@angular/common';
import { Component, ElementRef, HostListener, Inject, Renderer2, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';

import { MatDialog } from '@angular/material/dialog';
import { combineLatest, Subject } from 'rxjs';
import { ConfigProvider } from '../core/config.provider';
import { SimulationSetupDialogComponent } from '../simulation-setup-dialog/simulation-setup-dialog.component';

export interface DialogData {
  title: any;
  desc: any;
  element: any;
  config: any;
}

@Component({
  selector: 'app-simulation-setup',
  templateUrl: './simulation-setup.component.html',
  styleUrls: ['./simulation-setup.component.scss']
})
export class SimulationSetupComponent {

  @ViewChild('layout', { static: false }) svgLayout!: ElementRef;

  clickedSvgElement: string = '';
  options: FormGroup;
  hideRequiredControl = new FormControl(false);
  floatLabelControl = new FormControl('auto');

  private configurableShapeNames: (string[]) = [];
  private elements: (Node | null)[] | undefined = [];
  private config: any;
  private svgLoaded$ = new Subject();

  constructor(
    fb: FormBuilder,
    public dialog: MatDialog,
    private renderer: Renderer2,
    private configService: ConfigProvider,
    @Inject(DOCUMENT) private document: Document,
  ) {
    this.options = fb.group({
      hideRequired: this.hideRequiredControl,
      floatLabel: this.floatLabelControl,
    });
  }

  ngOnInit() {
    combineLatest([
      this.configService.getConfigFromAssets(),
      this.svgLoaded$.asObservable()
    ]).subscribe(([config, svgLoaded]) => {
      this.config = config;
      this.configurableShapeNames = this.getConfigurableShapeNames(config);
      this.elements = this.getConfigurableElements();
      this.bindHoverListenersToConfigurableElements();
      this.bindClickListenersToConfigurableElements();
    });
  }

  svgLoaded() {
    this.svgLoaded$.next(true);
  }

  ngOnDestroy() {
    this.elements?.map((el: Node | null) => {
      el?.removeEventListener('click', this.elementEnter.bind(this), true);
      el?.removeEventListener('mouseenter', this.elementEnter.bind(this), true);
      el?.removeEventListener('mouseleave', this.svgClicked.bind(this), true);
    });
  }

  private getConfigurableShapeNames(config: any) {
    const {col = {}, con = {}, ...configurables} = { ...config };

    return Object.keys(configurables).map(
      keyL1 => Object.keys(configurables[keyL1])
        .map(keyL2 => configurables[keyL1][keyL2].ID)
      ).reduce((acc, curVal) => acc.concat(curVal), []);
  }

  private getConfigurableElements(): (Node | null)[] | undefined {
    if (!this.svgLayout) return;
    let svg = this.svgLayout.nativeElement;
    return this.getElementsFromShapeNames(this.configurableShapeNames, svg);
  }

  private bindClickListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.addEventListener('click', this.svgClicked.bind(this), true);
    });
  }

  private bindHoverListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.addEventListener('mouseenter', this.elementEnter.bind(this), true);
      el?.addEventListener('mouseleave', this.elementLeave.bind(this), true);
    });
  }

  private svgClicked(target: any) {
    for (const element of target.path) {
      if (element.id) {
        const title = element.querySelector('title');
        const desc = element.querySelector('desc');

        if (!title) return; // @TODO: Probably not needed anymore since clickable elements come from json config

        this.clickedSvgElement = desc?.innerHTML;

        let unit_type, unit_id, rest;
        [unit_type, unit_id, ...rest] = title?.innerHTML?.split('_');
        const unit_config = { unit_type, unit_id, ...this.config[unit_type][unit_id] };

        unit_config ?? new Error('Missing config for given unit');
        this.openDialog(title, desc, element, unit_config);
        break;
      }
    }
  }

  private elementEnter(event: any) {
    this.renderer.addClass(event.target, 'entered');
  }

  private elementLeave(event: any) {
    this.renderer.removeClass(event.target, 'entered');
  }

  private openDialog(title: any, desc: any, element: any, config:  any) {
    const ref = this.dialog.open(SimulationSetupDialogComponent, {
      data: { title, desc, element, config },
    });

    ref.afterClosed().subscribe(result => {
      if (result) {
        this.updateConfig(result);
        this.applyElementSettings(result);
      };
    });
  }

  private updateConfig(result: { element: any, state: boolean, params: any }) {
    const params_id = result.params.ID;
    let [type, id, ...rest] = params_id.split('_');
    const { unit_type = '', unit_id= '', ...params } = {...result.params};
    this.config[type][id] = { ... params };
  }

  private applyElementSettings(result: { element: any, state: boolean, params: any }) {
    const matchingConnections = this.disableConnectionsByInOutIds(result.params.ID);
    this.findConnecstionLinesById([result.params.ID, ...matchingConnections], result.state);

    const title = result.element.getElementsByTagName('title')[0]?.innerHTML;
    const siblings = this.findAllElementsContainingTitle(title, this.svgLayout.nativeElement);

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
      const item: HTMLElement | null = this.findElementByName(id, this.svgLayout.nativeElement) as HTMLElement;
      state ? item?.classList.remove('inactive') : item?.classList.add('inactive');
    });
  }

  private getElementsFromShapeNames(names: string[], context: any): (Node | null)[] {
    return names.map(name => {
      return this.findElementByName(name, context);
    });
  }

  private findElementByName(name: string, context: any): (Node | null) {
    return this.document.evaluate(`//*[text()="${name}"]/..`, context, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
  }

  private findAllElementsContainingTitle(title: string, context: any): XPathResult {
    return this.document.evaluate(`//*[contains(text(),"${title}")]/..`, context, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
  }
}
