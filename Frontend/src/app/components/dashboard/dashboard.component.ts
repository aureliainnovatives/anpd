import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { SystemService } from '../../services/system.service';
import { LicenseService } from '../../services/license.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  pendingSystems: number = 0;
  activeLicenses: number = 0;
  expiredLicenses: number = 0;

  constructor(
    private router: Router,
    private systemService: SystemService,
    private licenseService: LicenseService
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    forkJoin({
      pendingSystems: this.systemService.getPendingSystems(),
      licenses: this.licenseService.getAllLicenses()
    }).subscribe({
      next: (data) => {
        this.pendingSystems = data.pendingSystems.length;
        this.activeLicenses = data.licenses.filter(l => l.status === 'active').length;
        this.expiredLicenses = data.licenses.filter(l => l.status === 'expired').length;
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
      }
    });
  }

  navigateToSystems(): void {
    this.router.navigate(['/systems']);
  }
} 