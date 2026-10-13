import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthStore } from './auth-store';
import { environment } from '../../environments/environment';

export interface Agent {
  id: string;
  tenantId: string;
  displayName: string;
  pattern: string;
  version: string;
  status: string;
}
export interface Tenant {
  id: string;
  name: string;
  status: string;
}
export interface RunItem {
  id: string;
  agent_id: string;
  agent_version: string;
  status: string;
  created_at: string;
}
export interface RunDetail extends RunItem {
  input: unknown;
  output: unknown;
  usage: unknown;
  steps: Array<{ seq: number; kind: string; payload: unknown; latency_ms: number }>;
}
export interface Approval {
  id: string;
  run_id: string;
  action: string;
  status: string;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
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

  private url(path: string): string {
    return `${environment.apiUrl}${path}`;
  }

  listAgents(): Observable<Agent[]> {
    return this.http.get<Agent[]>(this.url('/v1/agents/'), { headers: this.headers(false) });
  }
  createAgent(body: { id: string; displayName: string; pattern: string }): Observable<Agent> {
    return this.http.post<Agent>(this.url('/v1/agents/'), body, { headers: this.headers() });
  }
  listTenants(): Observable<Tenant[]> {
    return this.http.get<Tenant[]>(this.url('/v1/tenants/'), { headers: this.headers(false) });
  }
  listRuns(): Observable<RunItem[]> {
    return this.http.get<RunItem[]>(this.url('/v1/runs/'), { headers: this.headers(false) });
  }
  createRun(agentId: string, message: string): Observable<{ id: string; status: string; answer?: string; approval_id?: string }> {
    return this.http.post<{ id: string; status: string }>(
      this.url('/v1/runs/'),
      { agent_id: agentId, input: { message } },
      { headers: this.headers() },
    );
  }
  getRun(id: string): Observable<RunDetail> {
    return this.http.get<RunDetail>(this.url(`/v1/runs/${id}`), { headers: this.headers(false) });
  }
  async streamRun(id: string, onDelta: (text: string) => void): Promise<void> {
    const response = await fetch(`${environment.apiUrl}/v1/runs/${id}/stream`, {
      headers: {
        Authorization: `Bearer ${this.auth.token()}`,
        'X-Tenant-ID': this.auth.tenant(),
      },
    });
    if (!response.ok || !response.body) throw new Error(`stream failed: ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';
      for (const frame of frames) {
        for (const line of frame.split('\n')) {
          if (line.startsWith('data:')) {
            try {
              onDelta((JSON.parse(line.slice(5)) as { delta: string }).delta + ' ');
            } catch {
              /* ignore malformed frames */
            }
          }
        }
      }
    }
  }
  listApprovals(): Observable<Approval[]> {
    return this.http.get<Approval[]>(this.url('/v1/approvals/'), { headers: this.headers(false) });
  }
  decideApproval(id: string, decision: 'approved' | 'rejected'): Observable<unknown> {
    return this.http.post(this.url(`/v1/approvals/${id}/decide`), { decision }, { headers: this.headers() });
  }
  queryKb(kbId: string, query: string): Observable<{ answer: string | null; abstained: boolean; passages: Array<{ content: string; document_id: string }> }> {
    return this.http.post<{ answer: string | null; abstained: boolean; passages: Array<{ content: string; document_id: string }> }>(
      this.url('/v1/kb/query'),
      { kb_id: kbId, query, top_k: 5, citations: true },
      { headers: this.headers() },
    );
  }
  usageSummary(): Observable<{ runs: number; tokens_in: number; tokens_out: number; cost_usd: number }> {
    return this.http.get<{ runs: number; tokens_in: number; tokens_out: number; cost_usd: number }>(
      this.url('/v1/usage/summary'),
      { headers: this.headers(false) },
    );
  }
}
