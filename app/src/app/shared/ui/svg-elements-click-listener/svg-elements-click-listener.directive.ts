import { Directive, ElementRef, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges } from '@angular/core';
import { SvgElementToolsService } from '../../utils/svg-element-tools.service';

@Directive({
  selector: '[appSvgElementsClickListener]',
  standalone: true
})
export class SvgElementsClickListenerDirective implements OnChanges, OnDestroy {

  @Input() configurableShapes!: string[] | null;

  @Output('appSvgElementsClickListenerChange') svgClicked = new EventEmitter();

  private elements: (Node | null)[] | undefined = [];

  constructor(
    private el: ElementRef,
    private svgTools: SvgElementToolsService
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    if (this.configurableShapes && this.configurableShapes.length > 1 && this.elements?.length === 0) {
      this.elements = this.svgTools.getConfigurableElements(this.el, this.configurableShapes);
      this.bindClickListenersToConfigurableElements();
    }
  }

  ngOnDestroy() {
    this.unbindClickListenersToConfigurableElements();
  }

  private bindClickListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.addEventListener('click', this.svgClickedEmit.bind(this), true);
    });
  }

  private unbindClickListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.removeEventListener('click', this.svgClickedEmit.bind(this), true);
    });
  }

  private svgClickedEmit(event: any) {
    this.svgClicked.next(event);
  }
}