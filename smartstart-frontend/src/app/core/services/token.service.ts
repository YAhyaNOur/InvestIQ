import { Injectable } from '@angular/core';
import { jwtDecode } from 'jwt-decode';
import { JwtPayload } from '../models/JwtPayload';

@Injectable({ providedIn: 'root' })
export class TokenService {
  private readonly ACCESS_KEY = 'access_token';
  private readonly REFRESH_KEY = 'refresh_token';

  setTokens(access: string, refresh: string): void {
    localStorage.setItem(this.ACCESS_KEY, access);
    localStorage.setItem(this.REFRESH_KEY, refresh);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_KEY);
  }

  clearTokens(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
  }

  // Nouvelle méthode : extraire les infos du token
  getUserFromToken(): { userId: number; roles: string[] } | null {
    const token = this.getAccessToken();
    if (!token) return null;
    try {
      const decoded = jwtDecode<JwtPayload>(token);
      return {
        userId: parseInt(decoded.sub, 10),
        roles: decoded.roles || []
      };
    } catch (error) {
      console.error('Invalid token', error);
      return null;
    }
  }
}