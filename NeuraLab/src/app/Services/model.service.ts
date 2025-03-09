import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ModelService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  getAvailableModels(): Observable<any> {
    return this.http.get(`${this.apiUrl}/models`);
  }

  uploadDataset(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/upload-dataset`, formData);
  }

  startTraining(config: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/train`, config);
  }
} 