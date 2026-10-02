import { Component } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-company',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './company.component.html',
  styleUrls: ['./company.component.css']
})
export class CompanyComponent {
  loading = false;
  error = '';
  submitted = false;

  company = {
    name: '',
    sector: '',
    industry_group: '',
    region_std: '',
    beta: null as number | null,
    ebitda_margins: null as number | null,
    revenue_per_employee: null as number | null,
    net_debt: null as number | null,
    // ── NOUVEAUX ──
    revenue_growth: null as number | null,
    current_ratio: null as number | null,
    debt_to_equity: null as number | null,
  };

  constructor(private http: HttpClient, private router: Router) { }

  isValid(): boolean {
    return !!(
      this.company.name &&
      this.company.sector &&
      this.company.industry_group &&
      this.company.region_std &&
      this.company.beta !== null &&
      this.company.ebitda_margins !== null &&
      this.company.revenue_per_employee !== null &&
      this.company.net_debt !== null
      // revenue_growth, current_ratio, debt_to_equity sont optionnels
    );
  }

  submit() {
    this.submitted = true;

    if (!this.isValid()) {
      this.error = 'Please fill in all required fields.';
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      this.error = 'Session expired. Please login again.';
      this.router.navigate(['/login']);
      return;
    }

    this.loading = true;
    this.error = '';

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    });

    this.http.post('http://localhost:8000/companies/', this.company, { headers })
      .subscribe({
        next: (res: any) => {
          this.loading = false;
          console.log('Company created!', res);
          this.router.navigate(['/dashboard/startuper/ceo']);
        },
        error: (err) => {
          this.loading = false;
          if (err.status === 422) {
            this.error = 'Validation error: Check number fields.';
          } else if (err.status === 401) {
            this.error = 'Session expired. Please login again.';
          } else {
            this.error = err.error?.detail || 'An error occurred.';
          }
        }
      });
  }
}