import { Component, inject, signal } from '@angular/core';
import { ApiService, Tenant } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-tenants',
  standalone: true,
  template: `
    <section aria-labelledby="tenants-title">
      <h1 id="tenants-title">{{ t.nav.tenants }}</h1>
      @if (items().length === 0) { <p>{{ t.common.empty }}</p> }
      <ul>
        @for (tenant of items(); track tenant.id) {
          <li><strong>{{ tenant.id }}</strong> — {{ tenant.name }} ({{ tenant.status }})</li>
        }
      </ul>
    </section>
  `,
})
export class TenantsComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  items = signal<Tenant[]>([]);

  constructor() {
    this.api.listTenants().subscribe({ next: (items) => this.items.set(items) });
  }
}
