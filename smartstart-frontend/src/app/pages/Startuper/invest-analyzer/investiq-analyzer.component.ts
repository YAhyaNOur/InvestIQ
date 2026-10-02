import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';

export interface AnalysisResult {
  score: number;
  sector: string;
  project_type: string;
  keywords: string[];
  market_potential: number;   // ROI estimé
  innovation_score: number;   // Faisabilité
  risk_level: number;
  advantages: string[];
  disadvantages: string[];
  recommendation: string;
  funding_potential: string;
  target_market: string;
}

@Component({
  selector: 'app-investiq-analyzer',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './investiq-analyzer.component.html',
  styleUrls: ['./investiq-analyzer.component.css']
})
export class InvestiqAnalyzerComponent implements OnInit {
  projectDescription = '';
  isLoading = false;
  result: AnalysisResult | null = null;
  errorMessage = '';
  charCount = 0;
  maxChars = 2000;

  // Exemples adaptés aux projets d'entreprise (pas de startup / levée de fonds)
  exampleIdeas = [
    'Nous souhaitons déployer un ERP pour automatiser notre gestion de production et de stock. Le budget de 150 000€ est validé, notre équipe IT est en place et le fournisseur a été identifié après appel d\'offres.',
    'Construction d\'un nouvel entrepôt logistique de 800m² pour augmenter notre capacité de stockage et réduire les délais de livraison. Équipe de chantier expérimentée, budget de 400 000€ approuvé par le CA.',
    'Recrutement de 8 ingénieurs spécialisés et mise en place d\'une politique RH structurée pour accompagner notre croissance commerciale prévue sur les 18 prochains mois.',
  ];

  constructor(private http: HttpClient) { }

  ngOnInit(): void { }

  onTextChange(): void {
    this.charCount = this.projectDescription.length;
  }

  loadExample(example: string): void {
    this.projectDescription = example;
    this.charCount = example.length;
    this.errorMessage = '';
  }

  analyze(): void {
    if (!this.projectDescription.trim() || this.projectDescription.length < 50) {
      this.errorMessage = 'Veuillez décrire votre projet en au moins 50 caractères.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.result = null;

    this.http.post<AnalysisResult>('http://localhost:8000/analyze', {
      description: this.projectDescription
    }).subscribe({
      next: (data) => {
        this.result = data;
        this.isLoading = false;
        setTimeout(() => {
          document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Erreur lors de l\'analyse. Vérifiez que le backend est démarré sur le port 8000.';
      }
    });
  }

  getScoreClass(score: number): string {
    if (score >= 75) return 'score-high';
    if (score >= 50) return 'score-medium';
    return 'score-low';
  }

  getScoreLabel(score: number): string {
    if (score >= 80) return 'Excellent';
    if (score >= 65) return 'Prometteur';
    if (score >= 50) return 'Potentiel';
    if (score >= 35) return 'À retravailler';
    return 'Risqué';
  }

  getRiskLabel(risk: number): string {
    if (risk >= 70) return 'Élevé';
    if (risk >= 40) return 'Modéré';
    return 'Faible';
  }

  getRiskClass(risk: number): string {
    if (risk >= 70) return 'risk-high';
    if (risk >= 40) return 'risk-medium';
    return 'risk-low';
  }

  resetAnalysis(): void {
    this.result = null;
    this.projectDescription = '';
    this.charCount = 0;
    this.errorMessage = '';
  }
}