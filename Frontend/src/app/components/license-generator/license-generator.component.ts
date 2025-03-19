import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { LicenseService, License } from '../../services/license.service';
import { SystemService } from '../../services/system.service';
import { Clipboard } from '@angular/cdk/clipboard';
import { ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-license-generator',
  templateUrl: './license-generator.component.html',
  styleUrls: ['./license-generator.component.scss']
})
export class LicenseGeneratorComponent implements OnInit {
  licenseForm: FormGroup;
  isLoading = false;
  isGenerating = false;
  systemId: string = '';
  system: any = null;
  generatedLicense: License | null = null;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private snackBar: MatSnackBar,
    private licenseService: LicenseService,
    private systemService: SystemService,
    private clipboard: Clipboard,
    private dialog: MatDialog
  ) {
    this.licenseForm = this.fb.group({
      duration: ['', [Validators.required, Validators.min(1)]]
    });
  }

  ngOnInit(): void {
    this.systemId = this.route.snapshot.params['id'];
    this.loadSystemDetails();
  }

  loadSystemDetails(): void {
    this.isLoading = true;
    this.systemService.getSystemById(this.systemId).subscribe({
      next: (system) => {
        this.system = system;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading system details:', error);
        this.snackBar.open('Error loading system details', 'Close', {
          duration: 3000
        });
        this.router.navigate(['/systems']);
      }
    });
  }

  generateLicense(): void {
    if (this.licenseForm.valid) {
      if (this.system.license?.status === 'active') {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
          data: {
            title: 'Update License Key',
            message: 'This system already has an active license. The existing license key will be replaced with a new one. Do you want to continue?'
          }
        });

        dialogRef.afterClosed().subscribe(result => {
          if (result) {
            this.proceedWithLicenseGeneration();
          }
        });
      } else {
        this.proceedWithLicenseGeneration();
      }
    }
  }

  private proceedWithLicenseGeneration(): void {
    this.isGenerating = true;
    const duration = this.licenseForm.get('duration')?.value;

    this.licenseService.generateLicense(this.systemId, duration).subscribe({
      next: (license) => {
        this.generatedLicense = license;
        this.isGenerating = false;
        if (this.system.license?.status === 'active') {
          this.snackBar.open('License key has been updated successfully.', 'Close', {
            duration: 5000
          });
        }
      },
      error: (error) => {
        console.error('Error generating license:', error);
        this.snackBar.open('Error generating license', 'Close', {
          duration: 3000
        });
        this.isGenerating = false;
      }
    });
  }

  copyLicenseKey(): void {
    if (this.generatedLicense) {
      this.clipboard.copy(this.generatedLicense.licenseKey);
      this.snackBar.open('License key copied to clipboard', 'Close', {
        duration: 2000,
        horizontalPosition: 'center',
        verticalPosition: 'bottom'
      });
    }
  }

  generateNew(): void {
    this.generatedLicense = null;
    this.licenseForm.reset();
  }

  goBack(): void {
    this.router.navigate(['/systems']);
  }

  cancel(): void {
    this.router.navigate(['/systems']);
  }
} 