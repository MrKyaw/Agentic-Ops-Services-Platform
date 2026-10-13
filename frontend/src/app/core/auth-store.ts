import { Injectable, signal } from '@angular/core';
import { environment } from '../../environments/environment';

const TOKEN_KEY = 'sap.token';
const TENANT_KEY = 'sap.tenant';
const API_KEY = 'sap.apiUrl';

@Injectable({ providedIn: 'root' })
export class AuthStore {
  token = signal(localStorage.getItem(TOKEN_KEY) ?? '');
  tenant = signal(localStorage.getItem(TENANT_KEY) ?? '');
  apiUrl = signal(localStorage.getItem(API_KEY) ?? '');

  get connected(): boolean {
    return this.token().length > 0 && this.tenant().length > 0;
  }

  connect(token: string, tenant: string, apiUrl = ''): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(TENANT_KEY, tenant);
    if (apiUrl) localStorage.setItem(API_KEY, apiUrl);
    else localStorage.removeItem(API_KEY);
    this.token.set(token);
    this.tenant.set(tenant);
    this.apiUrl.set(apiUrl);
  }

  disconnect(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TENANT_KEY);
    this.token.set('');
    this.tenant.set('');
  }

  endpoint(): string {
    return this.apiUrl() || environment.apiUrl;
  }
}
