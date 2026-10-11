import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { JsonPipe } from '@angular/common';
import { ApiService, RunDetail } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-run-detail',
  standalone: true,
  imports: [RouterLink, JsonPipe],
  template: `
    <section aria-labelledby="trace-title">
      <p><a routerLink="/runs">← Runs</a></p>
      <h1 id="trace-title">Trace {{ run()?.id }}</h1>
      @if (run(); as r) {
        <p>Status: <strong>{{ r.status }}</strong> · Agent: {{ r.agent_id }} ({{ r.agent_version }})</p>
        <h2>Output</h2>
        <pre>{{ r.output | json }}</pre>
        <h2>Steps</h2>
        <ol>
          @for (step of r.steps; track step.seq) {
            <li><strong>{{ step.kind }}</strong> <small>{{ step.latency_ms }} ms</small>
              <pre>{{ step.payload | json }}</pre>
            </li>
          }
        </ol>
      } @else {
        <p>{{ t.common.loading }}</p>
      }
    </section>
  `,
})
export class RunDetailComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  run = signal<RunDetail | null>(null);

  constructor() {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.getRun(id).subscribe({ next: (run) => this.run.set(run) });
  }
}
