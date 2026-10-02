import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { RiskService } from '../../core/services/risk.service';

interface RiskResult {
  status: string;
  analysis: {
    risk_score: number;
    zone: string;
    confidence: string;
  };
  recommendation: {
    action: string;
    summary: string;
  };
  ui_display: {
    color: string;
    label: string;
  };
}

@Component({
  selector: 'app-risk',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './risk.component.html',
  styleUrls: ['./risk.component.css']
})
export class RiskComponent {

  formData = {
    Sector: 'Software',
    Region_std: 'Europe',
    Debt_To_Equity: 1,
    Total_Debt_M: 50,
    Current_Ratio: 1.2,
    Employees_Sector_Z: 0
  };
  sectors = [
    'Communication Services', 'Consumer Cyclical', 'Technology', 'Healthcare',
    'Industrials', 'Real Estate', 'Financial Services', 'Basic Materials',
    'Consumer Defensive', 'Energy', 'Utilities', 'Personal Care',
    'Software Engineering', 'IT Distribution', 'Hardware'
  ];

  
  regions = ['North_America', 'Europe', 'Asia', 'Other'];

  result: RiskResult | null = null;
  loading = false;

  constructor(
    private riskService: RiskService,
    private cdr: ChangeDetectorRef
  ) {}

  
  private toNumber(value: any): number {
    return Number(String(value).replace(',', '.')) || 0;
  }

  onAnalyze() {

  
    const payload = {
      Sector: this.formData.Sector || "UNKNOWN",
      Region_std: this.formData.Region_std || "UNKNOWN",

      Debt_To_Equity: this.toNumber(this.formData.Debt_To_Equity),
      Total_Debt_M: this.toNumber(this.formData.Total_Debt_M),
      Current_Ratio: this.toNumber(this.formData.Current_Ratio),
      Employees_Sector_Z: this.toNumber(this.formData.Employees_Sector_Z)
    };

    console.log("PAYLOAD:", payload);

    this.loading = true;

    this.riskService.predictRisk(payload).subscribe({
      next: (res) => {
        this.result = res;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("API ERROR:", err);
        this.loading = false;
      }
    });
  }
}