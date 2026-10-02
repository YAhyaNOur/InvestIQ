import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { TokenService } from './token.service';
import { environment } from '../../../environments/environments';
import { User } from '../models/user';
import { LoginRequest } from '../models/loginRequest';
import { TokenResponse } from '../models/TokenResponse';
import { RegisterRequest } from '../models/registerRequest';


@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private tokenService = inject(TokenService);
  private apiUrl = environment.apiUrl;

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor() {
    this.loadUserFromToken(); // au démarrage, si token existe, on restaure l'utilisateur
  }

  private loadUserFromToken(): void {
    const userInfo = this.tokenService.getUserFromToken();
    if (userInfo) {
      
      const user: User = {
        user_id: userInfo.userId,
        username: '',      // pas dans token
        email: '',         // pas dans token
        full_name: null,
        is_active: true,
        roles: userInfo.roles,
        avatar_url: null
      };
      this.currentUserSubject.next(user);
    }
  }

  login(credentials: LoginRequest): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/auth/login`, credentials)
      .pipe(
        tap(res => {
          this.tokenService.setTokens(res.access_token, res.refresh_token);
          // Mettre à jour l'utilisateur courant à partir du token
          this.loadUserFromToken();
        })
      );
  }

register(data: RegisterRequest): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/auth/register`, data);
  }
 

  logout(): void {
    this.tokenService.clearTokens();
    this.currentUserSubject.next(null);
  }
fetchMe(): Observable<User> {
  const token = this.tokenService.getAccessToken();
  if (!token) throw new Error('No token');
  return this.http.get<User>(`${this.apiUrl}/profile`, {
    headers: { Authorization: `Bearer ${token}` }
  }).pipe(
    tap(user => this.currentUserSubject.next(user))
  );
}
  isAuthenticated(): boolean {
    return !!this.tokenService.getAccessToken() ;
  }

  hasRole(role: string): boolean {
    const user = this.currentUserSubject.value;
    return user?.roles?.includes(role) ?? false;
  }
// auth.service.ts
clearCurrentUser(): void {
  this.currentUserSubject.next(null);
}
  // Optionnel : pour récupérer l'ID utilisateur rapidement
  getUserId(): number | null {
    return this.tokenService.getUserFromToken()?.userId ?? null;
  }
  currentUser(): User | null {
  return this.currentUserSubject.value;
}
roles(): string[] {
  return this.currentUserSubject.value?.roles ?? [];
}

isStartuper(): boolean {
  return this.hasRole('STARTUPER');
}

isInvestor(): boolean {
  return this.hasRole('INVESTOR');
}

saveTokens(tokens: TokenResponse): void {
  this.tokenService.setTokens(tokens.access_token, tokens.refresh_token);
  this.loadUserFromToken(); 
}
}