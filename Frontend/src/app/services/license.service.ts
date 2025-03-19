import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const API_URL = 'http://localhost:3000/api';

export interface License {
  _id: string;
  systemId: string;
  licenseKey: string;
  duration: number;
  startDate: Date;
  expiryDate: Date;
  status: 'active' | 'expired' | 'revoked';
}

export interface ActivationStatus {
  isActivated: boolean;
  systemId?: string;
}

@Injectable({
  providedIn: 'root'
})
export class LicenseService {
  constructor(private http: HttpClient) {}

  generateLicense(systemId: string, duration: number): Observable<License> {
    return this.http.post<License>(`${API_URL}/licenses/generate`, {
      systemId,
      duration
    });
  }

  validateLicense(licenseKey: string, uniqueId: string): Observable<any> {
    return this.http.post<any>(`${API_URL}/licenses/validate`, {
      licenseKey,
      uniqueId
    });
  }

  checkActivation(licenseKey: string): Observable<ActivationStatus> {
    return this.http.post<ActivationStatus>(`${API_URL}/licenses/check-activation`, {
      licenseKey
    });
  }

  getAllLicenses(): Observable<License[]> {
    return this.http.get<License[]>(`${API_URL}/licenses`);
  }
} 