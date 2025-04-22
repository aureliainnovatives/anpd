import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { FormControl } from '@angular/forms';

export interface DialogData {
  title: string;
  message: string;
  inputField?: boolean;
  inputValue?: string;
  inputPlaceholder?: string;
}

@Component({
  selector: 'app-confirm-dialog',
  template: `
    <h2 mat-dialog-title>{{ data.title }}</h2>
    <mat-dialog-content>
      <p>{{ data.message }}</p>
      <mat-form-field *ngIf="data.inputField" appearance="outline" class="full-width">
        <mat-label>{{ data.inputPlaceholder || 'Enter value' }}</mat-label>
        <input matInput [formControl]="inputControl" [placeholder]="data.inputPlaceholder || ''">
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="false">Cancel</button>
      <button mat-flat-button color="primary" [mat-dialog-close]="data.inputField ? inputControl.value : true">
        Save
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    :host {
      display: block;
      padding: 16px;
    }
    mat-dialog-content {
      margin: 16px 0;
    }
    mat-dialog-actions {
      margin-bottom: 0;
    }
    .full-width {
      width: 100%;
    }
  `]
})
export class ConfirmDialogComponent {
  inputControl: FormControl;

  constructor(
    public dialogRef: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {
    this.inputControl = new FormControl(this.data.inputValue || '');
  }
} 