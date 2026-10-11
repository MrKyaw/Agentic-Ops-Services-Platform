import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, Agent } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-agents',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section aria-labelledby="agents-title">
      <h1 id="agents-title">{{ t.nav.agents }}</h1>
      <form (ngSubmit)="create()" class="row">
        <label class="visually-hidden" for="new-id">ID</label>
        <input id="new-id" name="new-id" [(ngModel)]="newId" placeholder="agent id" required />
        <label class="visually-hidden" for="new-name">Name</label>
        <input id="new-name" name="new-name" [(ngModel)]="newName" placeholder="Display name" required />
        <label class="visually-hidden" for="new-pattern">Pattern</label>
        <select id="new-pattern" name="new-pattern" [(ngModel)]="newPattern">
          <option value="react">react</option>
          <option value="rewoo">rewoo</option>
        </select>
        <button type="submit">{{ t.common.submit }}</button>
      </form>
      @if (items().length === 0) { <p>{{ t.common.empty }}</p> }
      <ul>
        @for (agent of items(); track agent.id) {
          <li><strong>{{ agent.id }}</strong> — {{ agent.displayName }} — {{ agent.pattern }} v{{ agent.version }} ({{ agent.status }})</li>
        }
      </ul>
    </section>
  `,
})
export class AgentsComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  items = signal<Agent[]>([]);
  newId = signal('');
  newName = signal('');
  newPattern = signal('react');

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.api.listAgents().subscribe({ next: (items) => this.items.set(items) });
  }

  create(): void {
    this.api.createAgent({ id: this.newId().trim(), displayName: this.newName().trim(), pattern: this.newPattern() }).subscribe({
      next: () => {
        this.newId.set('');
        this.newName.set('');
        this.refresh();
      },
    });
  }
}
