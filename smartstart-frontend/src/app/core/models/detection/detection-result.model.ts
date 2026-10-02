export interface DetectionResult {
  is_anomaly: boolean;
  anomaly_score: number;      
  anomaly_severity: number;   
  anomaly_label: 'TYPICAL PROFILE' | 'MILD DEVIATION' | 'SIGNIFICANT DEVIATION' | 'CRITICAL ANOMALY';
  health_score: number;       }