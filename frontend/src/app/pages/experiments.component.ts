import { Component, inject, signal } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { RegistryService } from '../core/registry.service';

@Component({
  selector: 'app-experiments',
  standalone: true,
  imports: [JsonPipe],
  template: `
    <section aria-labelledby="experiments-title">
      <h1 id="experiments-title">Experiments</h1>
      @if (items().length === 0) { <p>No experiments recorded yet.</p> }
      <ul>
        @for (experiment of items(); track experiment.id) {
          <li><strong>{{ experiment.id }}</strong> — {{ experiment.subject_type }}
            <pre>{{ experiment.metrics | json }}</pre>
          </li>
        }
      </ul>
    </section>
  `,
})
export class ExperimentsComponent {
  private registry = inject(RegistryService);
  items = signal<Array<{ id: string; subject_type: string; metrics: Record<string, number> }>>([]);

  constructor() {
    this.registry.listExperiments().subscribe({ next: (items) => this.items.set(items) });
  }
}
