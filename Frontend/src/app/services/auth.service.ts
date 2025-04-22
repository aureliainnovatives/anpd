import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private tokenKey = 'auth_token';
  private userKey = 'user_data';

  constructor(private http: HttpClient) {}

  login(username: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, { username, password })
      .pipe(
        tap((response: any) => {
          if (response.token) {
            localStorage.setItem(this.tokenKey, response.token);
            localStorage.setItem(this.userKey, JSON.stringify({ username }));
          }
        })
      );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  getUserData(): any {
    const userData = localStorage.getItem(this.userKey);
    return userData ? JSON.parse(userData) : null;
  }

  getSessionExpiry(): Date | null {
    const token = this.getToken();
    if (!token) return null;
    
    try {
      const tokenData = JSON.parse(atob(token.split('.')[1]));
      return new Date(tokenData.exp * 1000);
    } catch (e) {
      return null;
    }
  }

  isSessionExpired(): boolean {
    const expiry = this.getSessionExpiry();
    if (!expiry) return true;
    return new Date() > expiry;
  }
} 