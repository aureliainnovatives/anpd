import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SystemService, System, SystemInfo } from '../../services/system.service';
import { Clipboard } from '@angular/cdk/clipboard';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';

interface License {
  _id: string;
  licenseKey: string;
  systemId: string;
  duration: number;
  startDate: Date;
  expiryDate: Date;
  status: string;
  createdAt: Date;
}

@Component({
  selector: 'app-system-list',
  templateUrl: './system-list.component.html',
  styleUrls: ['./system-list.component.scss']
})
export class SystemListComponent implements OnInit {
  displayedColumns: string[] = [
    'index',
    'uniqueId',
    'status',
    'systemInfo',
    'licenseKey',
    'duration',
    'lastActivated',
    'createdAt',
    'actions'
  ];
  
  dataSource!: MatTableDataSource<System>;
  loading = true;
  
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private router: Router,
    private systemService: SystemService,
    private snackBar: MatSnackBar,
    private clipboard: Clipboard
  ) {}

  ngOnInit(): void {
    this.loadSystems();
  }

  loadSystems(): void {
    this.loading = true;
    this.systemService.getAllSystems().subscribe({
      next: (systems) => {
        this.dataSource = new MatTableDataSource(systems);
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading systems:', error);
        this.snackBar.open('Error loading systems', 'Close', { duration: 3000 });
        this.loading = false;
      }
    });
  }

  generateLicense(systemId: string): void {
    this.router.navigate(['/generate-license', systemId]);
  }

  copyLicenseKey(licenseKey: string): void {
    if (licenseKey) {
      this.clipboard.copy(licenseKey);
      this.snackBar.open('License key copied to clipboard', 'Close', { 
        duration: 2000,
        horizontalPosition: 'center',
        verticalPosition: 'bottom'
      });
    }
  }
} 