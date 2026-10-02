import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

import { GrowthService } from '../../core/services/growth.service';
import { GrowthResult } from '../../core/models/growth/growth-result.model';

@Component({
  selector: 'app-growth',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './growth.component.html',
  styleUrls: ['./growth.component.css']
})
export class GrowthComponent {

  growthForm: FormGroup;
  predictionResult?: GrowthResult;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private growthService: GrowthService,
    private cdr: ChangeDetectorRef
  ) {
    this.growthForm = this.fb.group({
      Sector: ['', Validators.required],
      Beta: [0, Validators.required],
      Region_std: ['', Validators.required],
      Net_Debt: [0, Validators.required],
      Revenue_Growth: [0, Validators.required]
    });
  }

  onSubmit(): void {
    if (this.growthForm.valid) {

      this.isLoading = true;
      this.predictionResult = undefined;

      const payload = {
        Sector: this.growthForm.value.Sector,
        Beta: Number(this.growthForm.value.Beta),
        Region_std: this.growthForm.value.Region_std,
        Net_Debt: Number(this.growthForm.value.Net_Debt),
        Revenue_Growth: Number(this.growthForm.value.Revenue_Growth)
      };

      console.log("PAYLOAD SEND:", payload);

      this.growthService.predict(payload).subscribe({
        next: (res: GrowthResult) => {
          this.predictionResult = res;
          this.isLoading = false;
          this.cdr.detectChanges();
        },
        error: (err: any) => {
          console.error('Erreur API:', err);
          this.isLoading = false;
          this.cdr.detectChanges();
        }
      });
    }
  }
}