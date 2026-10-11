import { Injectable, signal } from '@angular/core';

const TOKEN_KEY = 'sap.token';
const TENANT_KEY = 'sap.tenant';

@Injectable({ providedIn: 'root' })
export class AuthStore {
  token = signal(localStorage.getItem(TOKEN_KEY) ?? '');
  tenant = signal(localStorage.getItem(TENANT_KEY) ?? '');

  get connected(): boolean {
    return this.token().length > 0 && this.tenant().length > 0;
  }

  connect(token: string, tenant: string): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(TENANT_KEY, tenant);
    this.token.set(token);
    this.tenant.set(tenant);
  }

  disconnect(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TENANT_KEY);
    this.token.set('');
    this.tenant.set('');
  }
}
