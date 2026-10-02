import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-company-analysis',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './company-analysis.html',
  styleUrls: ['./company-analysis.css']
})
export class CompanyAnalysisComponent implements OnInit, AfterViewInit {

  @ViewChild('scoresChart') scoresRef!: ElementRef;
  @ViewChild('gaugeChart') gaugeRef!: ElementRef;

  symbol = '';
  result: any = null;
  loading = false;
  error = '';
  searched = false;
  popularSymbols = [
    { symbol: 'HIMS' },   // Hims & Hers Health
    { symbol: 'RELY' },   // Remitly Global
    { symbol: 'TASK' },   // TaskUs
    { symbol: 'MAPS' },   // WM Technology
    { symbol: 'XMTR' },   // Xometry
    { symbol: 'ACMR' },   // ACM Research
  ];
  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) { }

  ngOnInit() { }
  ngAfterViewInit() { }

  analyze() {
    if (!this.symbol.trim()) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    this.loading = true;
    this.error = '';
    this.result = null;
    this.searched = true;

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.post<any>('http://localhost:8000/analyze/company',
      { symbol: this.symbol.toUpperCase() },
      { headers }
    ).subscribe({
      next: (data) => {
        this.result = data;
        this.loading = false;
        this.cdr.detectChanges();
        setTimeout(() => this.buildCharts(), 300);
      },
      // APRÈS
      error: (e) => {
        this.error = e.error?.detail || 'Symbole introuvable. Essayez : HIMS, RELY, TASK, MAPS, XMTR, ACMR';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  quickSearch(sym: string) {
    this.symbol = sym;
    this.analyze();
  }

  buildCharts() {
    this.buildScoresChart();
    this.buildGaugeChart();
  }

  buildScoresChart() {
    const canvas = this.scoresRef?.nativeElement;
    if (!canvas || !this.result) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: ['Growth Score', 'Risk Score', 'Investment Score'],
        datasets: [{
          data: [this.result.growth_score, this.result.risk_score, this.result.investment_score],
          backgroundColor: ['#10b981', '#ef4444', '#3b82f6'],
          borderRadius: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 11 } } },
          y: { min: 0, max: 100, grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } }
        }
      }
    });
  }

  buildGaugeChart() {
    const canvas = this.gaugeRef?.nativeElement;
    if (!canvas || !this.result) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    const score = this.result.investment_score;
    const remaining = 100 - score;

    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['Score', ''],
        datasets: [{
          data: [score, remaining],
          backgroundColor: [this.result.decision_color, '#f1f5f9'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '75%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        }
      }
    });
  }

  getScoreColor(score: number): string {
    if (score > 70) return '#10b981';
    if (score > 50) return '#3b82f6';
    if (score > 30) return '#f59e0b';
    return '#ef4444';
  }

  formatMarketCap(val: number): string {
    if (!val) return 'N/A';
    if (val >= 1e12) return (val / 1e12).toFixed(2) + 'T';
    if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
    if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
    return val.toString();
  }
}