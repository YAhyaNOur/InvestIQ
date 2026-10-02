import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard-ceo',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard-ceo.html',
  styleUrl: './dashboard-ceo.css'
})
export class DashboardCeo implements OnInit, AfterViewInit {

  @ViewChild('metricsChart') metricsRef!: ElementRef;
  @ViewChild('benchmarkChart') benchmarkRef!: ElementRef;
  @ViewChild('profileChart') profileRef!: ElementRef;

  company: any = null;
  loading = true;
  error = '';

  benchmarks: any = {
    Technology: { beta: 1.2, ebitda: 0.25, rev_emp: 500000 },
    Finance: { beta: 0.9, ebitda: 0.30, rev_emp: 800000 },
    Healthcare: { beta: 0.8, ebitda: 0.20, rev_emp: 600000 },
    Energy: { beta: 1.1, ebitda: 0.15, rev_emp: 400000 },
    Education: { beta: 0.7, ebitda: 0.18, rev_emp: 350000 },
  };

  today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) { }

  ngOnInit() { this.loadCompany(); }
  ngAfterViewInit() { }

  loadCompany() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.loading = false;
      this.cdr.detectChanges();
      return;
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    this.http.get<any>('http://localhost:8000/companies/me', { headers }).subscribe({
      next: (data) => {
        console.log('Company data:', data);
        if (data.error) {
          this.error = 'No company found';
          this.loading = false;
          this.cdr.detectChanges();
          return;
        }
        this.company = data;
        this.loading = false;
        this.cdr.detectChanges();
        setTimeout(() => this.buildCharts(), 300);
      },
      error: (err) => {
        console.error('Error:', err);
        this.loading = false;
        this.error = 'Error loading company';
        this.cdr.detectChanges();
      }
    });
  }

  buildCharts() {
    this.buildMetrics();
    this.buildBenchmark();
    this.buildProfile();
  }

  buildMetrics() {
    const canvas = this.metricsRef?.nativeElement;
    if (!canvas || !this.company) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();
    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: ['Beta', 'EBITDA Margin', 'Rev/Employee (k$)', 'Net Debt (k$)'],
        datasets: [{
          label: 'Your Company',
          data: [
            this.company.beta,
            this.company.ebitda_margins * 100,
            this.company.revenue_per_employee / 1000,
            this.company.net_debt / 1000
          ],
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
          borderRadius: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11 } } },
          y: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } }
        }
      }
    });
  }

  buildBenchmark() {
    const canvas = this.benchmarkRef?.nativeElement;
    if (!canvas || !this.company) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();
    const sector = this.company.sector;
    const bench = this.benchmarks[sector] || this.benchmarks['Technology'];
    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: ['Beta', 'EBITDA (%)', 'Rev/Emp (k$)'],
        datasets: [
          {
            label: 'Your Company',
            data: [this.company.beta, this.company.ebitda_margins * 100, this.company.revenue_per_employee / 1000],
            backgroundColor: 'rgba(59,130,246,0.85)',
            borderRadius: 6,
          },
          {
            label: `${sector} Average`,
            data: [bench.beta, bench.ebitda * 100, bench.rev_emp / 1000],
            backgroundColor: 'rgba(203,213,225,0.85)',
            borderRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { color: '#64748b', font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b' } },
          y: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } }
        }
      }
    });
  }

  buildProfile() {
    const canvas = this.profileRef?.nativeElement;
    if (!canvas || !this.company) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();
    const sector = this.company.sector;
    const bench = this.benchmarks[sector] || this.benchmarks['Technology'];
    const betaScore = bench.beta > 0 ? Math.min((bench.beta / this.company.beta) * 100, 150) : 100;
    const ebitdaScore = bench.ebitda > 0 ? Math.min((this.company.ebitda_margins / bench.ebitda) * 100, 150) : 100;
    const revScore = bench.rev_emp > 0 ? Math.min((this.company.revenue_per_employee / bench.rev_emp) * 100, 150) : 100;
    const debtScore = this.company.net_debt <= 0 ? 120 : Math.min((1 / (this.company.net_debt / 1000000 + 1)) * 100, 100);
    new Chart(canvas, {
      type: 'radar',
      data: {
        labels: ['Stability', 'Profitability', 'Productivity', 'Debt Health'],
        datasets: [{
          label: 'Your Profile',
          data: [betaScore, ebitdaScore, revScore, debtScore],
          backgroundColor: 'rgba(102,126,234,0.15)',
          borderColor: '#667eea',
          pointBackgroundColor: '#667eea',
          pointRadius: 5,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          r: {
            min: 0, max: 150,
            ticks: { color: '#94a3b8', font: { size: 10 }, stepSize: 50 },
            grid: { color: '#f1f5f9' },
            pointLabels: { color: '#64748b', font: { size: 11 } }
          }
        }
      }
    });
  }

  getRiskLevel(): string {
    if (!this.company) return 'N/A';
    if (this.company.beta > 1.3) return 'High Risk';
    if (this.company.beta > 0.8) return 'Medium Risk';
    return 'Low Risk';
  }

  getRiskClass(): string {
    if (!this.company) return '';
    if (this.company.beta > 1.3) return 'risk-high';
    if (this.company.beta > 0.8) return 'risk-medium';
    return 'risk-low';
  }

  getAttractivenessScore(): number {
    if (!this.company) return 0;
    let score = 0;
    if (this.company.ebitda_margins > 0.2) score += 30;
    else if (this.company.ebitda_margins > 0.1) score += 15;
    if (this.company.beta < 1.0) score += 25;
    else if (this.company.beta < 1.5) score += 10;
    if (this.company.revenue_per_employee > 500000) score += 25;
    else if (this.company.revenue_per_employee > 200000) score += 12;
    if (this.company.net_debt < 0) score += 20;
    else if (this.company.net_debt < 500000) score += 10;
    return score;
  }
}