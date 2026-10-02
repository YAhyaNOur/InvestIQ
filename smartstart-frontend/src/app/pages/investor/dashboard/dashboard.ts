import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-investor-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class Dashboard implements OnInit, AfterViewInit {

  @ViewChild('riskChart') riskChartRef!: ElementRef;
  @ViewChild('sectorChart') sectorChartRef!: ElementRef;

  recommendations: any[] = [];
  loading = true;
  filter = 'ALL';
  selectedId: number | null = null;

  today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.loadRecommendations();
  }

  ngAfterViewInit() { }

  // ── CHARGER LES RECOMMANDATIONS ─────────────────────────────────────────
  loadRecommendations() {
    this.loading = true;
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('userId') || this.getUserId(token);

    if (!token || !userId) {
      this.loading = false;
      return;
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.get<any>(`http://localhost:8000/data/recommend/${userId}`, { headers })
      .subscribe({
        next: (res) => {
          if (res && !res.error) {
            const recs = res.recommendations ?? [];
            this.recommendations = this.mapRecs(recs);
          }
          this.loading = false;
          this.cdr.detectChanges();

          this.loadMyInterests();

          setTimeout(() => this.buildCharts(), 200);
        },
        error: () => {
          this.loading = false;
          this.cdr.detectChanges();
        }
      });
  }

  // ── CHARGER LES INTÉRÊTS DÉJÀ SAUVEGARDÉS ──────────────────────────────

  loadMyInterests() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.get<any>('http://localhost:8000/interest/my-interests', { headers })
      .subscribe({
        next: (res) => {
          const ids: number[] = res.interested_company_ids ?? [];
          this.recommendations = this.recommendations
            .map(r => ({
              ...r,
              isInterested: ids.includes(Number(r.company_id))
            }))

          this.cdr.detectChanges();
        },
        error: () => { }
      });
  }

  mapRecs(data: any[]): any[] {
    if (!Array.isArray(data)) return [];

    return data.map(r => ({
      company_id: r.company_id ?? r.id,
      name: r.name ?? 'Unknown',
      contact_email: r.contact_email ?? '',  // ← email du owner
      score: Number(r.final_score ?? r.score ?? 0),
      ml_score: Number(r.ml_score ?? 0),
      business_score: Number(r.business_score ?? r.business_score_final ?? 0),
      sector: r.Sector ?? r.sector ?? 'N/A',
      region: r.Region_std ?? r.region_std ?? 'N/A',
      beta: Number(r.Beta ?? r.beta ?? 0),
      ebitda: Number(r['EBITDA Margins'] ?? r.ebitda_margins ?? 0),
      decision: r.decision ?? 'N/A',
      isInterested: false
    })).sort((a, b) => b.score - a.score);
  }

  // ── MARQUER COMME INTÉRESSÉ ─────────────────────────────────────────────
  markInterested(companyId: number, index: number) {
    const token = localStorage.getItem('access_token');
    if (!token || !companyId) return;

    if (this.recommendations[index].isInterested) return;

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.post(`http://localhost:8000/interest/${companyId}`, {}, { headers })
      .subscribe({
        next: (res: any) => {
          this.recommendations[index].isInterested = true;
          this.cdr.detectChanges();

          if (res.status === 'already_analyzed') {
            alert(
              `✓ Already analyzed — ${res.company_name}\n` +
              `Growth: ${res.growth_score}% | Risk: ${res.risk_score}%`
            );
          } else {
            alert(
              `✅ Analysis complete!\n` +
              `${res.company_name}\n` +
              `Growth: ${res.growth_score}% | Risk: ${res.risk_score}%\n` +
              `📧 Report sent to your email.`
            );
          }
        },
        error: (err) => {
          console.error("Erreur lors de l'analyse", err);
          alert("An error occurred during analysis.");
        }
      });
  }

  // ── LOGIQUE UI ──────────────────────────────────────────────────────────

  getUserId(token: string | null): string | null {
    try {
      if (!token) return null;
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.sub ?? payload.user_id ?? null;
    } catch (e) { return null; }
  }

  getFiltered(): any[] {
    if (this.filter === 'ALL') return this.recommendations;
    return this.recommendations.filter(r => this.getSignalLabel(r.score) === this.filter);
  }

  setFilter(f: string) { this.filter = f; }

  toggle(i: number) {
    this.selectedId = this.selectedId === i ? null : i;
  }

  getBuyCount(): number {
    return this.recommendations.filter(r => r.score > 0.55).length;
  }

  getAvgScore(): string {
    if (!this.recommendations.length) return '0';
    const avg = this.recommendations.reduce((a, r) => a + r.score, 0) / this.recommendations.length;
    return (avg * 100).toFixed(0);
  }

  getTopSector(): string {
    return this.recommendations[0]?.sector ?? 'N/A';
  }

  getSignalClass(score: number): string {
    if (score > 0.75) return 'strong-buy';
    if (score > 0.55) return 'buy';
    if (score > 0.35) return 'hold';
    return 'avoid';
  }

  getSignalLabel(score: number): string {
    if (score > 0.75) return 'STRONG BUY';
    if (score > 0.55) return 'BUY';
    if (score > 0.35) return 'HOLD';
    return 'AVOID';
  }

  getScoreStyle(score: number): string {
    const pct = score * 100;
    const color = score > 0.75 ? '#10b981'
      : score > 0.55 ? '#3b82f6'
        : score > 0.35 ? '#f59e0b'
          : '#ef4444';
    return `background: conic-gradient(${color} ${pct * 3.6}deg, #f1f5f9 0deg)`;
  }

  // ── CHARTS ──────────────────────────────────────────────────────────────

  buildCharts() {
    if (!this.recommendations.length) return;
    this.buildBar();
    this.buildDonut();
  }

  buildBar() {
    const canvas = this.riskChartRef?.nativeElement;
    if (!canvas) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: this.recommendations.map(r => r.name),
        datasets: [{
          label: 'Score %',
          data: this.recommendations.map(r => Math.round(r.score * 100)),
          backgroundColor: this.recommendations.map(r =>
            r.score > 0.75 ? '#10b981'
              : r.score > 0.55 ? '#3b82f6'
                : r.score > 0.35 ? '#f59e0b'
                  : '#ef4444'
          ),
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { min: 0, max: 100 } }
      }
    });
  }

  buildDonut() {
    const canvas = this.sectorChartRef?.nativeElement;
    if (!canvas) return;
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    const sectors = [...new Set(this.recommendations.map(r => r.sector))];
    const counts = sectors.map(s => this.recommendations.filter(r => r.sector === s).length);

    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: sectors,
        datasets: [{
          data: counts,
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  // ── EMAIL AU OWNER ──────────────────────────────────────────────────────
  openInvestorEmail(r: any) {
    const subject = encodeURIComponent(`Investment Opportunity – ${r.name}`);
    const body = encodeURIComponent(
      `Dear Sir/Madam,

I am writing to express my interest in exploring a potential investment opportunity with ${r.name}.

Having reviewed your company's profile, I believe there is a strong alignment with our investment strategy, and I would welcome the opportunity to discuss this further.

I would be grateful if you could contact me at your earliest convenience to arrange a meeting or call at a time that suits you.

Thank you for your time and consideration.

Yours sincerely`
    );

    const gmailLink = `https://mail.google.com/mail/?view=cm&fs=1&to=${r.contact_email}&su=${subject}&body=${body}`;
    console.log('Email du owner:', r.contact_email);
    window.open(gmailLink, '_blank');
  }
}