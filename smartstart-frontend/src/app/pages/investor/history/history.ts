import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Component({
  selector: 'app-investor-history',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './history.html',
  styleUrls: ['./history.css']
})
export class InvestorHistory implements OnInit {
  interests: any[] = [];
  loading = true;

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) { }

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    const token = localStorage.getItem('access_token');
    if (!token) { this.loading = false; return; }

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.get<any>('http://localhost:8000/interest/my-interests-full', { headers })
      .subscribe({
        next: (res) => {
          this.interests = res.interests ?? [];
          this.loading = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.loading = false;
          this.cdr.detectChanges();
        }
      });
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

  getSignalColor(score: number): string {
    if (score > 0.75) return '#10b981';
    if (score > 0.55) return '#3b82f6';
    if (score > 0.35) return '#f59e0b';
    return '#ef4444';
  }

  // Gauge SVG : arc = 157px total (demi-cercle r=50, périmètre ≈ 157)
  getGaugeDash(score: number): string {
    const total = 157;
    const filled = score * total;
    return `${filled} ${total}`;
  }

  openEmail(r: any) {
    const subject = encodeURIComponent(`Investment Opportunity – ${r.name}`);
    const body = encodeURIComponent(
      `Dear Sir/Madam,

I am writing to express my interest in exploring a potential investment opportunity with ${r.name}.

Having reviewed your company's profile, I believe there is a strong alignment with our investment strategy, and I would welcome the opportunity to discuss this further.

I would be grateful if you could contact me at your earliest convenience to arrange a meeting or call at a time that suits you.

Thank you for your time and consideration.

Yours sincerely`
    );
    const gmailLink = `https://mail.google.com/mail/?view=cm&fs=1&to=${r.contact_email ?? ''}&su=${subject}&body=${body}`;
    window.open(gmailLink, '_blank');
  }
}