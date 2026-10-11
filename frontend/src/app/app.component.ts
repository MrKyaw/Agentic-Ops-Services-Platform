import { Component, inject } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { AuthStore } from './core/auth-store';
import { STRINGS } from './core/messages';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink],
  template: `
    <header>
      <nav aria-label="Primary">
        <strong>{{ t.appName }}</strong>
        @if (auth.connected) {
          <a routerLink="/runs">{{ t.nav.runs }}</a>
          <a routerLink="/approvals">{{ t.nav.approvals }}</a>
          <a routerLink="/agents">{{ t.nav.agents }}</a>
          <a routerLink="/playground">{{ t.nav.playground }}</a>
          <a routerLink="/usage">{{ t.nav.usage }}</a>
          <a routerLink="/tenants">{{ t.nav.tenants }}</a>
          <span class="tenant">{{ auth.tenant() }}</span>
          <button (click)="auth.disconnect()">Disconnect</button>
        }
      </nav>
    </header>
    <router-outlet />
  `,
  styleUrl: './app.component.css',
})
export class AppComponent {
  protected t = STRINGS;
  protected auth = inject(AuthStore);
}
