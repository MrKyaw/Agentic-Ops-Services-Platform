import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-playground',
  standalone: true,
  imports: [FormsModule],
  template: `
    <section aria-labelledby="playground-title">
      <h1 id="playground-title">{{ t.nav.playground }}</h1>
      <form (ngSubmit)="ask()" class="row">
        <label class="visually-hidden" for="kb">Knowledge base</label>
        <input id="kb" name="kb" [(ngModel)]="kbId" placeholder="kb-policy" required />
        <label class="visually-hidden" for="q">Question</label>
        <input id="q" name="q" [(ngModel)]="query" placeholder="Ask a grounded question…" required size="48" />
        <button type="submit" [disabled]="busy()">{{ t.common.submit }}</button>
      </form>
      @if (busy()) { <p>{{ t.common.loading }}</p> }
      @if (answer() !== null) {
        <h2>Answer</h2>
        <p>{{ answer() }}</p>
        <h2>Sources</h2>
        <ul>
          @for (passage of passages(); track passage.content) {
            <li><small>{{ passage.document_id }}</small><br />{{ passage.content }}</li>
          }
        </ul>
      }
      @if (abstained()) { <p role="status">No supporting evidence — abstained.</p> }
    </section>
  `,
})
export class PlaygroundComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  kbId = signal('kb-policy');
  query = signal('');
  busy = signal(false);
  answer = signal<string | null>(null);
  abstained = signal(false);
  passages = signal<Array<{ content: string; document_id: string }>>([]);

  ask(): void {
    this.busy.set(true);
    this.answer.set(null);
    this.abstained.set(false);
    this.api.queryKb(this.kbId().trim(), this.query().trim()).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.answer.set(result.answer);
        this.abstained.set(result.abstained);
        this.passages.set(result.passages);
      },
      error: () => this.busy.set(false),
    });
  }
}
