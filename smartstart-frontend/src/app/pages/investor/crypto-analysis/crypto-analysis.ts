import {
  Component, OnInit, OnDestroy,
  AfterViewInit, AfterViewChecked,
  ChangeDetectorRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule
} from '@angular/forms';
import {
  trigger, state, style, transition, animate
} from '@angular/animations';

import { CryptoService } from '../../../core/services/crypto.service';
import { CryptoResult } from '../../../schemas/crypto.model';
import Chart from 'chart.js/auto';

import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-crypto-analysis',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './crypto-analysis.html',
  styleUrls: ['./crypto-analysis.css'],
  animations: [
    trigger('fadeInUp', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(24px)' }),
        animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('slideToggle', [
      state('open', style({ height: '*', opacity: 1, overflow: 'hidden' })),
      state('closed', style({ height: '0px', opacity: 0, overflow: 'hidden' })),
      transition('open <=> closed', animate('300ms ease-in-out'))
    ])
  ]
})
export class CryptoAnalysisComponent
  implements OnInit, OnDestroy, AfterViewInit, AfterViewChecked {

  analysisForm!: FormGroup;

  loading = false;
  result: CryptoResult | null = null;
  error = '';
  showForm = true;

  private charts: Chart[] = [];
  private chartInitialized = false;

  periodes = [
    { label: '1 an', value: 365 },
    { label: '2 ans', value: 730 },
    { label: '3 ans', value: 1095 }
  ];

  horizons = [
    { label: '7 jours', value: 7 },
    { label: '14 jours', value: 14 },
    { label: '30 jours', value: 30 }
  ];

  constructor(
    private fb: FormBuilder,
    private cryptoService: CryptoService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.analysisForm = this.fb.group({
      societe: ['', Validators.required],
      ticker: ['BTC-USD', Validators.required],
      jours: [365, Validators.required],
      horizon: [7, Validators.required],
      budget: [0, [Validators.required, Validators.min(0)]]
    });
  }

  ngAfterViewInit(): void { }

  ngAfterViewChecked(): void {
    if (this.result && !this.chartInitialized) {
      const canvas = document.getElementById('chartPrix') as HTMLCanvasElement;
      if (canvas) {
        this.chartInitialized = true;
        this.initCharts();
        this.cdr.detectChanges();
      }
    }
  }

  ngOnDestroy(): void {
    this.destroyCharts();
  }

  onSubmit(): void {
    if (this.analysisForm.invalid || this.loading) return;

    this.loading = true;
    this.error = '';
    this.result = null;
    this.showForm = false;
    this.chartInitialized = false;
    this.destroyCharts();

    const form = this.analysisForm.value;

    const payload = {
      societe: (form.societe || '').trim(),
      ticker: form.ticker,
      jours: Number(form.jours),
      horizon: Number(form.horizon),
      budget: Number(form.budget) || 0
    };

    this.cryptoService.analyze(payload).subscribe({
      next: (res: CryptoResult) => {
        console.log('RESULT RECU:', res);
        console.log('BUDGET ANALYSIS:', res.budget_analysis);
        this.result = res;
        this.loading = false;
        this.chartInitialized = false;
      },

      error: (err: any) => {
        console.error(err);
        this.loading = false;
        this.showForm = true;
        this.error = err?.error?.detail || 'Erreur analyse crypto';
      }
    });
  }

  resetForm(): void {
    this.result = null;
    this.showForm = true;
    this.error = '';
    this.chartInitialized = false;
    this.destroyCharts();
  }

  exportPDF(): void {
    const printContent = document.querySelector('.container') as HTMLElement;
    if (!printContent) { window.print(); return; }
    const originalBody = document.body.innerHTML;
    document.body.innerHTML = printContent.outerHTML;
    window.print();
    document.body.innerHTML = originalBody;
    window.location.reload();
  }

  private initCharts(): void {
    this.destroyCharts();

    if (!this.result?.historique?.prix?.length) {
      console.warn('Pas de données historique');
      return;
    }

    const canvas = document.getElementById('chartPrix') as HTMLCanvasElement;
    if (!canvas) {
      console.warn('Canvas introuvable');
      return;
    }

    this.charts.push(
      new Chart(canvas, {
        type: 'line',
        data: {
          labels: this.result.historique.dates,
          datasets: [{
            label: this.result.crypto_symbol,
            data: this.result.historique.prix,
            borderColor: '#185FA5',
            backgroundColor: 'rgba(55,138,221,0.08)',
            borderWidth: 2,
            pointRadius: 0,
            fill: true,
            tension: 0.3
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { display: false },
            y: {
              display: true,
              ticks: {
                callback: (v: any) => '$' + Math.round(Number(v) / 1000) + 'k',
                font: { size: 11 }
              },
              grid: { color: 'rgba(0,0,0,0.05)' }
            }
          }
        }
      })
    );
  }

  private destroyCharts(): void {
    this.charts.forEach(c => c.destroy());
    this.charts = [];
  }

  isFieldInvalid(field: string): boolean {
    const f = this.analysisForm.get(field);
    return !!(f && f.invalid && (f.dirty || f.touched));
  }
}