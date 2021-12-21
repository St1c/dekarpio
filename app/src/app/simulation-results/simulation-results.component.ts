import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-simulation-results',
  templateUrl: './simulation-results.component.html',
  styleUrls: ['./simulation-results.component.scss']
})
export class SimulationResultsComponent implements OnInit {

  constructor() {
    console.log('results constructed');
  }

  ngOnInit(): void {
  }

}
