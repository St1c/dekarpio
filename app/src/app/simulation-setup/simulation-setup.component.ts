import { DOCUMENT } from '@angular/common';
import { Component, ElementRef, Inject, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';

import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

export interface DialogData {
  title: any;
  desc: any;
  element: any;
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

  private shapeNames = [
    'Erdgas',
    'Wasserstoff',
    'Feste Biomasse',
    'Geothermie (120°C)',
    'Kessel BM',
    'E- Kessel',
    'K4',
    'K5',
    'K6',
    'Gasturbine (GT) + AHK',
    'Prozess-Erdgas-Bedarf',
    'Prozess-Dampf-Bedarf PM1+2 (130°C) 1,5 MW'
  ];

  private shape_titles = [
    'simple_ex',
    'fuel_gas1',
    'fuel_gas2',
    'fuel_power',
    'conversion_boiler1',
    'conversion_boiler2',
    'storage_power',
    'collector_steam',
    'collector_power',
    'demand_steam',
    'demand_power',
    // 'fuel_gas1_2_boiler',
    // 'fuel_gas2_2_boiler',
    // 'fuel_power_2_boiler2',
    // 'fuel_power_2_collector_power',
    // 'collector_power_2_demand_power',
    // 'collector_steam1_2_demand_steam',
    'boiler_collector_steam_1',
    'boiler_2_collector_steam_1',
    // 'storage_power_2_collector_power',
  ];
  private elements: (Node | null)[] = [];

  constructor(
    fb: FormBuilder,
    public dialog: MatDialog,
    @Inject(DOCUMENT) private document: Document
  ) {
    this.options = fb.group({
      hideRequired: this.hideRequiredControl,
      floatLabel: this.floatLabelControl,
    });
  }

  svgLoaded() {
    if (!this.svgLayout) return;

    let svg = this.svgLayout.nativeElement;
    this.elements = this.getElementsFromShapeNames(this.shape_titles, svg);
    this.elements.map((el: Node | null) => {
      el?.addEventListener('mouseenter', this.elementEnter, true);
      el?.addEventListener('mouseleave', this.elementLeave, true);
    });

    // console.log(svg.querySelector('#shape56-70'));
    // const res = this.document.evaluate(`//*[text()="${this.shape_titles[3]}"]/..`, svg, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    // console.log(res);
  }

  ngOnDestroy() {
    this.elements.map((el: Node | null) => {
      el?.removeEventListener('mouseenter', this.elementEnter, true);
      el?.removeEventListener('mouseleave', this.elementLeave, true);
    });
  }

  svgClicked(target: any) {
    console.log(target);

    for (const element of target.path) {
      if (element.id) {
        // console.log(element.id);
        const title = element.querySelector('title');
        const desc = element.querySelector('desc');
        this.clickedSvgElement = desc?.innerHTML;
        this.openDialog(title, desc, element);
        break;
      }
    }

  }

  private elementEnter(event: any) {
    event.target.classList.add('entered');
  }

  private elementLeave(event: any) {
    event.target.classList.remove('entered');
  }

  private openDialog(title: any, desc: any, element: any) {
    const ref = this.dialog.open(SvgElementDialogComponent, {
      data: { title, desc, element },
    });

    ref.afterClosed().subscribe(result => {
      if (result) this.applyElementSettings(result);
    });
  }

  private applyElementSettings(result: { element: any, state: boolean; }) {
    const title = result.element.getElementsByTagName('title')[0]?.innerHTML;

    const siblings = this.findAllElementsContainingTitle(title, this.svgLayout.nativeElement);

    for (let i = 0; i < siblings.snapshotLength; i++) {
      const item = siblings.snapshotItem(i) as HTMLElement;

      console.log(item);

      if (result.state) {
        item.classList.remove('inactive');
      } else {
        item.classList.add('inactive');
      }
    }

  }

  private getElementsFromShapeNames(names: string[], context: any): (Node | null)[] {
    return names.map(name => {
      return this.document.evaluate(`//*[text()="${name}"]/..`, context, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    });
  }

  private findAllElementsContainingTitle(title: string, context: any): XPathResult {
    return this.document.evaluate(`//*[contains(text(),"${title}")]/..`, context, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
  }
}

@Component({
  selector: 'svg-element-dialog',
  templateUrl: 'svg-element-dialog.html',
})
export class SvgElementDialogComponent {

  title = '';
  desc = '';
  element: any;

  elementUsed = new FormControl(true);
  range = new FormGroup({
    start: new FormControl(),
    end: new FormControl(),
  });

  constructor(
    public dialogRef: MatDialogRef<SvgElementDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {
    this.title = data.title?.innerHTML || '';
    this.desc = data.desc?.innerHTML || '';
    this.element = data.element;

    this.getElementState(this.element);
  }

  closeDialog() {
    this.dialogRef.close({ element: this.element, state: this.elementUsed.value });
  }

  private getElementState(element: any) {
    element.classList.contains('inactive') ? this.elementUsed.setValue(false) : this.elementUsed.setValue(true);
  }
}
