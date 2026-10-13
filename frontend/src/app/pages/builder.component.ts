import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { JsonPipe } from '@angular/common';
import { RegistryService } from '../core/registry.service';

@Component({
  selector: 'app-builder',
  standalone: true,
  imports: [FormsModule, JsonPipe],
  template: `
    <section aria-labelledby="builder-title">
      <h1 id="builder-title">Workflow builder</h1>
      <p class="hint">Describe the objective in plain language; the platform drafts a manifest and test cases for review.</p>
      <form (ngSubmit)="draft()" class="row">
        <label class="visually-hidden" for="objective">Objective</label>
        <input id="objective" name="objective" [(ngModel)]="objective" placeholder="What should this workflow do?" required size="52" />
        <button type="submit" [disabled]="busy()">Draft</button>
      </form>
      @if (busy()) { <p>Drafting…</p> }
      @if (result(); as draft) {
        <h2>Draft manifest</h2>
        <pre>{{ draft.manifest | json }}</pre>
        <h2>Suggested test cases</h2>
        <pre>{{ draft.test_cases | json }}</pre>
      }
    </section>
  `,
})
export class BuilderComponent {
  private registry = inject(RegistryService);
  objective = signal('');
  busy = signal(false);
  result = signal<{ manifest: unknown; test_cases: unknown[] } | null>(null);

  draft(): void {
    this.busy.set(true);
    this.result.set(null);
    this.registry.draftWorkflow(this.objective().trim()).subscribe({
      next: (draft) => {
        this.busy.set(false);
        this.result.set(draft);
      },
      error: () => this.busy.set(false),
    });
  }
}
