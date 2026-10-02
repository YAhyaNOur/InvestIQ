import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { DetectionService } from '../../core/services/detection.service';

// ✅ Interface mise à jour pour correspondre au Backend FastAPI
export interface DetectionResult {
  is_anomaly: boolean;
  anomaly_score: number;
  anomaly_severity: number; 
  anomaly_label: 'TYPICAL PROFILE' | 'MILD DEVIATION' | 'SIGNIFICANT DEVIATION' | 'CRITICAL ANOMALY';
  health_score: number;
}

export interface CompanyData {
  Debt_to_Revenue: number;
  Current_Ratio: number;
  Revenue_per_Employee: number;
  Net_Debt: number;
  Employees_Sector_Z: number;
}

@Component({
  selector: 'app-detection',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './detection.component.html',
  styleUrl: './detection.component.css'
})
export class DetectionComponent {
  private fb = inject(FormBuilder);
  private detectionService = inject(DetectionService);

  result = signal<DetectionResult | null>(null);
  loading = signal(false);

  form = this.fb.group({
    Debt_to_Revenue: [0.5, [Validators.required]],
    Current_Ratio: [1.5, [Validators.required]],
    Revenue_per_Employee: [150000, [Validators.required]],
    Net_Debt: [0, [Validators.required]],
    Employees_Sector_Z: [0, [Validators.required]],
  });

  submit() {
    if (this.form.valid) {
      this.loading.set(true);
      const payload = this.form.getRawValue() as CompanyData;
      
      this.detectionService.analyzeCompany(payload).subscribe({
        next: (res: DetectionResult) => {
          this.result.set(res);
          this.loading.set(false);
        },
        error: (err: any) => {
          console.error('Scan Error:', err);
          this.loading.set(false);
        }
      });
    }
  }

  
  getRiskColor(label: string | undefined): string {
    if (!label) return '#94a3b8';
    
    switch (label.toUpperCase()) {
      case 'CRITICAL ANOMALY': return '#ef4444';      // Rouge
      case 'SIGNIFICANT DEVIATION': return '#f59e0b'; // Orange/Ambre
      case 'MILD DEVIATION': return '#3b82f6';        // Bleu
      case 'TYPICAL PROFILE': return '#10b981';       // Vert
      default: return '#94a3b8';
    }
  }
}