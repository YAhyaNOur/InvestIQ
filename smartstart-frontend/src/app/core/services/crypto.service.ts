import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CryptoRequest,
  CryptoResult
} from '../../schemas/crypto.model';

@Injectable({
  providedIn: 'root'
})
export class CryptoService {

  private apiUrl = 'http://localhost:8000/api/crypto';

  constructor(private http: HttpClient) {}

  analyze(request: CryptoRequest): Observable<CryptoResult> {
    return this.http.post<CryptoResult>(
      `${this.apiUrl}/analyze`,
      request
    );
  }
}