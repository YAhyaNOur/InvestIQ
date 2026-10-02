import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CompanyData } from '../models/detection/detection-input.model';
import { DetectionResult } from '../models/detection/detection-result.model';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DetectionService {
  private http = inject(HttpClient);
  
  
  private readonly API_URL = 'http://localhost:8000/score/analyze';

  analyzeCompany(data: CompanyData): Observable<DetectionResult> {
    return this.http.post<DetectionResult>(this.API_URL, data);
  }
}