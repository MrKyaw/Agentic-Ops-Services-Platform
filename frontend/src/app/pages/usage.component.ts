import { Component, inject, signal } from '@angular/core';
import { ApiService } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-usage',
  standalone: true,
  template: `
    <section aria-labelledby="usage-title">
      <h1 id="usage-title">{{ t.nav.usage }}</h1>
      @if (summary(); as s) {
        <dl>
          <dt>Runs today</dt><dd>{{ s.runs }}</dd>
          <dt>Tokens in / out</dt><dd>{{ s.tokens_in }} / {{ s.tokens_out }}</dd>
          <dt>Cost (USD)</dt><dd>{{ s.cost_usd }}</dd>
        </dl>
      } @else {
        <p>{{ t.common.loading }}</p>
      }
    </section>
  `,
})
export class UsageComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  summary = signal<{ runs: number; tokens_in: number; tokens_out: number; cost_usd: number } | null>(null);

  constructor() {
    this.api.usageSummary().subscribe({ next: (summary) => this.summary.set(summary) });
  }
}
