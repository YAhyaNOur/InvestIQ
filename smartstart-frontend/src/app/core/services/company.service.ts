import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class CompanyService {

  private API = 'http://localhost:8000/companies';

  constructor(private http: HttpClient) {}

  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      headers: new HttpHeaders({
        Authorization: `Bearer ${token}`
      })
    };
  }

  getMyCompany() {
    return this.http.get(`${this.API}/me`, this.getHeaders());
  }

  createCompany(data: any) {
    return this.http.post(`${this.API}/`, data, this.getHeaders());
  }

  updateCompany(data: any) {
    return this.http.put(`${this.API}/me`, data, this.getHeaders());
  }
}