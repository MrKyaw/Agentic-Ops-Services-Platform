import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RegistryService } from '../core/registry.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-prompts',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section aria-labelledby="prompts-title">
      <h1 id="prompts-title">Prompts</h1>
      @if (message()) { <p role="status">{{ message() }}</p> }
      <form (ngSubmit)="create()" class="row">
        <label class="visually-hidden" for="prompt-id">ID</label>
        <input id="prompt-id" name="prompt-id" [(ngModel)]="newId" placeholder="prompt id" required />
        <label class="visually-hidden" for="prompt-template">Template</label>
        <input id="prompt-template" name="prompt-template" [(ngModel)]="newTemplate" placeholder="Template with {var}" required size="40" />
        <button type="submit">{{ t.common.submit }}</button>
      </form>
      <ul>
        @for (prompt of items(); track prompt.id) {
          <li><strong>{{ prompt.id }}</strong> v{{ prompt.version }} ({{ prompt.status }})
            @if (prompt.status === 'draft') {
              <button (click)="approve(prompt.id, prompt.version)">Approve</button>
            }
          </li>
        }
      </ul>
    </section>
  `,
})
export class PromptsComponent {
  protected t = STRINGS;
  private registry = inject(RegistryService);
  items = signal<Array<{ id: string; version: number; status: string }>>([]);
  message = signal('');
  newId = signal('');
  newTemplate = signal('');

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.registry.listPrompts().subscribe({ next: (items) => this.items.set(items) });
  }

  create(): void {
    this.registry.createPrompt(this.newId().trim(), this.newTemplate()).subscribe({
      next: (created) => {
        this.message.set(`Created ${created.id}@${created.version} as draft.`);
        this.newId.set('');
        this.newTemplate.set('');
        this.refresh();
      },
      error: () => this.message.set('Create failed.'),
    });
  }

  approve(id: string, version: number): void {
    this.registry.approvePrompt(id, version).subscribe({
      next: () => {
        this.message.set(`Approved ${id}@${version}.`);
        this.refresh();
      },
      error: () => this.message.set('Approve failed (admin role required).'),
    });
  }
}
