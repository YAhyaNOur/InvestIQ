// src/app/core/services/startup-dashboard.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AIAssistantRequest, AIAssistantResponse } from '../models/startup-dashboard.models';
import { environment } from '../../../environments/environments';

@Injectable({ providedIn: 'root' })
export class StartupDashboardService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  askAI(payload: AIAssistantRequest): Observable<AIAssistantResponse> {
    return this.http.post<AIAssistantResponse>(`${this.base}/startup/ai/ask`, payload);
  }
}
