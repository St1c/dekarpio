import { Directive, ElementRef, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges } from '@angular/core';
import { Simulation } from 'src/app/core/simulations/simulations.service';
import { SvgElementToolsService } from '../../utils/svg-element-tools.service';

@Directive({
  selector: '[appSvgElementsRightClickListener]',
  standalone: true
})
export class SvgElementsRightClickListenerDirective implements OnChanges, OnDestroy {

  @Input() configurableShapes!: string[] | null;

  @Output('appSvgElementsRightClickListenerChange') svgClicked = new EventEmitter();

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
      el?.addEventListener('contextmenu', this.svgClickedEmit.bind(this), true);
    });
  }

  private unbindClickListenersToConfigurableElements() {
    this.elements?.map((el: Node | null) => {
      el?.removeEventListener('contextmenu', this.svgClickedEmit.bind(this), true);
    });
  }

  private svgClickedEmit(event: any) {
    event.preventDefault();
    event.stopPropagation();
    this.svgClicked.next(event);
  }
}