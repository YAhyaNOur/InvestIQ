import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GrowthInput } from '../models/growth/growth-input.model';
import { GrowthResult } from '../models/growth/growth-result.model';

@Injectable({
  providedIn: 'root'
})
export class GrowthService {
  private apiUrl = 'http://localhost:8000/growth/predict';

  constructor(private http: HttpClient) { }

  predict(data: GrowthInput): Observable<GrowthResult> {
    return this.http.post<GrowthResult>(this.apiUrl, data);
  }
}