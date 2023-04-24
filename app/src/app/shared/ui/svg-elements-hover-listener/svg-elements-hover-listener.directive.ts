import { Directive, ElementRef, Input, OnChanges, OnDestroy, Renderer2, SimpleChanges } from '@angular/core';
import { SvgElementToolsService } from '../../utils/svg-element-tools.service';

@Directive({
  selector: '[appSvgElementsHoverListener]',
  standalone: true
})
export class SvgElementsHoverListenerDirective implements OnChanges, OnDestroy {

  @Input() configurableShapes!: string[] | null;

  private elements: (Node | null)[] | undefined = [];

  constructor(
    private el: ElementRef,
    private svgTools: SvgElementToolsService,
    private renderer: Renderer2,
  ) { }

  ngOnChanges(changes: SimpleChanges) {
    if (this.configurableShapes && this.configurableShapes.length > 1) {
      this.elements = this.svgTools.getConfigurableElements(this.el, this.configurableShapes);
      this.bindHoverListenersToConfigurableElements();
    }
  }

  ngOnDestroy() {
    this.unbindHoverListenersToConfigurableElements();
  }

  private bindHoverListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.addEventListener('mouseenter', this.elementEnter.bind(this), true);
      el?.addEventListener('mouseleave', this.elementLeave.bind(this), true);
    });
  }

  private unbindHoverListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.removeEventListener('mouseenter', this.elementEnter.bind(this), true);
      el?.removeEventListener('mouseleave', this.elementLeave.bind(this), true);
    });
  }

  private elementEnter(event: any) {
    this.renderer.addClass(event.target, 'entered');
  }

  private elementLeave(event: any) {
    this.renderer.removeClass(event.target, 'entered');
  }

}
