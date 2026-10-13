import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthStore } from './auth-store';
import { environment } from '../../environments/environment';
import { HttpHeaders } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class RegistryService {
  private http = inject(HttpClient);
  private auth = inject(AuthStore);

  private headers(contentType = true): HttpHeaders {
    let headers = new HttpHeaders({
      Authorization: `Bearer ${this.auth.token()}`,
      'X-Tenant-ID': this.auth.tenant(),
    });
    if (contentType) headers = headers.set('Content-Type', 'application/json');
    return headers;
  }

  listPrompts(): Observable<Array<{ id: string; version: number; status: string }>> {
    return this.http.get<Array<{ id: string; version: number; status: string }>>(
      `${environment.apiUrl}/v1/prompts/`,
      { headers: this.headers(false) },
    );
  }
  createPrompt(id: string, template: string): Observable<{ id: string; version: number }> {
    return this.http.post<{ id: string; version: number }>(
      `${environment.apiUrl}/v1/prompts/`,
      { id, template, variables: [] },
      { headers: this.headers() },
    );
  }
  approvePrompt(id: string, version: number): Observable<unknown> {
    return this.http.post(
      `${environment.apiUrl}/v1/prompts/${id}/${version}/approve`,
      {},
      { headers: this.headers() },
    );
  }
  listExperiments(): Observable<Array<{ id: string; subject_type: string; metrics: Record<string, number> }>> {
    return this.http.get<Array<{ id: string; subject_type: string; metrics: Record<string, number> }>>(
      `${environment.apiUrl}/v1/experiments/`,
      { headers: this.headers(false) },
    );
  }
  draftWorkflow(objective: string): Observable<{ manifest: unknown; test_cases: unknown[] }> {
    return this.http.post<{ manifest: unknown; test_cases: unknown[] }>(
      `${environment.apiUrl}/v1/builder/draft`,
      { objective },
      { headers: this.headers() },
    );
  }
}
