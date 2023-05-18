import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatTableModule } from '@angular/material/table';

import { ConfigsManagementSelectorsService } from '../shared/data-access/store/config-management/config-management.selectors';
import {ConfigsManagementActions, ConfigsManagementState} from '../shared/data-access/store/config-management/';
import { SimulationValidityPipe } from '../shared/ui/simulationValidity/simulation-validity.pipe';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
// import {MatPaginator} from '@angular/material/paginator';
import { Store } from '@ngrx/store';

@Component({
  selector: 'app-configs-management',
  standalone: true,
  imports: [
    CommonModule,

    MatButtonModule,
    MatIconModule,
    MatTableModule,

    SimulationValidityPipe
  ],
  templateUrl: './configs-management.component.html',
  styleUrls: ['./configs-management.component.scss']
})
export class ConfigsManagementComponent {

  // @ViewChild(MatPaginator) paginator!: MatPaginator;
  // totalItems!: number;
  // pageSize: number = 10;
  // pageSizeOptions: number[] = [5, 10, 25, 100];
  // currentPage: number = 1;

  dataSource = this.configsManagementSelectors.allConfigs$;
  displayedColumns = ['id', 'email', 'settings', 'name', 'created_at', 'updated_at', 'actions'];

  deleteInvoked = 0;

  constructor(
    private configsManagementSelectors: ConfigsManagementSelectorsService,
    private store: Store<ConfigsManagementState>,
  ) { }

  // ngOnInit() {
  //   this.loadPage(this.currentPage);
  // }

  // loadPage(page: number) {
  //   this.yourService.getPaginatedData(page, this.pageSize).subscribe(data => {
  //     this.dataSource = data;
  //     this.totalItems = data.totalItems;
  //     this.currentPage = page;
  //   });
  // }

  // onPageChange(event: PageEvent) {
  //   this.pageSize = event.pageSize;
  //   this.loadPage(event.pageIndex + 1);
  // }

  invokeDelete(id: number) {
    this.deleteInvoked = id;
    console.log('invokeDelete', id);
  }

  confirmDelete(id: number) {
    console.log('confirmDelete', id);
    this.deleteInvoked = 0;
    this.store.dispatch(ConfigsManagementActions.deleteConfig({ id }));
  }

  cancelDelete(id: number) {
    console.log('cancelDelete', id);
    this.deleteInvoked = 0;
  }

}
