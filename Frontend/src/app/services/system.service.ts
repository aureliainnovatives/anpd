import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, map } from 'rxjs';

const API_URL = 'http://localhost:3000/api';

export interface SystemInfo {
  hostname: string;
  platform: string;
  arch: string;
  release: string;
  cpus: string[];
  memory: {
    total: number;
    free: number;
  };
}

export interface License {
  _id: string;
  licenseKey: string;
  systemId: string | { _id: string };
  duration: number;
  startDate: Date;
  expiryDate: Date;
  status: string;
  createdAt: Date;
}

export interface System {
  _id: string;
  uniqueId: string;
  clientName: string;
  systemInfo: SystemInfo;
  status: string;
  createdAt: Date;
  license: License | null;
}

@Injectable({
  providedIn: 'root'
})
export class SystemService {
  private apiUrl = `${API_URL}/systems`;

  constructor(private http: HttpClient) {}

  getAllSystems(): Observable<System[]> {
    return forkJoin({
      systems: this.http.get<System[]>(this.apiUrl),
      licenses: this.http.get<License[]>(`${API_URL}/licenses`)
    }).pipe(
      map(({ systems, licenses }) => {
        return systems.map(system => {
          const license = licenses.find(l => 
            l.systemId && 
            (typeof l.systemId === 'string' ? 
              l.systemId === system._id : 
              (l.systemId as { _id: string })._id === system._id)
          );
          return {
            ...system,
            license: license || null
          };
        });
      })
    );
  }

  getPendingSystems(): Observable<System[]> {
    return this.http.get<System[]>(`${this.apiUrl}/pending`);
  }

  getSystemById(id: string): Observable<System> {
    return forkJoin({
      system: this.http.get<System>(`${this.apiUrl}/${id}`),
      licenses: this.http.get<License[]>(`${API_URL}/licenses`)
    }).pipe(
      map(({ system, licenses }) => {
        const license = licenses.find(l => 
          l.systemId && 
          (typeof l.systemId === 'string' ? 
            l.systemId === system._id : 
            (l.systemId as { _id: string })._id === system._id)
        );
        return {
          ...system,
          license: license || null
        };
      })
    );
  }

  registerSystem(system: { uniqueId: string; systemInfo: SystemInfo }): Observable<System> {
    return this.http.post<System>(this.apiUrl, system);
  }

  updateSystem(id: string, data: Partial<System>): Observable<System> {
    return this.http.patch<System>(`${this.apiUrl}/${id}`, data);
  }
} 