import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthStore } from '../core/auth-store';
import { STRINGS } from '../core/messages';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  template: `
    <main class="card" aria-labelledby="login-title">
      <h1 id="login-title">{{ t.login.title }} — {{ t.appName }}</h1>
      <p class="hint">{{ t.login.hint }}</p>
      <form (ngSubmit)="connect()" #form="ngForm">
        <label for="token">{{ t.login.token }}</label>
        <input id="token" name="token" type="password" [(ngModel)]="token" required autocomplete="off" />
        <label for="tenant">{{ t.login.tenant }}</label>
        <input id="tenant" name="tenant" [(ngModel)]="tenant" required autocomplete="off" />
        <button type="submit" [disabled]="form.invalid">{{ t.login.submit }}</button>
      </form>
    </main>
  `,
})
export class LoginComponent {
  protected t = STRINGS;
  private auth = inject(AuthStore);
  private router = inject(Router);
  token = signal('');
  tenant = signal('');

  connect(): void {
    this.auth.connect(this.token().trim(), this.tenant().trim());
    void this.router.navigate(['/runs']);
  }
}
