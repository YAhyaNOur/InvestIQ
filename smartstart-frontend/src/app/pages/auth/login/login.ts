import { apiErrorMessage } from '../../../core/utils/api-error';
import { AfterViewInit, Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { TokenService } from '../../../core/services/token.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login implements OnInit, AfterViewInit {
  email = '';
  password = '';
  role: 'STARTUPER' | 'INVESTOR' | '' = '';
  isLoading = false;
  errorMessage = '';

  private authService = inject(AuthService);
  private tokenService = inject(TokenService);
  private router = inject(Router);
  private http = inject(HttpClient);

  ngOnInit(): void { }
  ngAfterViewInit(): void {
    this.initParticles();
    this.initRingHover();
  }

  onSubmit(): void {
    if (!this.email || !this.password) {
      this.errorMessage = 'Veuillez remplir tous les champs';
      return;
    }
    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login({
      email: this.email,
      password: this.password,
      ...(this.role ? { role: this.role } : {})
    }).subscribe({
      next: (res: any) => {
        this.isLoading = false;
        this.tokenService.setTokens(res.access_token, res.refresh_token);

        const payload = JSON.parse(atob(res.access_token.split('.')[1]));
        const roles: string[] = payload.roles || [];
        const userId = payload.sub;

        localStorage.setItem('roles', JSON.stringify(roles));
        localStorage.setItem('userId', userId);
        localStorage.setItem('access_token', res.access_token);

        // ── Redirection selon rôle ──
        if (roles.includes('INVESTOR')) {
          this.checkOnboardingStatus(res.access_token);
        } else {
          this.checkCompanyStatus(res.access_token);
        }
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = apiErrorMessage(err, 'Échec de connexion. Vérifiez vos identifiants.');
      }
    });
  }

  private checkOnboardingStatus(token: string): void {
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    this.http.get<any>('http://localhost:8000/onboarding/status', { headers }).subscribe({
      next: (status) => {
        if (status.completed) {
          this.router.navigate(['/dashboard/investor']);
        } else {
          this.router.navigate(['/investor/onboarding']);
        }
      },
      error: () => this.router.navigate(['/investor/onboarding'])
    });
  }

  private checkCompanyStatus(token: string): void {
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    this.http.get<any>('http://localhost:8000/companies/me', { headers }).subscribe({
      next: (company) => {
        if (company && !company.error) {
          this.router.navigate(['/dashboard/startuper/ceo']);
        } else {
          this.router.navigate(['/startuper/onboarding']);
        }
      },
      error: () => this.router.navigate(['/startuper/onboarding'])
    });
  }

  private initParticles(): void { }
  private initRingHover(): void { }
}