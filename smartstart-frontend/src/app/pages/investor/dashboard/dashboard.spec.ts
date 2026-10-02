import { CommonModule } from '@angular/common';

export class Dashboard {

  investorName = "Investor";

  recommendations = [
    { name: "Startup A", score: 0.87 },
    { name: "Startup B", score: 0.75 },
    { name: "Startup C", score: 0.62 }
  ];

  riskScore = 0.42;
  growthScore = 0.78;
}