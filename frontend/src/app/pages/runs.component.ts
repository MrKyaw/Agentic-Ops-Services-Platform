import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService, RunItem } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-runs',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <section aria-labelledby="runs-title">
      <h1 id="runs-title">{{ t.nav.runs }}</h1>
      <form (ngSubmit)="start()" class="row">
        <label class="visually-hidden" for="agent">Agent</label>
        <input id="agent" name="agent" [(ngModel)]="agentId" placeholder="pilot-triage" required />
        <label class="visually-hidden" for="message">Message</label>
        <input id="message" name="message" [(ngModel)]="message" placeholder="Ask something…" required size="48" />
        <button type="submit" [disabled]="busy()">{{ t.common.submit }}</button>
      </form>
      @if (error()) { <p role="alert" class="error">{{ error() }}</p> }
      @if (loading()) { <p>{{ t.common.loading }}</p> }
      @if (!loading() && runs().length === 0) { <p>{{ t.common.empty }}</p> }
      <ul>
        @for (run of runs(); track run.id) {
          <li><a [routerLink]="['/runs', run.id]">{{ run.id }}</a> — {{ run.agent_id }} — <strong>{{ run.status }}</strong></li>
        }
      </ul>
    </section>
  `,
})
export class RunsComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  runs = signal<RunItem[]>([]);
  loading = signal(true);
  busy = signal(false);
  error = signal('');
  agentId = signal('pilot-triage');
  message = signal('');

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.api.listRuns().subscribe({
      next: (runs) => {
        this.runs.set(runs);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load runs.');
        this.loading.set(false);
      },
    });
  }

  start(): void {
    this.busy.set(true);
    this.error.set('');
    this.api.createRun(this.agentId().trim(), this.message().trim()).subscribe({
      next: () => {
        this.busy.set(false);
        this.message.set('');
        this.refresh();
      },
      error: () => {
        this.busy.set(false);
        this.error.set('Run failed to start.');
      },
    });
  }
}
