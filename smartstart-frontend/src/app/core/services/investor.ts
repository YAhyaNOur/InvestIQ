import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class InvestorService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  getQuestions(): Observable<any> {
    return this.http.get(`${this.apiUrl}/onboarding/questions`, {
      headers: this.getHeaders()
    });
  }

  submitOnboarding(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/onboarding/submit`, data, {
      headers: this.getHeaders()
    });
  }
}