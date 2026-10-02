import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InvestorService } from '../../../core/services/investor';

type SelectedKeys =
  | 'risk'
  | 'preferred_sector'
  | 'region_std'
  | 'portfolio_value'
  | 'active_companies';

interface Step {
  key: SelectedKeys;
  title: string;
  description: string;
  type: 'choice' | 'number';
  icon?: string;
}

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './onboarding.html',
  styleUrls: ['./onboarding.css']
})
export class OnboardingComponent implements OnInit {

  currentStep = 0;
  loading = false;
  error = '';

  selected: Record<SelectedKeys, any> = {
    risk: '',
    preferred_sector: '',
    region_std: '',
    portfolio_value: null,
    active_companies: null
  };

  steps: Step[] = [
    {
      key: 'risk',
      title: 'Quel est votre profil de risque ?',
      description: 'low / medium / high',
      type: 'choice',
      icon: '📊'
    },
    {
      key: 'preferred_sector',
      title: 'Quel secteur vous intéresse ?',
      description: 'Choisissez un secteur',
      type: 'choice',
      icon: '🏢'
    },
    {
      key: 'region_std',
      title: 'Votre région ?',
      description: 'NA / EU / AS / Other',
      type: 'choice',
      icon: '🌍'
    },
    {
      key: 'portfolio_value',
      title: 'Budget d’investissement',
      description: 'Montant total disponible',
      type: 'number',
      icon: '💰'
    },
    {
      key: 'active_companies',
      title: 'Nombre de compagnies',
      description: 'Dans combien de sociétés investissez-vous ?',
      type: 'number',
      icon: '📈'
    }
  ];

  questions: any = {
    risk: ['low', 'medium', 'high'],
    preferred_sector: [],
    region_std: []
  };

  constructor(
    private investorService: InvestorService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.investorService.getQuestions().subscribe({
      next: (data) => {
        this.questions = {
          risk: ['low', 'medium', 'high'],
          preferred_sector: data?.sectors ?? [],
          region_std: data?.regions ?? []
        };
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Erreur chargement questions';
      }
    });
  }

  get step(): Step {
    return this.steps[this.currentStep];
  }

  getOptions(): string[] {
    return this.questions[this.step.key] || [];
  }

  select(value: any): void {
    this.selected[this.step.key] = value;
  }

  isSelected(value: any): boolean {
    return this.selected[this.step.key] === value;
  }

  canProceed(): boolean {
    const value = this.selected[this.step.key];

    if (this.step.type === 'number') {
      return value !== null && value !== undefined && value !== '' && Number(value) >= 0;
    }

    return value !== '' && value !== null && value !== undefined;
  }

  next(): void {
    if (!this.canProceed()) return;

    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++;
    } else {
      this.submit();
    }
  }

  back(): void {
    if (this.currentStep > 0) this.currentStep--;
  }

  getProgress(): number {
    return ((this.currentStep + 1) / this.steps.length) * 100;
  }

  submit(): void {
    const token = localStorage.getItem('access_token');

    if (!token) {
      this.error = 'Vous devez être connecté';
      this.router.navigate(['/login']);
      return;
    }

    this.loading = true;

    const payload = {
      risk: this.selected.risk,
      preferred_sector: this.selected.preferred_sector,
      region_std: this.selected.region_std,
      portfolio_value: Number(this.selected.portfolio_value),
      active_companies: Number(this.selected.active_companies)
    };

    this.investorService.submitOnboarding(payload).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard/investor']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail || 'Erreur serveur';
      }
    });
  }
}