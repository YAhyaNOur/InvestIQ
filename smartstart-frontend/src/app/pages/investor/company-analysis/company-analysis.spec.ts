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
    lang: 'fr' | 'en' = 'fr';
    tooltipVisible: string | null = null;

    // ── PME réelles disponibles sur Yahoo Finance ──────────────────────────────
    popularSymbols = [
        { symbol: 'LBRT', name: 'Liberty Oilfield' },
        { symbol: 'KTOS', name: 'Kratos Defense' },
        { symbol: 'HALO', name: 'Halozyme Therap.' },
        { symbol: 'IIPR', name: 'Innovative Indus.' },
        { symbol: 'PRGS', name: 'Progress Software' },
        { symbol: 'MGNI', name: 'Magnite Inc.' },
        { symbol: 'ASAN', name: 'Asana Inc.' },
        { symbol: 'FOUR', name: 'Shift4 Payments' },
    ];

    // ── Traductions ────────────────────────────────────────────────────────────
    t: Record<string, Record<string, string>> = {
        fr: {
            title: 'Analyse d\'Entreprise',
            subtitle: 'Entrez un symbole boursier pour obtenir une analyse IA',
            placeholder: 'Symbole boursier (ex: AAPL)…',
            analyzeBtn: 'Analyser',
            loadingBtn: 'Chargement…',
            popular: 'PME populaires :',
            loadingMsg: 'Récupération des données & modèles IA…',
            emptyTitle: 'Recherchez une entreprise',
            emptyDesc: 'Entrez un symbole pour obtenir une analyse croissance & risque',
            investScore: 'Score Investissement',
            growthScore: '📈 Score Croissance',
            riskScore: '⚠️ Score Risque',
            marketCap: '💰 Capitalisation',
            peRatio: '📊 Ratio C/B',
            beta: '⚡ Bêta',
            price: '💵 Prix',
            aiBreakdown: 'Décomposition IA',
            gauge: 'Jauge Score Investissement',
            financialMetrics: 'Indicateurs Financiers',
            about: 'À propos de',
            revGrowth: 'Croissance du CA',
            debtEq: 'Dette/Capitaux propres',
            currentRatio: 'Ratio de liquidité',
            ebitda: 'Marge EBITDA',
            netDebt: 'Dette nette',
            range52: 'Plage 52 sem.',
            strong: '↑ Fort',
            moderate: '→ Modéré',
            declining: '↓ En déclin',
            low: '✓ Faible',
            high: '⚠ Élevé',
            healthy: '✓ Sain',
            watch: '⚠ Surveiller',
            excellent: '✓ Excellent',
            good: '→ Correct',
            netCash: '✓ Trésorerie nette',
            leveraged: 'Endetté',
            dashboard: 'Tableau de bord',
            analyze: 'Analyser',
            investor: 'Investisseur',
            premium: 'Premium',
        },
        en: {
            title: 'Company Analysis',
            subtitle: 'Enter a stock symbol to get AI-powered insights',
            placeholder: 'Stock symbol (e.g. AAPL)…',
            analyzeBtn: 'Analyze',
            loadingBtn: 'Loading…',
            popular: 'Popular SMEs:',
            loadingMsg: 'Fetching data & running AI models…',
            emptyTitle: 'Search any company',
            emptyDesc: 'Enter a stock symbol to get AI-powered growth & risk analysis',
            investScore: 'Investment Score',
            growthScore: '📈 Growth Score',
            riskScore: '⚠️ Risk Score',
            marketCap: '💰 Market Cap',
            peRatio: '📊 P/E Ratio',
            beta: '⚡ Beta',
            price: '💵 Price',
            aiBreakdown: 'AI Score Breakdown',
            gauge: 'Investment Score Gauge',
            financialMetrics: 'Financial Metrics',
            about: 'About',
            revGrowth: 'Revenue Growth',
            debtEq: 'Debt / Equity',
            currentRatio: 'Current Ratio',
            ebitda: 'EBITDA Margin',
            netDebt: 'Net Debt',
            range52: '52-Week Range',
            strong: '↑ Strong',
            moderate: '→ Moderate',
            declining: '↓ Declining',
            low: '✓ Low',
            high: '⚠ High',
            healthy: '✓ Healthy',
            watch: '⚠ Watch',
            excellent: '✓ Excellent',
            good: '→ Good',
            netCash: '✓ Net Cash',
            leveraged: 'Leveraged',
            dashboard: 'Dashboard',
            analyze: 'Analyze',
            investor: 'Investor',
            premium: 'Premium',
        }
    };

    // ── Explications des ratios ────────────────────────────────────────────────
    ratioExplanations: Record<string, Record<string, string>> = {
        fr: {
            revGrowth: 'La croissance du chiffre d\'affaires mesure l\'augmentation des ventes sur un an. >10% indique une forte dynamique commerciale.',
            debtEq: 'Le ratio Dette/Capitaux propres compare l\'endettement aux fonds propres. <1 signifie que l\'entreprise est peu endettée et financièrement solide.',
            currentRatio: 'Le ratio de liquidité mesure la capacité à rembourser les dettes à court terme. >1,5 est considéré comme sain.',
            ebitda: 'La marge EBITDA représente la rentabilité opérationnelle avant intérêts, impôts et amortissements. >20% est excellent.',
            netDebt: 'La dette nette = dettes financières − trésorerie. Une valeur négative signifie que l\'entreprise détient plus de cash que de dettes.',
            range52: 'La plage 52 semaines montre les cours extrêmes sur un an, utile pour évaluer la volatilité et les niveaux de support/résistance.',
            peRatio: 'Le ratio Cours/Bénéfice (PER) indique combien les investisseurs payent pour 1 € de bénéfice. Un PER élevé peut signifier une valorisation premium.',
            beta: 'Le bêta mesure la sensibilité de l\'action par rapport au marché. β>1 = plus volatile que le marché ; β<1 = moins volatile.',
        },
        en: {
            revGrowth: 'Revenue growth measures the year-over-year increase in sales. >10% indicates strong commercial momentum.',
            debtEq: 'Debt/Equity ratio compares total debt to shareholders\' equity. <1 means the company is lightly leveraged and financially solid.',
            currentRatio: 'The current ratio measures the ability to cover short-term liabilities. >1.5 is considered healthy.',
            ebitda: 'EBITDA margin represents operational profitability before interest, taxes, and amortisation. >20% is excellent.',
            netDebt: 'Net debt = financial liabilities − cash. A negative value means the company holds more cash than debt.',
            range52: 'The 52-week range shows extreme prices over a year, useful to assess volatility and support/resistance levels.',
            peRatio: 'The Price/Earnings ratio shows how much investors pay per $1 of earnings. A high P/E may indicate a premium valuation.',
            beta: 'Beta measures the stock\'s sensitivity relative to the market. β>1 = more volatile; β<1 = less volatile.',
        }
    };

    constructor(private http: HttpClient, private cdr: ChangeDetectorRef) { }

    ngOnInit() { }
    ngAfterViewInit() { }

    switchLang(l: 'fr' | 'en') { this.lang = l; }

    tr(key: string): string { return this.t[this.lang][key] ?? key; }

    explain(key: string): string {
        return this.ratioExplanations[this.lang][key] ?? '';
    }

    showTooltip(key: string) { this.tooltipVisible = key; }
    hideTooltip() { this.tooltipVisible = null; }

    analyze() {
        if (!this.symbol.trim()) return;
        const token = localStorage.getItem('access_token');
        if (!token) return;

        this.loading = true;
        this.error = '';
        this.result = null;
        this.searched = true;

        const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

        this.http.post<any>(
            'http://localhost:8000/analyze/company',
            { symbol: this.symbol.toUpperCase() },
            { headers }
        ).subscribe({
            next: (data) => {
                this.result = data;
                this.loading = false;
                this.cdr.detectChanges();
                setTimeout(() => this.buildCharts(), 300);
            },
            error: (e) => {
                this.error = e.error?.detail || 'Symbol not found. Try: LBRT, KTOS, HALO…';
                this.loading = false;
                this.cdr.detectChanges();
            }
        });
    }

    quickSearch(sym: string) { this.symbol = sym; this.analyze(); }

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
                labels: [this.tr('growthScore'), this.tr('riskScore'), this.tr('investScore')],
                datasets: [{
                    data: [this.result.growth_score, this.result.risk_score, this.result.investment_score],
                    backgroundColor: ['#2dd4bf', '#f43f5e', '#6366f1'],
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
                    y: { min: 0, max: 100, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }
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
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Score', ''],
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [this.result.decision_color, '#1e293b'],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '78%',
                plugins: { legend: { display: false }, tooltip: { enabled: false } }
            }
        });
    }

    getScoreColor(score: number): string {
        if (score > 70) return '#2dd4bf';
        if (score > 50) return '#6366f1';
        if (score > 30) return '#f59e0b';
        return '#f43f5e';
    }

    formatMarketCap(val: number): string {
        if (!val) return 'N/A';
        if (val >= 1e12) return (val / 1e12).toFixed(2) + 'T';
        if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
        if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
        return val.toString();
    }
}