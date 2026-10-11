import { Component, inject, signal } from '@angular/core';
import { ApiService, Approval } from '../core/api.service';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-approvals',
  standalone: true,
  template: `
    <section aria-labelledby="approvals-title">
      <h1 id="approvals-title">{{ t.nav.approvals }}</h1>
      @if (message()) { <p role="status">{{ message() }}</p> }
      @if (items().length === 0) { <p>{{ t.common.empty }}</p> }
      <ul>
        @for (item of items(); track item.id) {
          <li>
            <strong>{{ item.action }}</strong> on run {{ item.run_id }}
            <button (click)="decide(item.id, 'approved')" [disabled]="busy()">{{ t.common.approve }}</button>
            <button (click)="decide(item.id, 'rejected')" [disabled]="busy()">{{ t.common.reject }}</button>
          </li>
        }
      </ul>
    </section>
  `,
})
export class ApprovalsComponent {
  protected t = STRINGS;
  private api = inject(ApiService);
  items = signal<Approval[]>([]);
  busy = signal(false);
  message = signal('');

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.api.listApprovals().subscribe({ next: (items) => this.items.set(items) });
  }

  decide(id: string, decision: 'approved' | 'rejected'): void {
    this.busy.set(true);
    this.api.decideApproval(id, decision).subscribe({
      next: () => {
        this.message.set(`Approval ${id} ${decision}.`);
        this.busy.set(false);
        this.refresh();
      },
      error: () => {
        this.message.set('Decision failed.');
        this.busy.set(false);
      },
    });
  }
}
