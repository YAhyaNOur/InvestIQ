import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RiskService {

  private apiUrl = 'http://127.0.0.1:8000/risk/predict_risk';

  constructor(private http: HttpClient) {}

  predictRisk(data: any): Observable<any> {
    return this.http.post(this.apiUrl, data);
  }
}