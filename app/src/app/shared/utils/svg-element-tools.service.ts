import { DOCUMENT } from '@angular/common';
import { ElementRef, Inject, Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SvgElementToolsService {

  constructor(
    @Inject(DOCUMENT) private document: Document,
  ) { }

  getConfigurableElements(svgLayout: ElementRef, configurableShapeNames: string[]): (Node | null)[] | undefined {
    if (!svgLayout) return;
    let svg = svgLayout.nativeElement;
    return this.getElementsFromShapeNames(configurableShapeNames, svg);
  }

  getConfigurableShapeNames(config: any) {
    const { col = {}, con = {}, ...configurables } = { ...config };

    return Object.keys(configurables).map(
      keyL1 => Object.keys(configurables[keyL1])
        .map(keyL2 => configurables[keyL1][keyL2].ID)
    ).reduce((acc, curVal) => acc.concat(curVal), []);
  }

  findElementByName(name: string, context: any): (Node | null) {
    return this.document.evaluate(`//*[text()="${name}"]/..`, context, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
  }

  findAllElementsContainingTitle(title: string, context: any): XPathResult {
    return this.document.evaluate(`//*[contains(text(),"${title}")]/..`, context, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
  }

  findConnecstionLinesById(ids: string[], state: boolean, svgLayout: ElementRef) {
    ids.map(id => {
      const item: HTMLElement | null = this.findElementByName(id, svgLayout.nativeElement) as HTMLElement;
      state ? item?.classList.remove('inactive') : item?.classList.add('inactive');
    });
  }

  private getElementsFromShapeNames(names: string[], context: any): (Node | null)[] {
    return names.map(name => {
      return this.findElementByName(name, context);
    });
  }

}
