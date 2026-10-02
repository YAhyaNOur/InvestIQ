export interface RiskResult {
  status: string;
  analysis: {
    risk_score: number;     
    zone: string; 
    confidence: string;
    threshold_used?: number; 
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