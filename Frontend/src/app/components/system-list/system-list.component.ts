import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SystemService, System, SystemInfo } from '../../services/system.service';
import { Clipboard } from '@angular/cdk/clipboard';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { LicenseService } from '../../services/license.service';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';

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
  renewingLicenseId: string | null = null;
  terminatingLicenseId: string | null = null;
  
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private router: Router,
    private systemService: SystemService,
    private licenseService: LicenseService,
    private snackBar: MatSnackBar,
    private clipboard: Clipboard,
    private dialog: MatDialog
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

  renewLicense(system: System): void {
    const licenseKey = system.license?.licenseKey;
    if (!licenseKey) {
      this.snackBar.open('No license key found for this system', 'Close', {
        duration: 3000
      });
      return;
    }

    if (system.license?.status === 'terminated') {
      this.snackBar.open('Cannot renew a terminated license', 'Close', {
        duration: 3000
      });
      return;
    }

    this.renewingLicenseId = system._id;
    this.licenseService.renewLicense(licenseKey).subscribe({
      next: (response) => {
        this.snackBar.open('License renewed successfully', 'Close', {
          duration: 3000
        });
        this.loadSystems(); // Reload the systems list
      },
      error: (error) => {
        console.error('Error renewing license:', error);
        const errorMessage = error.error?.message || 'Error renewing license';
        this.snackBar.open(errorMessage, 'Close', {
          duration: 3000
        });
      },
      complete: () => {
        this.renewingLicenseId = null;
      }
    });
  }

  terminateLicense(system: System): void {
    const licenseKey = system.license?.licenseKey;
    if (!licenseKey) {
      this.snackBar.open('No license key found for this system', 'Close', {
        duration: 3000
      });
      return;
    }

    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Terminate License',
        message: 'Are you sure you want to terminate this license? This action cannot be undone.'
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.terminatingLicenseId = system._id;
        this.licenseService.terminateLicense(licenseKey).subscribe({
          next: (response) => {
            this.snackBar.open('License terminated successfully', 'Close', {
              duration: 3000
            });
            this.loadSystems(); // Reload the systems list
          },
          error: (error) => {
            console.error('Error terminating license:', error);
            this.snackBar.open('Error terminating license', 'Close', {
              duration: 3000
            });
          },
          complete: () => {
            this.terminatingLicenseId = null;
          }
        });
      }
    });
  }
} 